import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication
from core.object_style import outline_margin
from core.text_layout import build_document
from features.editor_qml.bridge import EditorBridge
from features.editor_qml.canvas_text_editor import CanvasTextEditor
from features.generator.renderer import NativeRenderer

APP = QApplication.instance() or QApplication([])


class ShapesOutlineTest(unittest.TestCase):
    def setUp(self):
        self.bridge = EditorBridge()
        self.errors = []
        self.bridge.error.connect(self.errors.append)
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.bridge.shutdown()
        self.temp.cleanup()

    def test_shape_lifecycle_and_portable_save_without_assets(self):
        self.bridge.addItem("shape")
        key = self.bridge._selected
        self.bridge.setValue("fill_color", "#000000")
        self.bridge.setValue("outline_enabled", True)
        self.bridge.setValue("outline_color", "#ffffff")
        self.bridge.setValue("outline_width", 5)
        self.bridge.setValue("shape_type", "square")
        self.bridge.setValue("w", 150)
        self.assertEqual(self.bridge.state["selected"]["h"], 150)
        self.bridge.setValue("locked", True)
        self.bridge.setValue("fill_color", "#ff0000")
        self.assertEqual(self.bridge.state["selected"]["fill_color"], "#000000")
        self.bridge.setValue("locked", False)
        self.bridge.duplicateSelected()
        self.assertNotEqual(self.bridge._selected, key)
        self.bridge.deleteSelected()
        self.bridge.undo()
        path = Path(self.temp.name) / "template_v3.json"
        self.assertTrue(self.bridge.save_to(path), self.errors)
        saved = json.loads(path.read_text())
        self.assertEqual(len(saved["shapes"]), 2)
        self.assertEqual(saved["images"], [])
        self.assertFalse((path.parent / "assets").exists())
        self.assertTrue(self.bridge.load(str(path)))
        self.bridge.select(key)
        self.assertEqual(self.bridge.state["selected"]["outline_width"], 5)
        self.assertEqual(self.bridge.state["selected"]["shape_type"], "square")

    def test_shapes_draw_fill_outline_and_geometry_with_cache(self):
        self.bridge.addItem("shape")
        self.bridge.setValue("fill_color", "#ff0000")
        self.bridge.setValue("outline_enabled", True)
        self.bridge.setValue("outline_width", 6)
        for kind in ("rectangle", "square", "ellipse", "circle"):
            self.bridge.setValue("shape_type", kind)
            renderer = NativeRenderer(self.bridge.render_data())
            image = renderer.render_to_qimage({}, {})
            self.assertEqual(image.pixelColor(150, 110), QColor("red"))
            self.assertEqual(image.pixelColor(50, 100 if kind == "rectangle" else 150), QColor("black"))
            renderer.pre_render_static_base()
            self.assertEqual(image, renderer.render_to_qimage({}, {}))
        self.bridge.setValue("opacity", 0.5)
        self.bridge.setValue("rotation", 20)
        renderer = NativeRenderer(self.bridge.render_data())
        image = renderer.render_to_qimage({}, {})
        self.assertGreater(image.pixelColor(150, 150).green(), 100)
        self.bridge.setValue("visible", False)
        image = NativeRenderer(self.bridge.render_data()).render_to_qimage({}, {})
        self.assertEqual(image.pixelColor(150, 150), QColor("white"))

    def test_mixed_order_and_shape_links_survive_cached_rendering(self):
        self.bridge.addItem("shape")
        shape = self.bridge._selected
        self.bridge.setValue("fill_color", "#ff0000")
        self.bridge.setValue("has_link", True)
        link_key = self.bridge.state["selected"]["link_key"]
        self.bridge.addItem("text")
        text = self.bridge._selected
        self.bridge.setValue("html", "<p>MMMM</p>")
        first = NativeRenderer(self.bridge.render_data()).render_to_qimage({}, {})
        self.bridge.moveLayer(shape, text)
        renderer = NativeRenderer(self.bridge.render_data())
        links = []
        values = {link_key: "example.com"}
        second = renderer.render_to_qimage(values, values, links)
        self.assertNotEqual(first, second)
        self.assertEqual(second.pixelColor(60, 60), QColor("red"))
        renderer.pre_render_static_base()
        cached_links = []
        self.assertEqual(second, renderer.render_to_qimage(values, values, cached_links))
        self.assertEqual(links, cached_links)
        self.assertEqual(links[0]["url"], "https://example.com")

    def test_contour_restricted_and_invalid_widths_rejected(self):
        for kind in ("image", "signature"):
            self.bridge.insert_item(kind, {"path": "missing.png", "width": 20, "height": 20})
            self.bridge.setValue("outline_enabled", True)
            self.assertNotIn("outline_enabled", self.bridge.current()[1])
        self.bridge.addItem("shape")
        for value in (0, -1, "nan", "inf", "bad", 101):
            self.bridge.setValue("outline_width", value)
        self.assertEqual(self.bridge.state["selected"]["outline_width"], 1)

    def test_text_contour_surrounds_glyphs_and_matches_native_paint(self):
        self.bridge.addItem("text")
        self.bridge.setValue("html", "<p>AB <i>Cd</i></p>")
        self.bridge.setValue("font_size", 46)
        self.bridge.setValue("font_color", "#0000ff")
        self.bridge.setValue("outline_enabled", True)
        self.bridge.setValue("outline_color", "#ff0000")
        self.bridge.setValue("outline_width", 4)
        self.bridge.setValue("rotation", 11)
        box = self.bridge.current()[1]
        renderer = NativeRenderer(self.bridge.render_data())
        expected = renderer.render_to_qimage({}, {})
        colors = {expected.pixelColor(x, y).name() for x in range(40, 250) for y in range(35, 140)}
        self.assertIn("#ff0000", colors)
        self.assertIn("#0000ff", colors)
        # A caixa continua invisível, inclusive junto ao limite inferior.
        self.assertEqual(expected.pixelColor(250, 140), QColor("white"))
        native = CanvasTextEditor()
        native.beginEditing(box)
        actual = QImage(expected.size(), QImage.Format_ARGB32)
        actual.setDotsPerMeterX(3780)
        actual.setDotsPerMeterY(3780)
        actual.fill(Qt.white)
        p = QPainter(actual)
        p.translate(box["x"]+box["w"]/2, box["y"]+box["h"]/2)
        p.rotate(box["rotation"])
        p.translate(-box["w"]/2, -box["h"]/2)
        margin = outline_margin(box)
        p.setClipRect(QRectF(-margin, -10000, box["w"]+2*margin, 20000))
        p.translate(native.contentLeft, native.contentTop)
        native.paint(p)
        p.end()
        self.assertEqual(actual, expected)
        self.bridge.attachTextEditor(native)
        self.bridge.startTextSession(self.bridge._selected)
        native.insertText("!")
        self.bridge.finishTextSession()
        doc = build_document(self.bridge.current()[1], native.text)
        self.assertEqual(doc.begin().begin().fragment().charFormat().textOutline().widthF(), 4)
        self.bridge.setValue("outline_enabled", False)
        self.assertNotEqual(NativeRenderer(self.bridge.render_data()).render_to_qimage({}, {}), expected)
        native.deleteLater()


if __name__ == "__main__":
    unittest.main()
