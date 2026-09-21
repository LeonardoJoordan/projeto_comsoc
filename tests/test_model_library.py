import os
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QMessageBox

from core.fornax_container import (
    FULL_MODE,
    SIGNATURES_MODE,
    inspect_fornax,
    open_public_fornax,
    save_protected_fornax,
    save_public_fornax,
)
from core.model_document import normalize_model_document, save_model_document
from core.model_library import scan_model_library
from features.generator.renderer import renderers_for_document
from features.workspace.main_window import MainWindow


APP = QApplication.instance() or QApplication([])


def _document(name="Modelo Fornax", *, background_path=None, image_path=None):
    document = normalize_model_document({
        "name": name,
        "canvas_size": {"w": 120, "h": 80},
        "target_w_mm": 60.0,
        "target_h_mm": 40.0,
        "placeholders": ["nome"],
        "background_path": background_path,
        "bg_props": {
            "x": 0, "y": 0, "w": 120, "h": 80,
            "opacity": 1.0, "visible": True,
        },
        "boxes": [{
            "id": "nome", "html": "{nome}",
            "x": 10, "y": 20, "w": 100, "h": 30,
            "font_family": "Inter", "font_size": 14,
            "align": "center", "visible": True,
        }],
    })
    page = document["pages"][0]
    if image_path:
        page["images"].append({
            "object_id": "image:test", "path": str(image_path),
            "x": 0, "y": 0, "width": 120, "height": 80,
            "rotation": 0, "opacity": 1.0, "visible": True,
        })
    page["layer_order"] = [
        item["object_id"]
        for collection in ("shapes", "images", "signatures", "boxes")
        for item in page[collection]
    ]
    return document


def test_library_scans_legacy_public_and_full_without_leaking_full_name(tmp_path):
    legacy = tmp_path / "legado"
    save_model_document(_document("Modelo legado"), legacy)
    save_public_fornax(_document("Modelo público"), tmp_path / "publico.fornax")
    save_protected_fornax(
        _document("Nome secreto"), tmp_path / "arquivo-neutro.fornax",
        "senha-segura", mode=FULL_MODE,
    )
    (tmp_path / ".publico.fornax.pending-resto.fornax").write_bytes(b"incompleto")
    (tmp_path / "invalido.fornax").write_bytes(b"invalido")

    found = scan_model_library(tmp_path)

    assert {item.kind for item in found} == {"legacy", "fornax"}
    assert {item.display_name for item in found} == {
        "Modelo legado", "Modelo público", "arquivo-neutro",
    }
    assert all("Nome secreto" not in item.display_name for item in found)
    assert len({item.key for item in found}) == 3


def test_renderer_reads_public_fornax_assets_in_memory_with_visual_parity(tmp_path):
    background = tmp_path / "background.png"
    image = QImage(120, 80, QImage.Format.Format_ARGB32)
    image.fill(QColor("#8b4fd8"))
    assert image.save(str(background), "PNG")
    source = _document("Paridade", image_path=str(background))
    destination = tmp_path / "paridade.fornax"
    save_public_fornax(source, destination)

    opened = open_public_fornax(destination)
    legacy_image = renderers_for_document(source)[0].render_to_qimage(
        {"nome": "Ana"}, {"nome": "Ana"}
    )
    fornax_image = renderers_for_document(
        opened.document(), asset_provider=opened.asset,
    )[0].render_to_qimage({"nome": "Ana"}, {"nome": "Ana"})

    assert fornax_image == legacy_image


def test_workspace_selects_public_fornax_and_builds_preview_and_table(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    package = models / "modelo-publico.fornax"
    save_public_fornax(_document("Modelo público"), package)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)

    patches = (
        patch("features.workspace.main_window.get_models_dir", return_value=models),
        patch("features.workspace.frontend.get_models_dir", return_value=models),
        patch("features.workspace.main_window.get_app_settings", return_value=settings),
    )
    for current in patches:
        current.start()
    try:
        window = MainWindow()
    finally:
        for current in reversed(patches):
            current.stop()
    try:
        APP.processEvents()
        assert window.preview_panel.cbo_models.currentText() == "Modelo público"
        assert window.cached_model_document["schema_version"] == 4
        assert window.table_panel.table.horizontalHeaderItem(1).text() == "nome"
        pixmap = window.preview_panel.preview._pixmap
        assert pixmap is not None and not pixmap.isNull()
        assert window._fornax_asset_provider is not None
        assert window.btn_config_model.isEnabled()
        assert not list(models.glob("**/.render_cache/*"))
        old_revision = inspect_fornax(package).revision_id
        window._update_template_json({"output_suffix": "{nome}_final"})
        assert inspect_fornax(package).revision_id != old_revision
        assert open_public_fornax(package).document()["output_suffix"] == "{nome}_final"
    finally:
        window.close()
        APP.processEvents()


