"""Contratos de referência anteriores à adoção do contêiner .fornax."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtWidgets import QApplication

from core.dynamic_images import dynamic_image_fields
from core.model_document import (
    adapt_model_page,
    document_signatures,
    iter_page_asset_paths,
    iter_page_link_items,
    load_model_document,
    normalize_model_document,
    page_ids,
    persistent_model_document,
    save_model_document,
)
from features.generator.renderer import renderers_for_document


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "fornax_stage1"
FIXTURE = FIXTURE_DIR / "template_v4.json"


def _png_digest(image) -> str:
    encoded = QByteArray()
    buffer = QBuffer(encoded)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    return hashlib.sha256(bytes(encoded)).hexdigest()


def test_stage1_fixture_preserves_multipage_relations_and_fields():
    document = load_model_document(FIXTURE)

    assert page_ids(document) == ("front", "back")
    assert document["placeholders"] == ["Nome", "Cargo", "Site", "Foto", "Observacao"]
    assert dynamic_image_fields(document) == ["Foto"]

    front = document["pages"][0]
    masked = next(item for item in front["images"] if item["object_id"] == "image:masked")
    mask = next(item for item in front["shapes"] if item["object_id"] == "shape:mask")
    assert masked["mask_shape_id"] == mask["object_id"]
    assert masked["mask_order"] == 0
    assert mask["mask_group_id"] == 1
    assert {mask["group_id"], front["boxes"][0]["group_id"]} == {1}

    signatures = document_signatures(document)
    assert [(item["signature_id"], item["visible"]) for item in signatures] == [
        ("sig-stage1-visible", True),
        ("sig-stage1-hidden", False),
    ]

    links = list(iter_page_link_items(document))
    assert [(page, collection, item["link_key"]) for page, collection, item in links] == [
        ("front", "boxes", "Site")
    ]


def test_stage1_fixture_inventory_includes_hidden_signature_and_missing_asset():
    document = load_model_document(FIXTURE)
    assets = list(iter_page_asset_paths(document))

    assert ("front", "signatures", "assets/reference-signature-visible.svg") in assets
    assert ("front", "signatures", "assets/reference-signature-hidden.svg") in assets
    assert ("front", "images", "assets/intentionally-missing.png") in assets
    assert not (FIXTURE_DIR / "assets" / "intentionally-missing.png").exists()


def test_stage1_fixture_round_trip_keeps_persistent_document(tmp_path):
    source = load_model_document(FIXTURE)
    expected = persistent_model_document(source)

    target = save_model_document(source, tmp_path / "model")
    restored = load_model_document(target)

    # O primeiro salvamento acrescenta somente o snapshot de origem esperado.
    assert persistent_model_document(restored)["pages"] == expected["pages"]
    assert restored["canvas_size"] == source["canvas_size"]
    assert restored["placeholders"] == source["placeholders"]


def test_stage1_renderer_is_deterministic_for_both_pages_and_missing_asset():
    app = QApplication.instance() or QApplication([])
    document = load_model_document(FIXTURE)
    row = {
        "Nome": "Ada Lovelace",
        "Cargo": "Referência",
        "Site": "https://example.invalid/ada",
        "Foto": "missing-dynamic-photo",
        "Observacao": "Contrato visual do verso",
        "__use_signature__:sig-stage1-visible": True,
        "__use_signature__:sig-stage1-hidden": False,
    }
    renderers = renderers_for_document(document)

    first = [renderer.render_to_qimage(row, row) for renderer in renderers]
    second = [renderer.render_to_qimage(row, row) for renderer in renderers]

    assert [(image.width(), image.height()) for image in first] == [(400, 240), (400, 240)]
    assert [_png_digest(image) for image in first] == [_png_digest(image) for image in second]
    assert _png_digest(first[0]) != _png_digest(first[1])
    app.processEvents()


def test_stage1_page_adapters_do_not_share_mutations():
    document = normalize_model_document(load_model_document(FIXTURE))
    front = adapt_model_page(document, "front")
    back = adapt_model_page(document, "back")

    front["boxes"][0]["html"] = "alterado"
    assert document["pages"][0]["boxes"][0]["html"] != "alterado"
    assert back["boxes"][0]["html"] != "alterado"
