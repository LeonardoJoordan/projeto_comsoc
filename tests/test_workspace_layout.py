import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from core.model_document import load_model_document
from features.workspace.main_window import MainWindow


APP = QApplication.instance() or QApplication([])


def _workspace(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    patches = (
        patch("features.workspace.main_window.get_models_dir", return_value=models),
        patch("features.workspace.frontend.get_models_dir", return_value=models),
        patch(
            "features.workspace.main_window.get_app_settings",
            return_value=settings,
        ),
    )
    for current in patches:
        current.start()
    try:
        window = MainWindow()
    finally:
        for current in reversed(patches):
            current.stop()
    return window, models


def _close(window):
    window.close()
    APP.processEvents()


def test_workspace_builds_the_approved_layout_directly(tmp_path):
    window, _models = _workspace(tmp_path)
    try:
        window.show()
        APP.processEvents()

        assert window.splitter.count() == 2
        assert not hasattr(window, "controls_panel")
        assert not hasattr(window, "left_panel")
        assert not hasattr(window, "preview_container")
        assert window.btn_config_model.isVisible()
        assert window.footer_container.parentWidget().objectName() == "previewWorkspace"
        assert window.table_panel.parentWidget().objectName() == "dataRail"
    finally:
        _close(window)


def test_clean_install_creates_a_valid_starter_model_and_closes_workers(tmp_path):
    window, models = _workspace(tmp_path)
    try:
        document = load_model_document(models / "modelo_exemplo")
        front = document["pages"][0]
        object_ids = {
            item["object_id"]
            for collection in ("shapes", "images", "signatures", "boxes")
            for item in front[collection]
        }
        assert set(front["layer_order"]) == object_ids
        assert window.preview_panel.cbo_models.currentText() == "Modelo Exemplo"
    finally:
        _close(window)

    assert not window._preview_workers
    assert not window._sheet_preview_workers
