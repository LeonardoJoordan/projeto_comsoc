import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTableWidgetItem

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


def test_about_menu_exposes_first_steps_tutorial(tmp_path):
    window, _models = _workspace(tmp_path)
    try:
        assert window._tutorial_menu.title() == "Tutorial interativo"
        assert [action.text() for action in window._tutorial_actions] == [
            "Primeiros passos",
        ]
        assert window._first_steps_tutorial_action.isEnabled()
        assert window._tutorial_menu.isEnabled()
    finally:
        _close(window)


def test_first_steps_tutorial_opens_editor_and_waits_for_real_text_action(tmp_path):
    window, _models = _workspace(tmp_path)
    editor = None
    try:
        window.show()
        window._first_steps_tutorial_action.trigger()
        APP.processEvents()

        tutorial = window._active_tutorial
        assert tutorial.step == 1
        assert tutorial.coach.card.title.text() == "Primeiros passos"
        card = tutorial.coach.card
        assert abs(card.next.geometry().center().x() - card.rect().center().x()) <= 1
        assert card.next.height() == 30
        assert card.back.height() == card.skip.height() == 24

        tutorial.next()
        APP.processEvents()
        assert tutorial.step == 2
        window._model_menu.aboutToShow.emit()
        APP.processEvents()
        assert tutorial.step == 3
        assert tutorial._menu_spotlight is not None
        assert tutorial._menu_spotlight._target_rect == window._model_menu.actionGeometry(
            window._new_model_action
        ).adjusted(2, 1, -2, -1)
        assert not tutorial.coach.spotlight._target_rect.isValid()
        window._new_model_action.trigger()
        APP.processEvents()
        editor = tutorial.editor
        assert editor is window.editor_window
        assert tutorial.step == 4

        tutorial.next()
        APP.processEvents()
        assert tutorial.step == 5
        assert tutorial.coach.target is editor.btn_add

        editor.btn_add.click()
        APP.processEvents()
        assert tutorial.step == 6
        assert tutorial.text_box is not None
        assert editor.lst_placeholders.count() == 1
        assert editor.lst_placeholders.item(0).text() == "campo"

        tutorial.next()  # redimensionamento
        box_rect = tutorial.text_box.rect()
        tutorial.text_box.setRect(
            box_rect.x(), box_rect.y(), box_rect.width() + 40, box_rect.height()
        )
        tutorial._poll_current_step()
        assert tutorial.step == 8
        tutorial.next()
        assert tutorial.coach.target is editor._text_section.header
        tutorial.next()
        center_button = editor.editor_texto_panel.alignment_buttons[1]
        alignment = editor.editor_texto_panel.alignment_widget
        alignment_top_left = alignment.mapTo(editor, alignment.rect().topLeft())
        alignment_rect = alignment.rect().translated(alignment_top_left)
        assert not tutorial.coach.card.geometry().intersects(alignment_rect)
        QTest.mouseClick(center_button, Qt.MouseButton.LeftButton)
        APP.processEvents()
        assert tutorial.step == 11
        tutorial.next()
        middle_button = editor.editor_texto_panel.alignment_buttons[5]
        QTest.mouseClick(middle_button, Qt.MouseButton.LeftButton)
        APP.processEvents()
        assert tutorial.step == 13
        tutorial.next()
        assert tutorial.step == 14
        editor.editor_texto_panel.spin_size.setValue(45)
        APP.processEvents()
        assert tutorial.step == 15
        tutorial.text_box.state.html_content = (
            "Este cartão foi feito de forma muito rápida e eficiente para "
            "{nome}| com a ajuda de {programa}|!"
        )
        tutorial._poll_current_step()
        assert tutorial.step == 15
        assert tutorial._phase == 1
        box_rect = tutorial.text_box.rect()
        tutorial.text_box.setRect(
            box_rect.x(), box_rect.y(), box_rect.width() + 40, box_rect.height()
        )
        tutorial._poll_current_step()
        assert tutorial.step == 15
        assert tutorial._phase == 1
        tutorial.next()
        assert tutorial.step == 16
        assert {
            editor.lst_placeholders.item(index).text()
            for index in range(editor.lst_placeholders.count())
        } == {"nome", "programa"}

        tutorial.finish()
        APP.processEvents()
        assert window._active_tutorial is None
    finally:
        if editor is not None:
            editor._last_saved_state = editor.get_current_scene_state()
            editor.close()
            APP.processEvents()
        _close(window)


def test_first_steps_tutorial_validates_bulk_table_exercises(tmp_path):
    window, _models = _workspace(tmp_path)
    try:
        window.show()
        window._first_steps_tutorial_action.trigger()
        APP.processEvents()
        tutorial = window._active_tutorial
        table = window.table_panel.table
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Cópias", "nome", "programa"])
        table.setRowCount(1)

        tutorial.step = 21
        tutorial._show_step()
        for row, name in enumerate((
            "Ana Silva", "Bruno Costa", "Carla Souza", "Daniel Lima", "Elisa Rocha",
            "Felipe Alves", "Gabriela Nunes", "Henrique Melo", "Isabela Martins", "João Ribeiro",
        )):
            if row >= table.rowCount():
                table.insertRow(row)
            table.setItem(row, 1, QTableWidgetItem(name))
        tutorial._poll_current_step()
        assert tutorial.step == 22

        tutorial.next()
        tutorial.next()
        for row in range(10):
            table.setItem(row, 2, QTableWidgetItem("FORNAX Forge"))
        tutorial._poll_current_step()
        assert tutorial.step == 24

        tutorial.next()
        table.setCurrentCell(5, 1)
        table.setCurrentCell(6, 1)
        QTest.qWait(220)
        assert tutorial.step == 24
        assert tutorial._phase == 2
        tutorial.next()
        assert tutorial.step == 25
        table.selectAll()
        window.table_panel.btn_delete_rows.click()
        APP.processEvents()
        assert tutorial.step == 26

        for row, name in enumerate((
            "Ana Silva", "Bruno Costa", "Carla Souza", "Daniel Lima", "Elisa Rocha",
            "Felipe Alves", "Gabriela Nunes", "Henrique Melo", "Isabela Martins", "João Ribeiro",
        )):
            if row >= table.rowCount():
                table.insertRow(row)
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 2, QTableWidgetItem("FORNAX Forge"))
        tutorial._poll_current_step()
        assert tutorial.step == 27
        tutorial.next()
        table.setCurrentCell(0, 1)
        table.setCurrentCell(1, 1)
        QTest.qWait(220)
        assert tutorial.step == 27
        assert tutorial._phase == 2
        tutorial.next()
        assert tutorial.step == 28
    finally:
        if getattr(window, "_active_tutorial", None):
            window._active_tutorial.finish()
        _close(window)
