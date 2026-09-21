from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from core.fornax_container import (
    PUBLIC_MODE, SIGNATURES_MODE, FornaxAssetError,
    inspect_fornax, open_public_fornax, unlock_fornax,
)
from core.legacy_migration import (
    LegacyMigrationError, migrate_legacy_model, resume_legacy_migrations,
)
from core.model_document import load_model_document, normalize_model_document, save_model_document
from core.model_library import scan_model_library
from features.generator.renderer import renderers_for_document


PASSWORD = "senha-segura"
APP = QApplication.instance() or QApplication([])


def _legacy_document(name="Legado", *, image_path=None, signature_path=None):
    document = normalize_model_document({
        "name": name,
        "canvas_size": {"w": 120, "h": 80},
        "target_w_mm": 60.0,
        "target_h_mm": 40.0,
        "placeholders": ["nome"],
        "background_path": None,
        "boxes": [{
            "id": "nome", "html": "Olá {nome}",
            "x": 10, "y": 20, "w": 100, "h": 30,
            "font_family": "Inter", "font_size": 14,
            "align": "center", "visible": True,
        }],
    })
    page = document["pages"][0]
    if image_path:
        page["images"].append({
            "object_id": "image:test", "path": image_path,
            "x": 0, "y": 0, "width": 120, "height": 80,
            "rotation": 0, "opacity": 1.0, "visible": True,
        })
    if signature_path:
        page["signatures"].append({
            "object_id": "signature:test", "signature_id": "sig-test",
            "custom_name": "Diretor", "path": signature_path,
            "x": 20, "y": 45, "width": 40, "height": 20,
            "rotation": 0, "opacity": 1.0, "visible": False,
        })
    page["layer_order"] = [
        item["object_id"]
        for collection in ("images", "signatures", "boxes")
        for item in page[collection]
    ]
    return document


def _image(path: Path, color="#2878e8"):
    image = QImage(24, 16, QImage.Format.Format_ARGB32)
    image.fill(QColor(color))
    assert image.save(str(path), "PNG")


def test_public_legacy_conversion_preserves_rendering_and_removes_source(tmp_path):
    models = tmp_path / "models"
    source = models / "cartao"
    source.mkdir(parents=True)
    _image(source / "photo.png")
    original = _legacy_document(image_path="photo.png")
    save_model_document(original, source)
    before = renderers_for_document(load_model_document(source))[0].render_to_qimage(
        {"nome": "Ana"}, {"nome": "Ana"},
    )

    result = migrate_legacy_model(source, models, mode=PUBLIC_MODE)

    assert result.cleanup_complete is True
    assert not source.exists()
    assert result.destination.is_file()
    assert not (tmp_path / "migrations").exists()
    opened = open_public_fornax(result.destination)
    assert len(opened.document()["pages"]) == 1
    after = renderers_for_document(
        opened.document(), asset_provider=opened.asset,
    )[0].render_to_qimage({"nome": "Ana"}, {"nome": "Ana"})
    assert after == before


def test_signed_legacy_requires_protection_and_keeps_hidden_signature(tmp_path):
    models = tmp_path / "models"
    source = models / "diploma"
    source.mkdir(parents=True)
    _image(source / "signature.png", "#151515")
    save_model_document(
        _legacy_document(signature_path="signature.png"), source,
    )

    with pytest.raises(LegacyMigrationError, match="exigem proteção"):
        migrate_legacy_model(source, models, mode=PUBLIC_MODE)
    assert source.is_dir()

    result = migrate_legacy_model(
        source, models, mode=SIGNATURES_MODE, password=PASSWORD,
    )

    descriptor = inspect_fornax(result.destination)
    assert descriptor.mode == SIGNATURES_MODE
    assert open_public_fornax(descriptor).document()["pages"][0]["signatures"] == []
    restored = unlock_fornax(descriptor, PASSWORD).document()
    signatures = restored["pages"][0]["signatures"]
    assert len(signatures) == 1
    assert signatures[0]["visible"] is False
    assert not source.exists()


