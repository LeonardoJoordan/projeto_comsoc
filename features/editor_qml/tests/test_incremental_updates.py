import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor
from features.editor_qml.bridge import EditorBridge

APP = QApplication.instance() or QApplication([])


class IncrementalUpdatesTest(unittest.TestCase):
    def setUp(self):
        self.bridge = EditorBridge()
        for _ in range(20):
            self.bridge.addItem('text')
        self.key = self.bridge._selected
        self.bridge._data['boxes'][-1]['rich_text_version'] = 1
        self.bridge.notify()
        self.bridge.attachCanvas()
        self.bridge.textFormat

    def tearDown(self):
        self.bridge.shutdown()

    def test_geometry_selection_guides_skip_layout_fonts_and_page_preparation(self):
        model = self.bridge.canvasLayers
        other = model.objects[model.keys[0]]
        picture = other.picture
        with (patch('features.editor_qml.bridge.QTextDocument', side_effect=AssertionError('Reanálise HTML')),
             patch('features.editor_qml.bridge.build_document', side_effect=AssertionError('Layout na seleção')),
             patch('features.editor_qml.bridge.missing_template_fonts', side_effect=AssertionError('Varredura de fontes')),
             patch.object(self.bridge, 'render_data', side_effect=AssertionError('Preparação de página')),
             patch.object(model.cache, 'picture', wraps=model.cache.picture) as paint,
             patch.object(self.bridge, 'item_view', wraps=self.bridge.item_view) as views):
            self.bridge.select(self.key)
            self.bridge.textFormat
            self.bridge.moveSelected(150, 170)
            self.assertEqual(self.bridge.textFormat['x'], 150)
            self.assertEqual(views.call_count, 1)
            self.bridge.addGuide(True)
            self.bridge.moveGuide(0, 100)
            self.assertEqual(views.call_count, 1)
            self.assertEqual(paint.call_count, 0)
        self.assertIs(other.picture, picture)

    def test_qml_state_does_not_repeat_document_lists_or_html(self):
        state = self.bridge.uiState
        self.assertEqual(state['layerCount'], 20)
        self.assertNotIn('layers', state)
        self.assertNotIn('paintLayers', state)
        self.assertNotIn('html', state['selected'])
        self.assertNotIn('html', self.bridge.uiTextFormat)
        self.assertNotIn('html', self.bridge.canvasLayers.objects[self.key].uiView)
        self.assertEqual(len(self.bridge.state['layers']), 20)
        self.assertIn('html', self.bridge.state['selected'])

    def test_text_edit_updates_one_view_and_one_picture_and_font_warning(self):
        model = self.bridge.canvasLayers
        count = model.cache.recordings
        untouched = model.objects[model.keys[0]].picture
        with (patch.object(self.bridge, 'item_view', wraps=self.bridge.item_view) as views,
             patch.object(model.cache, 'picture', wraps=model.cache.picture) as paint):
            self.bridge.setValue('html', '<p><span style="font-family: MissingComsoc5678;">Novo</span></p>')
            self.assertEqual(views.call_count, 1)
            self.assertEqual(paint.call_count, 1)
        self.assertIn('MissingComsoc5678', self.bridge.state['missingFonts'])
        self.assertEqual(model.cache.recordings, count+1)
        self.assertIs(model.objects[model.keys[0]].picture, untouched)
        self.bridge.undo()
        self.assertNotIn('MissingComsoc5678', self.bridge.state['missingFonts'])

    def test_save_as_and_reload_refresh_asset_paths_and_pixels(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            asset = base/'source.png'
            image = QImage(20, 20, QImage.Format_ARGB32)
            image.fill(QColor('red')); image.save(str(asset))
            self.bridge.insert_item('image', dict(path=str(asset), width=20, height=20))
            key = self.bridge._selected
            path = base/'copy'/'template_v3.json'
            self.assertTrue(self.bridge.save_to(path))
            model = self.bridge.canvasLayers
            resolved = Path(model.items[key][1]['path'])
            self.assertTrue(resolved.is_relative_to(path.parent))
            self.assertTrue(resolved.is_file())
            before = model.objects[key].picture
            image.fill(QColor('blue')); image.save(str(resolved))
            stamp = resolved.stat()
            os.utime(resolved, ns=(stamp.st_atime_ns, stamp.st_mtime_ns+1000000))
            self.assertTrue(self.bridge.load(str(path)))
            self.assertIsNot(model.objects[key].picture, before)
            self.assertEqual(model.cache._renderer._image_cache[str(resolved)].pixelColor(0, 0), QColor('blue'))
            self.bridge.select(key)
            before = model.objects[key].picture
            image.fill(QColor('green')); image.save(str(resolved))
            self.assertTrue(self.bridge.replace_asset(resolved))
            self.assertIsNot(model.objects[key].picture, before)
            self.assertEqual(model.cache._renderer._image_cache[str(resolved)].pixelColor(0, 0), QColor('green'))


if __name__ == '__main__':
    unittest.main()
