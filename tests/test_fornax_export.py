"""Contratos das cópias de compartilhamento individuais e em lote."""

from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from core.fornax_container import (
    FULL_MODE,
    PUBLIC_MODE,
    SIGNATURES_MODE,
    FornaxError,
    inspect_fornax,
    open_public_fornax,
    save_protected_fornax,
    save_public_fornax,
    unlock_fornax,
)
from core.fornax_export import ExportRequest, export_models
from core.model_document import document_signatures
from tests.test_fornax_crypto import FIXTURE_DIR, PASSWORD, protected_document


TRANSPORT_PASSWORD = "Senha exclusiva do envio 2026"


def signature_free_document():
    document = protected_document()
    for page in document["pages"]:
        signature_ids = {item["object_id"] for item in page["signatures"]}
        page["signatures"] = []
        page["layer_order"] = [
            item for item in page["layer_order"] if item not in signature_ids
        ]
    return document


def test_public_single_export_creates_independent_copy(tmp_path):
    source = tmp_path / "source.fornax"
    original = save_public_fornax(
        signature_free_document(), source, source_dir=FIXTURE_DIR,
    )
    before = source.read_bytes()
    destination = tmp_path / "shared.fornax"

    result = export_models(
        [ExportRequest(source, "Modelo público")], destination,
        include_signatures=False,
    )

    assert len(result) == 1
    assert inspect_fornax(destination).mode == PUBLIC_MODE
    assert inspect_fornax(destination).model_id != original.model_id
    assert open_public_fornax(destination).document()["pages"]
    assert source.read_bytes() == before


def test_partial_export_reencrypts_signatures_with_transport_password(tmp_path):
    source = tmp_path / "partial.fornax"
    original = save_protected_fornax(
        protected_document(), source, PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    before = source.read_bytes()
    destination = tmp_path / "shared.fornax"

    export_models(
        [ExportRequest(source, "Protegido", local_password=PASSWORD)],
        destination, include_signatures=True,
        transport_password=TRANSPORT_PASSWORD,
    )

    shared = inspect_fornax(destination)
    assert shared.mode == SIGNATURES_MODE
    assert shared.model_id != original.model_id
    assert shared.salt != original.salt
    with pytest.raises(FornaxError):
        unlock_fornax(destination, PASSWORD)
    assert len(document_signatures(
        unlock_fornax(destination, TRANSPORT_PASSWORD).document()
    )) == 2
    assert source.read_bytes() == before


def test_partial_export_without_signatures_needs_no_local_password(tmp_path):
    source = tmp_path / "partial.fornax"
    save_protected_fornax(
        protected_document(), source, PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    before = source.read_bytes()
    destination = tmp_path / "without-signatures.fornax"

    export_models(
        [ExportRequest(source, "Sem assinaturas")], destination,
        include_signatures=False,
    )

    assert inspect_fornax(destination).mode == PUBLIC_MODE
    assert document_signatures(open_public_fornax(destination).document()) == []
    with zipfile.ZipFile(destination) as archive:
        assert "protected.bin" not in archive.namelist()
        contents = b"".join(archive.read(name) for name in archive.namelist())
        assert b"reference-signature" not in contents
    assert source.read_bytes() == before


def test_full_export_without_signatures_requires_unlock(tmp_path):
    source = tmp_path / "full.fornax"
    save_protected_fornax(
        protected_document(), source, PASSWORD,
        mode=FULL_MODE, source_dir=FIXTURE_DIR,
    )
    before = source.read_bytes()
    destination = tmp_path / "public-copy.fornax"

    with pytest.raises(FornaxError):
        export_models(
            [ExportRequest(source, "Integral")], destination,
            include_signatures=False,
        )
    assert not destination.exists()

    export_models(
        [ExportRequest(source, "Integral", local_password=PASSWORD)],
        destination, include_signatures=False,
    )
    assert inspect_fornax(destination).mode == PUBLIC_MODE
    assert document_signatures(open_public_fornax(destination).document()) == []
    assert source.read_bytes() == before


def test_batch_supports_three_modes_and_per_model_signature_choice(tmp_path):
    public = tmp_path / "public.fornax"
    partial = tmp_path / "partial.fornax"
    full = tmp_path / "full.fornax"
    save_public_fornax(signature_free_document(), public, source_dir=FIXTURE_DIR)
    save_protected_fornax(
        protected_document(), partial, PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    save_protected_fornax(
        protected_document(), full, PASSWORD,
        mode=FULL_MODE, source_dir=FIXTURE_DIR,
    )
    originals = {path: path.read_bytes() for path in (public, partial, full)}
    destination = tmp_path / "models.zip"

    exported = export_models(
        [
            ExportRequest(public, "Público"),
            ExportRequest(partial, "Parcial", include_signatures=False),
            ExportRequest(full, "Integral", local_password=PASSWORD),
        ],
        destination, include_signatures=True,
        transport_password=TRANSPORT_PASSWORD,
    )

    assert len(exported) == 3
    with zipfile.ZipFile(destination) as archive:
        assert len(archive.namelist()) == 3
        assert all(name.endswith(".fornax") for name in archive.namelist())
        archive.extractall(tmp_path / "clean-environment")
    extracted = sorted((tmp_path / "clean-environment").glob("*.fornax"))
    modes = {inspect_fornax(path).mode for path in extracted}
    assert modes == {PUBLIC_MODE, FULL_MODE}
    full_copy = next(path for path in extracted if inspect_fornax(path).mode == FULL_MODE)
    assert len(document_signatures(
        unlock_fornax(full_copy, TRANSPORT_PASSWORD).document()
    )) == 2
    for path in extracted:
        if inspect_fornax(path).mode == PUBLIC_MODE:
            assert document_signatures(open_public_fornax(path).document()) == []
    assert all(path.read_bytes() == contents for path, contents in originals.items())


def test_failed_export_does_not_publish_output_or_change_source(tmp_path):
    source = tmp_path / "partial.fornax"
    save_protected_fornax(
        protected_document(), source, PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    before = source.read_bytes()
    destination = tmp_path / "failed.fornax"

    with pytest.raises(FornaxError):
        export_models(
            [ExportRequest(source, "Protegido", local_password="Senha errada válida")],
            destination, include_signatures=True,
            transport_password=TRANSPORT_PASSWORD,
        )

    assert not destination.exists()
    assert source.read_bytes() == before
