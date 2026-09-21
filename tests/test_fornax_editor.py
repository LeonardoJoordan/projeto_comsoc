import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from core.fornax_container import (
    PUBLIC_MODE, SIGNATURES_MODE, inspect_fornax, open_public_fornax,
    save_protected_fornax, save_public_fornax,
)
from core.fornax_session import FornaxSessionManager
from core.model_document import normalize_model_document
from features.editor.canvas_items import BackgroundItem, ImageItem, RectangleItem
from features.editor.editor_window import EditorWindow


APP = QApplication.instance() or QApplication([])


def _image_document(path):
    document = normalize_model_document({
        "name": "Editor em memória",
        "canvas_size": {"w": 160, "h": 100},
        "target_w_mm": 80.0, "target_h_mm": 50.0,
        "placeholders": [], "boxes": [], "signatures": [], "shapes": [],
        "images": [{
            "object_id": "image:memory", "path": str(path),
            "x": 10, "y": 10, "width": 80, "height": 50,
            "rotation": 0, "opacity": 1.0, "visible": True,
        }],
    })
    document["pages"][0]["layer_order"] = ["image:memory"]
    return document


def _signature_document(path, *, acknowledged=True):
    document = normalize_model_document({
        "name": "Assinatura pública",
        "canvas_size": {"w": 160, "h": 100},
        "target_w_mm": 80.0, "target_h_mm": 50.0,
        "placeholders": [], "boxes": [], "images": [], "shapes": [],
        "signatures": [{
            "object_id": "signature:public", "signature_id": "sig-public",
            "custom_name": "Diretor", "path": str(path),
            "x": 10, "y": 10, "width": 50, "height": 25,
            "rotation": 0, "opacity": 1.0, "visible": True,
        }],
    })
    document["pages"][0]["layer_order"] = ["signature:public"]
    if acknowledged:
        document["protection_preferences"] = {
            "public_signatures_acknowledged": True,
        }
    return document


def test_editor_loads_and_resaves_public_fornax_without_extracting_assets(tmp_path):
    source = tmp_path / "source.png"
    image = QImage(32, 20, QImage.Format.Format_ARGB32)
    image.fill(QColor("#2f80ed"))
    assert image.save(str(source), "PNG")
    package = tmp_path / "models" / "editor-memoria.fornax"
    package.parent.mkdir()
    save_public_fornax(_image_document(source), package)
    manager = FornaxSessionManager()
    initial = manager.select(package)
    window = EditorWindow()
    window.load_from_fornax(
        manager.document(package), path=package, mode=PUBLIC_MODE,
        model_id=initial.descriptor.model_id,
        asset_provider=lambda reference: manager.asset(reference, package),
        session_manager=manager,
    )
    try:
        items = [
            item for item in window.scene.items()
            if isinstance(item, ImageItem)
            and not isinstance(item, (RectangleItem, BackgroundItem))
        ]
        assert len(items) == 1
        assert not items[0].pixmap().isNull()
        assert items[0]._original_path.startswith("public/assets/")
        old_revision = initial.descriptor.revision_id
        items[0].setPos(22, 14)
        window._write_fornax_recovery()
        recovery_path = window.fornax_recovery_path(package)
        assert recovery_path.is_file()
        recovered = manager.read_recovery(recovery_path, path=package).document()
        assert recovered["pages"][0]["images"][0]["x"] == 22

        with patch.object(window, "_show_save_success_dialog"):
            window._export_to_fornax(window.get_current_scene_state())

        assert manager.status(package).descriptor.revision_id != old_revision
        assert package.with_name(package.name + ".bak").is_file()
        assert not recovery_path.exists()
        assert not list(package.parent.glob("**/assets"))
    finally:
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()
        manager.close()
        APP.processEvents()


