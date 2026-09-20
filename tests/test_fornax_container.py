"""Contratos do contêiner público .fornax v1 (checkpoint 3.1)."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import stat
import warnings
import zipfile

import pytest

import core.fornax_container as container
from core.fornax_container import (
    FornaxAssetError,
    FornaxFormatError,
    FornaxLimitError,
    UnsupportedFornaxFeature,
    inspect_fornax,
    open_public_fornax,
    save_public_fornax,
)
from core.model_document import load_model_document, persistent_model_document


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "fornax_stage1"
MODEL_ID = "11111111-1111-4111-8111-111111111111"
REVISION_ID = "22222222-2222-4222-8222-222222222222"


def public_document():
    document = load_model_document(FIXTURE_DIR / "template_v4.json")
    for page in document["pages"]:
        signature_ids = {item["object_id"] for item in page["signatures"]}
        page["signatures"] = []
        page["layer_order"] = [
            item for item in page["layer_order"] if item not in signature_ids
        ]
        page["images"] = [
            item for item in page["images"]
            if item.get("path") != "assets/intentionally-missing.png"
        ]
        present_ids = {
            item["object_id"]
            for collection in ("boxes", "images", "shapes")
            for item in page[collection]
        }
        page["layer_order"] = [item for item in page["layer_order"] if item in present_ids]
    return persistent_model_document(document)


def manifest(*, mode="none", version=1):
    return {"header": {
        "format": "fornax",
        "version": version,
        "mode": mode,
        "model_id": MODEL_ID,
        "revision_id": REVISION_ID,
    }}


def write_zip(path, entries):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, contents in entries:
            archive.writestr(name, contents)


def test_public_round_trip_preserves_document_and_asset_bytes(tmp_path):
    source = public_document()
    descriptor = save_public_fornax(
        source, tmp_path / "modelo.fornax", source_dir=FIXTURE_DIR,
        model_id=MODEL_ID,
    )

    inspected = inspect_fornax(descriptor.path)
    opened = open_public_fornax(inspected)
    restored = opened.document()

    assert inspected.model_id == MODEL_ID
    assert inspected.revision_id != REVISION_ID
    assert opened.asset_references
    assert all(reference.startswith("public/assets/") for reference in opened.asset_references)
    assert restored["pages"][0]["boxes"] == source["pages"][0]["boxes"]
    assert restored["pages"][1]["boxes"] == source["pages"][1]["boxes"]
    assert restored["canvas_size"] == source["canvas_size"]
    assert restored["pages"][0]["images"][0]["path"] in opened.asset_references
    assert opened.asset(restored["pages"][0]["images"][0]["path"]).startswith(b"<svg")

    detached = opened.document()
    detached["pages"][0]["boxes"].clear()
    assert opened.document()["pages"][0]["boxes"]


def test_writer_rejects_signature_and_missing_asset(tmp_path):
    signed = load_model_document(FIXTURE_DIR / "template_v4.json")
    with pytest.raises(FornaxFormatError, match="assinatura"):
        save_public_fornax(signed, tmp_path / "signed.fornax", source_dir=FIXTURE_DIR)

    source = public_document()
    source["pages"][0]["images"][0]["path"] = "assets/missing.svg"
    with pytest.raises(FornaxAssetError, match="não encontrado"):
        save_public_fornax(source, tmp_path / "missing.fornax", source_dir=FIXTURE_DIR)


def test_failed_verification_keeps_existing_destination_and_removes_pending(tmp_path, monkeypatch):
    destination = tmp_path / "model.fornax"
    destination.write_bytes(b"previous-valid-version")
    source = public_document()

    def fail_verification(_path):
        raise FornaxFormatError("falha injetada")

    monkeypatch.setattr(container, "open_public_fornax", fail_verification)
    with pytest.raises(FornaxFormatError, match="injetada"):
        save_public_fornax(source, destination, source_dir=FIXTURE_DIR)

    assert destination.read_bytes() == b"previous-valid-version"
    assert not list(tmp_path.glob(".*.pending-*.fornax"))


@pytest.mark.parametrize("bad_name", ["../escape", "/absolute", "public\\asset.svg"])
def test_reader_rejects_unsafe_paths(tmp_path, bad_name):
    package = tmp_path / "unsafe.fornax"
    write_zip(package, [
        ("manifest.json", json.dumps(manifest())),
        ("public/document.json", json.dumps(public_document())),
        (bad_name, b"unsafe"),
    ])
    with pytest.raises(FornaxFormatError):
        inspect_fornax(package)


def test_reader_rejects_duplicate_and_case_ambiguous_entries(tmp_path):
    for names in (
        ("manifest.json", "manifest.json"),
        ("manifest.json", "MANIFEST.JSON"),
    ):
        package = tmp_path / f"duplicate-{len(names[1])}-{names[1][0]}.fornax"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            write_zip(package, [
                (names[0], json.dumps(manifest())),
                (names[1], json.dumps(manifest())),
                ("public/document.json", json.dumps(public_document())),
            ])
        with pytest.raises(FornaxFormatError, match="duplicada ou ambígua"):
            inspect_fornax(package)


def test_reader_rejects_symlink_entry(tmp_path):
    package = tmp_path / "symlink.fornax"
    link = zipfile.ZipInfo("public/assets/11111111-1111-4111-8111-111111111111.svg")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest()))
        archive.writestr("public/document.json", json.dumps(public_document()))
        archive.writestr(link, "target")
    with pytest.raises(FornaxFormatError, match="simbólico"):
        inspect_fornax(package)


def test_reader_rejects_oversized_manifest_before_json_parse(tmp_path):
    package = tmp_path / "large.fornax"
    write_zip(package, [
        ("manifest.json", b"{" + b" " * container.MAX_MANIFEST_BYTES + b"}"),
        ("public/document.json", b"{}"),
    ])
    with pytest.raises(FornaxLimitError, match="limite"):
        inspect_fornax(package)


def test_reader_rejects_duplicate_json_keys_and_unknown_mode_or_version(tmp_path):
    duplicate = tmp_path / "duplicate-json.fornax"
    raw = (
        '{"header":{"format":"fornax","version":1,"mode":"none",'
        f'"model_id":"{MODEL_ID}","revision_id":"{REVISION_ID}",'
        '"mode":"none"}}'
    )
    write_zip(duplicate, [
        ("manifest.json", raw),
        ("public/document.json", json.dumps(public_document())),
    ])
    with pytest.raises(FornaxFormatError, match="repetida"):
        inspect_fornax(duplicate)

    for filename, changed in (
        ("mode.fornax", manifest(mode="future")),
        ("version.fornax", manifest(version=2)),
    ):
        package = tmp_path / filename
        write_zip(package, [
            ("manifest.json", json.dumps(changed)),
            ("public/document.json", json.dumps(public_document())),
        ])
        with pytest.raises(UnsupportedFornaxFeature):
            inspect_fornax(package)


def test_reader_rejects_missing_and_orphan_assets(tmp_path):
    source = public_document()
    source["pages"][0]["images"][0]["path"] = (
        "public/assets/11111111-1111-4111-8111-111111111111.svg"
    )
    missing = tmp_path / "missing.fornax"
    write_zip(missing, [
        ("manifest.json", json.dumps(manifest())),
        ("public/document.json", json.dumps(source)),
    ])
    with pytest.raises(FornaxAssetError, match="ausente"):
        open_public_fornax(missing)

    clean = public_document()
    for page in clean["pages"]:
        image_ids = {item["object_id"] for item in page["images"]}
        page["images"] = []
        page["background_path"] = None
        page["layer_order"] = [
            object_id for object_id in page["layer_order"] if object_id not in image_ids
        ]
    orphan = tmp_path / "orphan.fornax"
    write_zip(orphan, [
        ("manifest.json", json.dumps(manifest())),
        ("public/document.json", json.dumps(clean)),
        ("public/assets/11111111-1111-4111-8111-111111111111.svg", b"<svg/>")
    ])
    with pytest.raises(FornaxFormatError, match="não referenciado"):
        open_public_fornax(orphan)


def test_writer_rejects_svg_with_external_reference(tmp_path):
    unsafe = tmp_path / "unsafe.svg"
    unsafe.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<image href="file:///etc/passwd"/></svg>',
        encoding="utf-8",
    )
    source = public_document()
    source["pages"][0]["images"][0]["path"] = str(unsafe)

    with pytest.raises(FornaxFormatError, match="referência externa"):
        save_public_fornax(source, tmp_path / "unsafe.fornax", source_dir=FIXTURE_DIR)


def test_reader_rejects_more_than_entry_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(container, "MAX_ENTRIES", 2)
    package = tmp_path / "entries.fornax"
    write_zip(package, [
        ("manifest.json", json.dumps(manifest())),
        ("public/document.json", json.dumps(public_document())),
        ("public/assets/11111111-1111-4111-8111-111111111111.svg", b"<svg/>"),
    ])
    with pytest.raises(FornaxLimitError, match="entradas demais"):
        inspect_fornax(package)