def test_workspace_converts_unsigned_legacy_model_when_selected(tmp_path):
    models = tmp_path / "models"
    legacy = models / "modelo-legado"
    save_model_document(_document("Modelo legado"), legacy)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    patches = (
        patch("features.workspace.main_window.get_models_dir", return_value=models),
        patch("features.workspace.frontend.get_models_dir", return_value=models),
        patch("features.workspace.main_window.get_app_settings", return_value=settings),
    )
    for current in patches:
        current.start()
    try:
        window = MainWindow()
    finally:
        for current in reversed(patches):
            current.stop()
    try:
        APP.processEvents()
        assert not legacy.exists()
        packages = list(models.glob("*.fornax"))
        assert len(packages) == 1
        assert window._active_library_model.is_fornax
        assert window.cached_model_document["name"] == "Modelo legado"
        assert len(window.cached_model_document["pages"]) == 1
    finally:
        window.close()
        APP.processEvents()


def test_workspace_opens_full_protected_model_neutral_without_prompt(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    password = "senha-segura"
    expected_name = "2.2.1 - Nome interno confidencial"
    save_protected_fornax(
        _document(expected_name), models / "221_nome_interno_confidencial.fornax",
        password, mode=FULL_MODE,
    )
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    question = Mock()
    patches = (
        patch("features.workspace.main_window.get_models_dir", return_value=models),
        patch("features.workspace.frontend.get_models_dir", return_value=models),
        patch("features.workspace.main_window.get_app_settings", return_value=settings),
        patch("features.workspace.main_window.QMessageBox.question", new=question),
    )
    for current in patches:
        current.start()
    try:
        window = MainWindow()
    finally:
        for current in reversed(patches):
            current.stop()
    try:
        APP.processEvents()
        assert window.preview_panel.cbo_models.currentText() == "221_nome_interno_confidencial"
        assert window.cached_model_document is None
        assert window.preview_panel.preview.text() == "Modelo protegido"
        assert window.table_panel.table.columnCount() == 1
        assert not window.btn_config_model.isEnabled()
        assert not window.preview_panel.btn_unlock_model.isHidden()
        assert window.preview_panel.btn_unlock_model.isEnabled()
        assert window.preview_panel.btn_unlock_model.text() == "Desbloquear modelo"
        question.assert_not_called()

        password_prompt = Mock(return_value=password)
        window._request_fornax_password = password_prompt
        with patch("features.workspace.main_window.get_models_dir", return_value=models):
            window.preview_panel.btn_unlock_model.click()
            APP.processEvents()
        assert window.preview_panel.cbo_models.currentText() == expected_name
        assert window.preview_panel.btn_unlock_model.text() == "Bloquear modelo"

        window.preview_panel.btn_unlock_model.click()
        APP.processEvents()
        assert window.preview_panel.cbo_models.currentText() == expected_name
        assert window.cached_model_document is None
        assert window.preview_panel.btn_unlock_model.text() == "Desbloquear modelo"
        password_prompt.assert_called_once()
    finally:
        window.close()
        APP.processEvents()


def test_signature_protected_model_opens_without_prompt_and_unlocks_from_button(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    password = "senha-segura"
    package = models / "assinatura-protegida.fornax"
    signature = tmp_path / "signature.svg"
    signature.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10">'
        '<path d="M1 8 L19 2" stroke="black"/></svg>',
        encoding="utf-8",
    )
    document = _document("Assinatura protegida")
    document["pages"][0]["signatures"].append({
        "object_id": "signature:test", "signature_id": "test",
        "path": "signature.svg", "x": 20, "y": 30,
        "width": 40, "height": 20, "rotation": 0,
        "opacity": 1.0, "visible": True,
    })
    document["pages"][0]["layer_order"].append("signature:test")
    save_protected_fornax(
        document, package, password,
        mode=SIGNATURES_MODE, source_dir=tmp_path,
    )
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    patches = (
        patch("features.workspace.main_window.get_models_dir", return_value=models),
        patch("features.workspace.frontend.get_models_dir", return_value=models),
        patch("features.workspace.main_window.get_app_settings", return_value=settings),
    )
    for current in patches:
        current.start()
    try:
        window = MainWindow()
    finally:
        for current in reversed(patches):
            current.stop()
    try:
        APP.processEvents()
        password_prompt = Mock(return_value=password)
        window._request_fornax_password = password_prompt
        assert not window.preview_panel.btn_unlock_model.isHidden()
        assert window.preview_panel.btn_unlock_model.isEnabled()
        assert not window.cached_model_document["pages"][0]["signatures"]
        password_prompt.assert_not_called()

        with patch("features.workspace.main_window.get_models_dir", return_value=models):
            window.preview_panel.btn_unlock_model.click()
            APP.processEvents()
        assert window.cached_model_document["pages"][0]["signatures"]
        assert window.preview_panel.btn_unlock_model.text() == "Bloquear modelo"
        password_prompt.assert_called_once()
    finally:
        window.close()
        APP.processEvents()


def test_library_restores_only_encrypted_package_bytes_from_valid_backup(tmp_path):
    package = tmp_path / "recuperavel.fornax"
    save_public_fornax(_document("Primeira revisão"), package)
    save_public_fornax(_document("Segunda revisão"), package)
    backup = package.with_name(package.name + ".bak")
    expected = backup.read_bytes()
    package.write_bytes(b"interrupted revision")

    found = scan_model_library(tmp_path)

    assert len(found) == 1
    assert found[0].display_name == "Primeira revisão"
    assert package.read_bytes() == expected