def test_missing_asset_never_publishes_or_removes_legacy_source(tmp_path):
    models = tmp_path / "models"
    source = models / "incompleto"
    source.mkdir(parents=True)
    save_model_document(
        _legacy_document(image_path="missing.png"), source,
    )

    with pytest.raises(FornaxAssetError):
        migrate_legacy_model(source, models, mode=PUBLIC_MODE)

    assert source.is_dir()
    assert not list(models.glob("*.fornax"))
    assert not list((tmp_path / "migrations").glob("*.json"))


def test_missing_hidden_signature_also_blocks_protected_conversion(tmp_path):
    models = tmp_path / "models"
    source = models / "assinatura-incompleta"
    source.mkdir(parents=True)
    save_model_document(
        _legacy_document(signature_path="missing-signature.png"), source,
    )

    with pytest.raises(FornaxAssetError):
        migrate_legacy_model(
            source, models, mode=SIGNATURES_MODE, password=PASSWORD,
        )

    assert source.is_dir()
    assert not list(models.glob("*.fornax"))


def test_published_migration_resumes_cleanup_after_interruption(tmp_path):
    models = tmp_path / "models"
    source = models / "retomavel"
    source.mkdir(parents=True)
    save_model_document(_legacy_document(), source)

    with patch(
        "core.legacy_migration._cleanup_source",
        side_effect=KeyboardInterrupt("interrupção simulada"),
    ):
        with pytest.raises(KeyboardInterrupt):
            migrate_legacy_model(source, models, mode=PUBLIC_MODE)

    destination = models / "retomavel.fornax"
    assert destination.is_file()
    assert source.is_dir()
    assert list((tmp_path / "migrations").glob("*.json"))

    assert resume_legacy_migrations(models) == (source.resolve(),)
    assert not source.exists()
    assert not list((tmp_path / "migrations").glob("*.json"))
    assert inspect_fornax(destination)


def test_verified_package_is_published_on_resume_without_reconversion(tmp_path):
    models = tmp_path / "models"
    source = models / "verificado"
    source.mkdir(parents=True)
    save_model_document(_legacy_document(), source)
    from core.file_transactions import publish_new as real_replace
    interrupted = {"done": False}

    def interrupt_publication(old, new):
        if Path(new).name == "verificado.fornax" and not interrupted["done"]:
            interrupted["done"] = True
            raise OSError("interrupção antes da publicação")
        return real_replace(old, new)

    with patch("core.legacy_migration.publish_new", side_effect=interrupt_publication):
        with pytest.raises(OSError, match="antes da publicação"):
            migrate_legacy_model(source, models, mode=PUBLIC_MODE)

    assert source.is_dir()
    assert not (models / "verificado.fornax").exists()
    journal = next((tmp_path / "migrations").glob("*.json"))
    assert '"state": "VERIFIED"' in journal.read_text(encoding="utf-8")

    assert resume_legacy_migrations(models) == (source.resolve(),)
    assert (models / "verificado.fornax").is_file()
    assert not source.exists()


def test_changed_or_added_legacy_files_are_not_deleted_after_publication(tmp_path):
    models = tmp_path / "models"
    source = models / "concorrente"
    source.mkdir(parents=True)
    save_model_document(_legacy_document(), source)

    from core import legacy_migration
    original_cleanup = legacy_migration._cleanup_source

    def add_file_then_cleanup(folder, inventory):
        (folder / "adicionado-depois.txt").write_text("preservar", encoding="utf-8")
        return original_cleanup(folder, inventory)

    with patch("core.legacy_migration._cleanup_source", side_effect=add_file_then_cleanup):
        result = migrate_legacy_model(source, models, mode=PUBLIC_MODE)

    assert result.cleanup_complete is False
    assert (source / "adicionado-depois.txt").read_text(encoding="utf-8") == "preservar"
    found = scan_model_library(models)
    assert [model.kind for model in found] == ["fornax"]
    assert source.is_dir()


