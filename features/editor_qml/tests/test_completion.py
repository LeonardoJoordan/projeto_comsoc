from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt, QSettings, QCoreApplication, QEvent
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QTableWidgetItem, QMessageBox
from PySide6.QtTest import QTest
from features.editor_qml.bridge import EditorBridge
from features.editor_qml.preview_service import paint_preview
from features.editor_qml.session import EditorSession
from core.history_manager import HistoryManager

APP = QApplication.instance() or QApplication([])


def until(predicate, timeout=3000):
    for _ in range(timeout // 10):
        if predicate():
            return True
        QTest.qWait(10)
    return predicate()


class CompletionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.bridge = EditorBridge()
        self.errors = []
        self.bridge.error.connect(self.errors.append)

    def tearDown(self):
        self.bridge.shutdown()
        self.temp.cleanup()

    def test_noop_history_save_keeps_redo(self):
        self.bridge.addItem("text")
        path = self.base / "template_v3.json"
        self.assertTrue(self.bridge.save_to(path))
        self.bridge.setValue("html", "<p>changed</p>")
        self.bridge.undo()
        self.assertTrue(self.bridge.save())
        self.assertTrue(self.bridge.state["canRedo"])
        self.bridge.redo()
        self.assertIn("changed", self.bridge._data["boxes"][0]["html"])

    def test_text_paint_replays_without_accessing_gui_document_in_render_thread(self):
        from features.editor_qml.canvas_text_editor import CanvasTextEditor
        item = CanvasTextEditor()
        item.beginEditing({"w": 300, "h": 100, "html": "<p>Texto</p>", "font_size": 20})
        item.selectRange(0, 3)

        def render():
            image = QImage(320, 120, QImage.Format_ARGB32)
            image.fill(Qt.white)
            painter = QPainter(image)
            try:
                item.paint(painter)
            finally:
                painter.end()
            return image

        expected = render()
        doc, cursor = item._doc, item._cursor

        class GuiOnly:
            def __getattr__(self, name):
                raise AssertionError(f"A pintura acessou estado da GUI: {name}")

        results, errors = [], []
        def run():
            try:
                results.append(render())
            except Exception as exc:
                errors.append(exc)

        try:
            item._doc = item._cursor = GuiOnly()
            thread = threading.Thread(target=run)
            thread.start()
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors, errors)
            self.assertEqual(results, [expected])
        finally:
            item._doc, item._cursor = doc, cursor
        item.insertText("Alterado")
        self.assertNotEqual(render(), expected)

    def test_missing_inline_fonts_warn_without_replacing_names(self):
        self.bridge.addItem("text")
        self.bridge.setValue("font_family", "Comsoc Missing Family 9876")
        self.bridge._data["boxes"][0].update(rich_text_version=1, html="<p><span style=\"font-family:'Comsoc Missing Inline 1234';\">Name</span></p>")
        self.bridge.notify(True)
        self.assertIn("Comsoc Missing Family 9876", self.bridge.state["missingFonts"])
        self.assertIn("Comsoc Missing Inline 1234", self.bridge.state["missingFonts"])
        path = self.base / "template_v3.json"
        self.assertTrue(self.bridge.save_to(path))
        saved = json.loads(path.read_text())
        self.assertEqual(saved["boxes"][0]["font_family"], "Comsoc Missing Family 9876")
        self.assertIn("Comsoc Missing Inline 1234", saved["boxes"][0]["html"])

    def test_async_preview_coalesces_and_discards_stale_results(self):
        entered, release = threading.Event(), threading.Event()
        calls = []

        def slow(data, editing_key=""):
            calls.append(data["shapes"][0]["fill_color"])
            if len(calls) == 1:
                entered.set()
                release.wait(3)
            return paint_preview(data, editing_key)

        self.bridge.addItem("shape")
        self.bridge.setValue("fill_color", "#ff0000")
        with patch("features.editor_qml.preview_service.paint_preview", side_effect=slow):
            try:
                self.bridge._render_timer.stop()
                self.bridge.requestPreview()
                self.assertTrue(entered.wait(1))
                self.bridge.setValue("fill_color", "#00ff00")
                self.bridge._render_timer.stop()
                self.bridge.requestPreview()
                self.bridge.setValue("fill_color", "#0000ff")
                self.bridge._render_timer.stop()
                self.bridge.requestPreview()
                QTest.qWait(30)  # O loop da interface continua disponível com o worker bloqueado.
                self.assertTrue(self.bridge.state["previewBusy"])
            finally:
                release.set()
            self.assertTrue(until(lambda: not self.bridge.state["previewBusy"]))
        self.assertEqual(calls, ["#ff0000", "#0000ff"])
        self.assertEqual(self.bridge.provider.image.pixelColor(100, 100), QColor("blue"))
        self.assertFalse(self.errors)

    def test_dimensions_replacement_links_and_invalid_load(self):
        self.assertTrue(self.bridge.setDocumentSize("800", "600", "210", "148,5"))
        self.assertEqual(self.bridge.documentSize["heightMm"], 148.5)
        self.bridge.undo()
        self.assertEqual(self.bridge.documentSize["w"], 1000)
        asset = self.base / "replacement.png"
        image = QImage(30, 20, QImage.Format_ARGB32)
        image.fill(Qt.red)
        image.save(str(asset))
        self.bridge.insert_item("image", {"path": "old.png", "x": 12, "width": 65, "height": 40, "rotation": 25})
        key = self.bridge._selected
        self.assertTrue(self.bridge.replace_asset(asset))
        self.assertEqual(self.bridge._selected, key)
        self.assertEqual(self.bridge.state["selected"]["w"], 65)
        self.assertEqual(self.bridge.state["selected"]["rotation"], 25)
        self.bridge.setValue("has_link", True)
        self.bridge.setValue("link_key", "Website")
        self.assertEqual(self.bridge.state["fields"], ["Website"])
        self.bridge.setValue("locked", True)
        self.assertFalse(self.bridge.replace_asset(asset))
        before = deepcopy(self.bridge._data)
        path = self.base / "invalid.json"
        path.write_text('{"canvas_size":{"w":100,"h":100},"boxes":[{"w":"oops"}]}')
        self.assertFalse(self.bridge.load(str(path)))
        self.assertEqual(self.bridge._data, before)
        self.bridge.addGuide(True)
        self.bridge.guideOption("guidelines_locked", True)
        self.bridge.deleteGuide(0)
        self.assertEqual(len(self.bridge.state["guides"]), 1)
        self.bridge.guideOption("guidelines_locked", False)
        with patch("features.editor_qml.bridge.QInputDialog.getDouble", return_value=(42.5, True)):
            self.bridge.editGuide(0)
        self.assertEqual(self.bridge.state["guides"][0]["pos"], 42.5)
        self.bridge.deleteGuide(0)
        self.bridge.undo()
        self.assertEqual(self.bridge.state["guides"][0]["pos"], 42.5)

    def test_save_signal_only_after_success(self):
        emitted = []
        self.bridge.modelSaved.connect(lambda *args: emitted.append(args))
        path = self.base / "template_v3.json"
        self.assertTrue(self.bridge.save_to(path))
        self.assertEqual(emitted[0][2], str(path))
        path.write_text(path.read_text()+" ")
        self.assertFalse(self.bridge.save())
        self.assertEqual(len(emitted), 1)


