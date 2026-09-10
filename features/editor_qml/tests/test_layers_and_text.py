"""Verificações específicas das etapas de camadas e edição nativa de texto."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QTextCursor, QTextDocument
from PySide6.QtWidgets import QApplication
from core.document_layers import upgrade_layers, layer_entries
from core.text_layout import build_document, resolve_rich_text
from features.generator.renderer import NativeRenderer
from features.editor_qml.bridge import EditorBridge
from features.editor_qml.canvas_text_editor import CanvasTextEditor

APP = QApplication.instance() or QApplication([])
ROOT = Path(__file__).resolve().parents[3]


class LayersAndTextTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.bridge = EditorBridge()
        self.edit = CanvasTextEditor()
        self.bridge.attachTextEditor(self.edit)
        self.errors = []
        self.bridge.error.connect(self.errors.append)

    def tearDown(self):
        self.bridge.shutdown()
        self.edit.deleteLater()
        self.temp.cleanup()

    def start(self, content="<p>Alpha Beta</p>"):
        self.bridge.addItem("text")
        self.bridge.setValue("html", content)
        self.bridge.startTextSession(self.bridge._selected)

    def char_format(self, position):
        cursor = QTextCursor(self.edit._doc)
        cursor.setPosition(position)
        cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        return cursor.charFormat()

    def asset(self, name, color):
        image = QImage(100, 100, QImage.Format_ARGB32)
        image.fill(QColor(color))
        path = self.base / name
        image.save(str(path))
        return str(path)

    def test_migration_preserves_rendering_and_is_idempotent(self):
        for name in ("teste", "teste2"):
            path = ROOT / "models" / name / "template_v3.json"
            original = path.read_bytes()
            data = json.loads(original)
            data["__model_dir"] = str(path.parent)
            if data.get("background_path"):
                data["background_path"] = str(path.parent / data["background_path"])
            for group in ("images", "signatures"):
                for item in data.get(group, []):
                    item["path"] = str(path.parent / item["path"])
            migrated = upgrade_layers(data)
            self.assertEqual(migrated, upgrade_layers(migrated))
            self.assertEqual(NativeRenderer(data).render_to_pixmap().toImage(), NativeRenderer(migrated).render_to_pixmap().toImage())
            self.assertEqual(path.read_bytes(), original)
            self.assertIsNone(migrated["background_path"])
            if data.get("background_path"):
                self.assertEqual(layer_entries(migrated)[0][1], "image")

    def test_global_order_and_static_cache_match_with_link_and_signature(self):
        data = upgrade_layers({"canvas_size": {"w": 100, "h": 100},
            "images": [{"path": self.asset("red.png", "red"), "width": 100, "height": 100, "has_link": True, "link_key": "URL"}],
            "boxes": [{"html": "<p>MMMM</p>", "w": 100, "h": 100, "font_size": 30}],
            "signatures": [{"path": self.asset("blue.png", "blue"), "width": 100, "height": 100}]})
        image, text, signature = data["layer_order"]
        for order in ([image, text, signature], [signature, text, image], [image, signature, text]):
            data["layer_order"] = order
            for visible in (True, False):
                row = {"URL": "example.com", "__use_signature__": visible}
                renderer = NativeRenderer(data)
                links = []
                expected = renderer.render_to_qimage(row, row, links)
                renderer.pre_render_static_base()
                cached_links = []
                self.assertEqual(expected, renderer.render_to_qimage(row, row, cached_links))
                self.assertEqual(links, cached_links)
                self.assertEqual(len(links), 1)
                if order[-1] == image:
                    self.assertEqual(expected.pixelColor(50, 50), QColor("red"))
                elif order[-1] == signature and visible:
                    self.assertEqual(expected.pixelColor(50, 50), QColor("blue"))

    def test_active_editor_composes_lower_and_upper_layers_in_order(self):
        self.bridge.insert_item("image", {"path": self.asset("red.png", "red"), "width": 1000, "height": 700})
        self.bridge.addItem("text")
        key = self.bridge._selected
        self.bridge.setValue("html", "<p>Alpha Beta</p>")
        self.bridge.insert_item("image", {"path": self.asset("blue.png", "blue"), "x": 80, "y": 50, "width": 30, "height": 50})
        self.bridge.render()
        expected = self.bridge.provider.image.copy()
        self.bridge.startTextSession(key)
        self.assertTrue(self.bridge.provider.above.hasAlphaChannel())
        actual = self.bridge.provider.image.copy()
        painter = QPainter(actual)
        painter.save()
        painter.translate(50, 50 + self.edit.contentTop)
        self.edit.paint(painter)
        painter.restore()
        painter.drawImage(0, 0, self.bridge.provider.above)
        painter.end()
        self.assertEqual(actual, expected)

    def test_selection_formatting_and_insertion_preserve_other_characters(self):
        self.start()
        self.edit.selectRange(0, 5)
        self.bridge.formatText("Negrito")
        self.bridge.setValue("font_size", 37)
        self.bridge.setValue("font_color", "#ff0000")
        self.assertEqual(self.char_format(0).fontWeight(), QFont.Bold)
        self.assertEqual(self.char_format(0).fontPointSize(), 37)
        self.assertEqual(self.char_format(0).foreground().color(), QColor("red"))
        self.assertNotEqual(self.char_format(6).fontWeight(), QFont.Bold)
        self.assertNotEqual(self.char_format(6).fontPointSize(), 37)
        self.assertNotEqual(self.char_format(6).foreground().color(), QColor("red"))
        self.edit.selectRange(10, 10)
        self.bridge.formatText("Itálico")
        self.edit.insertText("!")
        self.assertTrue(self.char_format(10).fontItalic())
        self.bridge.finishTextSession()
        saved = self.bridge._data["boxes"][0]["html"]
        self.bridge.undo()
        self.assertEqual(self.bridge._data["boxes"][0]["html"], "<p>Alpha Beta</p>")
        self.bridge.redo()
        self.assertEqual(self.bridge._data["boxes"][0]["html"], saved)

    def test_variable_optional_and_split_span_resolution(self):
        self.start("<p>😀 Olá </p>")
        self.assertTrue(self.edit.insertVariable("Nome"))
        self.edit.insertText(" |Cargo: {Cargo}|")
        self.edit.selectRange(9, 11)  # Parte do nome da variável, offsets UTF-16.
        self.bridge.formatText("Negrito")
        self.assertEqual(self.bridge.state["fields"], ["Nome", "Cargo"])
        box = self.bridge._data["boxes"][0]
        rendered = QTextDocument()
        rendered.setHtml(resolve_rich_text(box, {"Nome": "Ana", "Cargo": ""}))
        self.assertEqual(rendered.toPlainText(), "😀 Olá Ana ")
        rendered.setHtml(resolve_rich_text(box, {"Nome": "Ana", "Cargo": "Diretora"}))
        self.assertEqual(rendered.toPlainText(), "😀 Olá Ana Cargo: Diretora")
        self.assertIsNone(resolve_rich_text(box, {"Nome": "", "Cargo": ""}))
        self.edit.selectRange(0, 2)
        self.assertTrue(self.edit.wrapOptional())
        self.assertTrue(self.edit._doc.toPlainText().startswith("|😀|"))
        self.bridge.undo()
        self.assertTrue(self.edit._doc.toPlainText().startswith("😀"))
        self.bridge.redo()
        self.assertTrue(self.edit._doc.toPlainText().startswith("|😀|"))

    def test_save_finishes_session_and_reopens_rich_format(self):
        self.start()
        self.edit.selectRange(0, 5)
        self.bridge.setValue("font_color", "#123456")
        path = self.base / "template_v3.json"
        self.assertTrue(self.bridge.save_to(path), self.errors)
        self.assertFalse(self.bridge.editingText)
        self.assertTrue(self.bridge.load(str(path)))
        self.bridge.startTextSession(self.bridge._data["boxes"][0]["object_id"])
        self.assertEqual(self.char_format(0).foreground().color().name(), "#123456")
        self.assertEqual(self.char_format(6).foreground().color().name(), "#000000")

    def test_add_and_delete_finish_active_session(self):
        self.start()
        self.edit.insertText("!")
        self.bridge.addItem("text")
        self.assertFalse(self.bridge.editingText)
        self.assertIn("!", self.bridge._data["boxes"][0]["html"])
        self.bridge.startTextSession(self.bridge._selected)
        self.bridge.deleteSelected()
        self.assertFalse(self.bridge.editingText)
        self.bridge.render()
        self.assertFalse(self.errors)

    def test_noop_text_session_preserves_document_redo(self):
        self.bridge.addItem("text")
        self.bridge.setValue("html", "<p>Changed</p>")
        self.bridge.undo()
        before = deepcopy(self.bridge._data)
        self.bridge.startTextSession(self.bridge._data["boxes"][0]["object_id"])
        self.bridge.finishTextSession()
        self.assertEqual(self.bridge._data, before)
        self.assertTrue(self.bridge.state["canRedo"])
        self.bridge.startTextSession(self.bridge._selected)
        self.edit.insertText("!")
        self.bridge.undo()
        self.bridge.finishTextSession()
        self.assertEqual(self.bridge._data, before)
        self.assertTrue(self.bridge.state["canRedo"])

    def test_native_text_paint_matches_export_layout(self):
        for rich in (False, True):
            box = {"html": '<p>Texto <b>negrito</b></p><p>Outra linha</p>',
                   "x": 50, "y": 50, "w": 250, "h": 200, "rotation": 13,
                   "font_family": "Arial", "font_size": 20, "font_color": "#123456",
                   "align": "center", "vertical_align": "bottom", "indent_px": 12, "line_height": 1.3}
            if rich:
                doc = build_document(box, box["html"])
                cursor = QTextCursor(doc)
                cursor.setPosition(2)
                cursor.setPosition(9, QTextCursor.KeepAnchor)
                from PySide6.QtGui import QTextCharFormat
                fmt = QTextCharFormat()
                fmt.setFontPointSize(32)
                fmt.setForeground(QColor("red"))
                cursor.mergeCharFormat(fmt)
                box.update(html=doc.toHtml(), rich_text_version=1)
            self.edit.beginEditing(box)
            expected = NativeRenderer({"canvas_size": {"w": 400, "h": 350}, "boxes": [box]}).render_to_pixmap().toImage()
            actual = QImage(expected.size(), QImage.Format_ARGB32)
            actual.setDotsPerMeterX(3780)
            actual.setDotsPerMeterY(3780)
            actual.fill(Qt.white)
            painter = QPainter(actual)
            painter.translate(box["x"]+box["w"]/2, box["y"]+box["h"]/2)
            painter.rotate(box["rotation"])
            painter.translate(-box["w"]/2, -box["h"]/2)
            painter.setClipRect(0, -10000, box["w"], 20000)
            painter.translate(0, self.edit.contentTop)
            self.edit.paint(painter)
            painter.end()
            self.assertEqual(actual.convertToFormat(expected.format()), expected)


if __name__ == "__main__":
    unittest.main()