def test_signature_free_editor_copy_requires_new_name_and_preserves_original(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    signature_path = tmp_path / "signature.png"
    image = QImage(24, 12, QImage.Format.Format_ARGB32)
    image.fill(QColor("#151515"))
    assert image.save(str(signature_path), "PNG")
    document = normalize_model_document({
        "name": "Original protegido",
        "canvas_size": {"w": 160, "h": 100},
        "target_w_mm": 80.0, "target_h_mm": 50.0,
        "placeholders": [], "boxes": [], "images": [], "shapes": [],
        "signatures": [{
            "object_id": "signature:test", "signature_id": "sig-test",
            "custom_name": "Diretor", "path": str(signature_path),
            "x": 10, "y": 10, "width": 50, "height": 25,
            "rotation": 0, "opacity": 1.0, "visible": True,
        }],
    })
    document["pages"][0]["layer_order"] = ["signature:test"]
    original = models / "original.fornax"
    password = "senha-segura"
    save_protected_fornax(document, original, password, mode=SIGNATURES_MODE)
    original_bytes = original.read_bytes()
    manager = FornaxSessionManager()
    status = manager.open_without_signatures(original)
    window = EditorWindow()
    window.load_from_fornax(
        manager.document(original), path=original, mode=SIGNATURES_MODE,
        model_id=status.descriptor.model_id,
        asset_provider=lambda reference: manager.asset(reference, original),
        session_manager=manager, save_as_required=True,
    )
    try:
        with (
            patch("features.editor.editor_window.get_models_dir", return_value=models),
            patch("features.editor.editor_window.dialog_get_text", return_value=("Cópia segura", True)),
            patch.object(window, "_choose_fornax_protection", return_value=(PUBLIC_MODE, False)),
            patch.object(window, "_show_save_success_dialog"),
        ):
            window._export_to_fornax(window.get_current_scene_state())

        copied = models / "copia_segura.fornax"
        assert copied.is_file()
        assert original.read_bytes() == original_bytes
        assert inspect_fornax(copied).model_id != inspect_fornax(original).model_id
        opened = open_public_fornax(copied)
        assert opened.document()["name"] == "Cópia segura"
        assert opened.document()["pages"][0]["signatures"] == []
    finally:
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()
        manager.close()
        APP.processEvents()


def test_editor_does_not_repeat_public_signature_choice_after_acceptance(tmp_path):
    signature = tmp_path / "signature.png"
    image = QImage(24, 12, QImage.Format.Format_ARGB32)
    image.fill(QColor("#151515"))
    assert image.save(str(signature), "PNG")
    package = tmp_path / "signed.fornax"
    save_public_fornax(_signature_document(signature), package)
    manager = FornaxSessionManager()
    initial = manager.select(package)
    window = EditorWindow()
    window.load_from_fornax(
        manager.document(package), path=package, mode=PUBLIC_MODE,
        model_id=initial.descriptor.model_id,
        asset_provider=lambda reference: manager.asset(reference, package),
        session_manager=manager,
    )
    try:
        with (
            patch.object(window, "_choose_fornax_protection") as choose,
            patch.object(window, "_show_save_success_dialog"),
        ):
            window._export_to_fornax(window.get_current_scene_state())
        choose.assert_not_called()
        assert inspect_fornax(package).version == 2
        assert open_public_fornax(package).document()["protection_preferences"] == {
            "public_signatures_acknowledged": True,
        }
    finally:
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()
        manager.close()
        APP.processEvents()


def test_save_as_resets_acceptance_and_cancel_keeps_original(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    signature = tmp_path / "signature.png"
    image = QImage(24, 12, QImage.Format.Format_ARGB32)
    image.fill(QColor("#151515"))
    assert image.save(str(signature), "PNG")
    original = models / "original.fornax"
    save_public_fornax(_signature_document(signature), original)
    original_bytes = original.read_bytes()
    manager = FornaxSessionManager()
    status = manager.select(original)
    window = EditorWindow()
    window.load_from_fornax(
        manager.document(original), path=original, mode=PUBLIC_MODE,
        model_id=status.descriptor.model_id,
        asset_provider=lambda reference: manager.asset(reference, original),
        session_manager=manager, save_as_required=True,
    )
    try:
        with (
            patch("features.editor.editor_window.get_models_dir", return_value=models),
            patch("features.editor.editor_window.dialog_get_text", return_value=("Nova cópia", True)),
            patch.object(window, "_choose_fornax_protection", return_value=None) as choose,
        ):
            window._export_to_fornax(window.get_current_scene_state())
        choose.assert_called_once_with(True)
        assert original.read_bytes() == original_bytes
        assert not (models / "nova_copia.fornax").exists()
    finally:
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()
        manager.close()
        APP.processEvents()


def test_save_as_public_signature_records_fresh_acceptance_after_success(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    signature = tmp_path / "signature.png"
    image = QImage(24, 12, QImage.Format.Format_ARGB32)
    image.fill(QColor("#151515"))
    assert image.save(str(signature), "PNG")
    original = models / "original.fornax"
    save_public_fornax(_signature_document(signature), original)
    original_id = inspect_fornax(original).model_id
    manager = FornaxSessionManager()
    status = manager.select(original)
    window = EditorWindow()
    window.load_from_fornax(
        manager.document(original), path=original, mode=PUBLIC_MODE,
        model_id=status.descriptor.model_id,
        asset_provider=lambda reference: manager.asset(reference, original),
        session_manager=manager, save_as_required=True,
    )
    try:
        with (
            patch("features.editor.editor_window.get_models_dir", return_value=models),
            patch("features.editor.editor_window.dialog_get_text", return_value=("Nova cópia", True)),
            patch.object(
                window, "_choose_fornax_protection", return_value=(PUBLIC_MODE, True),
            ) as choose,
            patch.object(window, "_show_save_success_dialog"),
        ):
            window._export_to_fornax(window.get_current_scene_state())

        copied = models / "nova_copia.fornax"
        choose.assert_called_once_with(True)
        assert copied.is_file()
        assert inspect_fornax(copied).model_id != original_id
        assert open_public_fornax(copied).document()["protection_preferences"] == {
            "public_signatures_acknowledged": True,
        }
    finally:
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()
        manager.close()
        APP.processEvents()