class WorkspaceEditorTest(unittest.TestCase):
    def setUp(self):
        from features.workspace.main_window import MainWindow
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.models = self.base / "models"
        self.models.mkdir()
        settings = QSettings(str(self.base / "settings.ini"), QSettings.IniFormat)
        self.patches = [patch("features.workspace.main_window.get_models_dir", return_value=self.models),
                        patch("features.editor_qml.bridge.get_models_dir", return_value=self.models),
                        patch("features.workspace.main_window.QSettings", return_value=settings)]
        for p in self.patches:
            p.start()
        bridge = EditorBridge()
        bridge.addItem("text")
        bridge.setValue("html", "<p>{Nome}</p>")
        self.path = self.models / "sample" / "template_v3.json"
        self.assertTrue(bridge.save_to(self.path, "Sample"))
        bridge.shutdown()
        self.window = MainWindow()

    def tearDown(self):
        for session in tuple(self.window._qml_editors):
            session.bridge._saved = deepcopy(session.bridge._data)
            session.close()
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_choice_save_refresh_and_preserve_table_values(self):
        self.assertEqual(self.window.preview_panel.cbo_editor.currentData(), "legacy")
        self.window.preview_panel.cbo_editor.setCurrentIndex(self.window.preview_panel.cbo_editor.findData("qml"))
        self.window._open_model_dialog()
        session = next(iter(self.window._qml_editors))
        self.assertEqual(session.bridge._path, self.path)
        self.window._open_model_dialog()
        self.assertEqual(len(self.window._qml_editors), 1)
        table = self.window.table_panel.table
        table.setRowCount(2)
        name = QTableWidgetItem("Ana")
        name.setData(Qt.UserRole, "<b>Ana</b>")
        table.setItem(0, 1, name)
        table.setItem(0, 0, QTableWidgetItem("3"))
        table.setItem(1, 1, QTableWidgetItem("Bruno"))
        session.bridge.addItem("text")
        session.bridge.setValue("html", "<p>{Cargo}</p>")
        self.assertTrue(session.bridge.save())
        self.assertEqual(self.window.cached_model_data["placeholders"], ["Nome", "Cargo"])
        self.assertEqual(table.rowCount(), 2)
        self.assertEqual(table.item(0, 1).text(), "Ana")
        self.assertEqual(table.item(0, 1).data(Qt.UserRole), "<b>Ana</b>")
        self.assertEqual(table.item(0, 0).text(), "3")
        self.assertEqual(table.item(1, 1).text(), "Bruno")
        self.assertEqual(table.horizontalHeaderItem(2).text(), "Cargo")
        self.assertIsNotNone(self.window.preview_renderer)
        self.assertEqual(self.window.settings.value("model_editor"), "qml")
        session.bridge.setValue("font_size", 29)
        self.assertTrue(session.bridge.save())
        self.assertEqual(table.item(0, 1).text(), "Ana")

    def test_legacy_choice_and_workspace_close_cancellation(self):
        with patch("features.workspace.main_window.EditorWindow") as legacy:
            self.window.preview_panel.cbo_editor.setCurrentIndex(self.window.preview_panel.cbo_editor.findData("legacy"))
            self.window._on_add_model()
            legacy.assert_called_once_with(self.window)
        self.window.preview_panel.cbo_editor.setCurrentIndex(self.window.preview_panel.cbo_editor.findData("qml"))
        self.window._on_add_model()
        session = next(iter(self.window._qml_editors))
        session.bridge.addItem("shape")
        with patch("features.editor_qml.bridge.QMessageBox.question", return_value=QMessageBox.Cancel):
            self.assertFalse(self.window.close())
        self.assertTrue(session.window.isVisible())

    def test_new_qml_model_saves_into_library_and_save_as_preserves_rows(self):
        session = self.window._open_qml_editor(self.path)
        table = self.window.table_panel.table
        table.setItem(0, 1, QTableWidgetItem("Ana"))
        with patch("features.editor_qml.bridge.QInputDialog.getText", return_value=("Sample Copy", True)):
            self.assertTrue(session.bridge.saveAs())
        self.assertEqual(self.window.preview_panel.cbo_models.currentText(), "Sample Copy")
        self.assertEqual(table.item(0, 1).text(), "Ana")
        self.assertTrue((self.models / "sample_copy" / "template_v3.json").exists())
        self.assertEqual(self.window.cached_model_data["name"], "Sample Copy")


if __name__ == "__main__":
    unittest.main()