def test_symlink_in_legacy_model_is_rejected_without_touching_source(tmp_path):
    models = tmp_path / "models"
    source = models / "symlink"
    source.mkdir(parents=True)
    save_model_document(_legacy_document(), source)
    outside = tmp_path / "outside.txt"
    outside.write_text("externo", encoding="utf-8")
    try:
        (source / "unsafe").symlink_to(outside)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows account lacks the symbolic-link privilege")
        raise

    with pytest.raises(LegacyMigrationError, match="link simbólico"):
        migrate_legacy_model(source, models, mode=PUBLIC_MODE)

    assert outside.read_text(encoding="utf-8") == "externo"
    assert source.is_dir()


@pytest.mark.parametrize('mode', [PUBLIC_MODE, SIGNATURES_MODE, 'full'])
@pytest.mark.parametrize('order', [None, ['text:2', 'removed-layer']])
def test_raw_v3_migrates_without_complete_layer_order_and_preserves_pixels(tmp_path, mode, order):
    import json
    from core.model_document import persistent_model_document
    models = tmp_path / 'models'
    source = models / 'legacy-v3'
    source.mkdir(parents=True)
    _image(source / 'background.png', '#123456')
    _image(source / 'photo.png', '#aa3311')
    _image(source / 'signature.png', '#eeeeee')
    raw = {
        'canvas_size': {'w': 120, 'h': 80},
        'target_w_mm': 60, 'target_h_mm': 40,
        'name': 'Legado real', 'placeholders': ['nome'],
        'background_path': 'background.png',
        'bg_props': {'x': 0, 'y': 0, 'w': 120, 'h': 80, 'opacity': 1},
        'images': [{'layer_id': 1, 'path': 'photo.png', 'x': 10, 'y': 10,
                    'width': 40, 'height': 30}],
        'boxes': [{'layer_id': 2, 'id': 'nome', 'html': 'Olá {nome}',
                   'x': 10, 'y': 15, 'w': 100, 'h': 30,
                   'font_family': 'Inter', 'font_size': 14}],
        'signatures': [] if mode == PUBLIC_MODE else [
            {'layer_id': 3, 'path': 'signature.png', 'x': 15, 'y': 20,
             'width': 40, 'height': 15, 'visible': True}],
    }
    if order is not None:
        raw['layer_order'] = order
    path = source / 'template_v3.json'
    encoded = json.dumps(raw).encode()
    path.write_bytes(encoded)
    document = load_model_document(source)
    before = renderers_for_document(document)[0].render_to_qimage({'nome': 'Ana'}, {'nome': 'Ana'})
    # Converter em memória não escreve na origem nem altera seu estado tolerante.
    persistent = persistent_model_document(document)
    assert path.read_bytes() == encoded
    assert document.get('__source_schema_version') == 3
    page = persistent['pages'][0]
    assert set(page['layer_order']) == {
        item['object_id'] for collection in ('images', 'boxes', 'shapes', 'signatures')
        for item in page[collection]
    }
    result = migrate_legacy_model(source, models, mode=mode,
                                  password=None if mode == PUBLIC_MODE else PASSWORD)
    opened = (open_public_fornax(result.destination) if mode == PUBLIC_MODE
              else unlock_fornax(result.destination, PASSWORD))
    after = renderers_for_document(opened.document(), asset_provider=opened.asset)[0].render_to_qimage(
        {'nome': 'Ana'}, {'nome': 'Ana'})
    assert before == after
    assert result.cleanup_complete


def test_current_document_with_missing_layer_order_is_still_rejected():
    from core.model_document import ModelValidationError, persistent_model_document
    document = _legacy_document()
    document.pop('__source_schema_version', None)
    document['pages'][0].pop('layer_order')
    with pytest.raises(ModelValidationError, match='layer_order inválido'):
        persistent_model_document(document)
