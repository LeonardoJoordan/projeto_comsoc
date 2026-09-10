import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import Qt
from core.document_layers import upgrade_layers, layer_entries
from features.editor_qml.layer_paint_cache import LayerPaintCache
from features.generator.renderer import NativeRenderer

APP = QApplication.instance() or QApplication([])


class LayerPaintCacheTest(unittest.TestCase):
    def test_composition_matches_renderer_and_move_reuses_picture(self):
        data = upgrade_layers({"canvas_size": {"w": 500, "h": 400},
            "shapes": [{"x": 40, "y": 60, "width": 220, "height": 150,
                        "fill_color": "#ff6633", "outline_enabled": True,
                        "outline_width": 5, "rotation": 12, "opacity": .7}],
            "boxes": [{"x": 100, "y": 110, "w": 280, "h": 130,
                       "html": "<p><b>{Nome}</b> exemplo</p>", "font_size": 22,
                       "font_family": "DejaVu Sans", "rotation": -8,
                       "outline_enabled": True, "outline_width": 2,
                       "outline_color": "#0055aa"}]})
        cache = LayerPaintCache()

        def compose():
            image = QImage(500, 400, QImage.Format_ARGB32)
            image.setDotsPerMeterX(3780)
            image.setDotsPerMeterY(3780)
            image.fill(Qt.white)
            painter = QPainter(image)
            try:
                for key, kind, item in layer_entries(data):
                    if item.get("visible", True):
                        painter.save()
                        painter.translate(item["x"], item["y"])
                        painter.drawPicture(0, 0, cache.picture(key, kind, item, {"Nome": "Ana"}))
                        painter.restore()
            finally:
                painter.end()
            return image

        self.assertEqual(compose(), NativeRenderer(data).render_to_qimage({}, {"Nome": "Ana"}))
        count = cache.recordings
        for item in data["boxes"] + data["shapes"]:
            item.update(x=item["x"]+15, y=item["y"]-10, locked=True, custom_name="Renomeado")
        self.assertEqual(compose(), NativeRenderer(data).render_to_qimage({}, {"Nome": "Ana"}))
        self.assertEqual(cache.recordings, count)
        data["boxes"][0]["font_size"] = 30
        self.assertEqual(compose(), NativeRenderer(data).render_to_qimage({}, {"Nome": "Ana"}))
        self.assertEqual(cache.recordings, count+1)

    def test_asset_replacement_and_removal_invalidate_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "image.png"
            image = QImage(20, 20, QImage.Format_ARGB32)
            image.fill(QColor("red"))
            image.save(str(path))
            cache = LayerPaintCache()
            item = dict(path=str(path), width=20, height=20)
            first = cache.picture("image", "image", item)
            self.assertIs(cache.picture("image", "image", item), first)
            image.fill(QColor("blue"))
            image.save(str(path))
            stat = path.stat()
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000000))
            self.assertIsNot(cache.picture("image", "image", item), first)
            self.assertEqual(cache._renderer._image_cache[str(path)].pixelColor(0, 0), QColor("blue"))
            for kind, group in (("image", "images"), ("signature", "signatures")):
                with self.subTest(kind=kind):
                    placed = dict(item, object_id=kind, x=25, y=30, rotation=20, opacity=.5)
                    data = {"canvas_size": {"w": 80, "h": 80}, "layer_order": [kind], group: [placed]}
                    actual = QImage(80, 80, QImage.Format_ARGB32)
                    actual.setDotsPerMeterX(3780)
                    actual.setDotsPerMeterY(3780)
                    actual.fill(Qt.white)
                    painter = QPainter(actual)
                    painter.translate(25, 30)
                    painter.drawPicture(0, 0, cache.picture(kind, kind, placed))
                    painter.end()
                    self.assertEqual(actual, NativeRenderer(data).render_to_qimage({}, {}))
            cache.retain([])
            self.assertFalse(cache._entries)
            self.assertFalse(cache._renderer._image_cache)


if __name__ == "__main__":
    unittest.main()
