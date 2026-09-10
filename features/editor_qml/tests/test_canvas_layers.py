import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import Qt
from features.editor_qml.bridge import EditorBridge
from features.editor_qml.canvas_layers import CanvasLayer
from features.editor_qml.canvas_text_editor import CanvasTextEditor
from features.generator.renderer import NativeRenderer

APP = QApplication.instance() or QApplication([])
ROOT = Path(__file__).resolve().parents[3]


class CanvasLayersTest(unittest.TestCase):
    def setUp(self):
        self.bridge = EditorBridge()

    def tearDown(self):
        self.bridge.shutdown()

    def compose(self):
        model = self.bridge.canvasLayers
        size = self.bridge.documentSize
        result = QImage(size['w'], size['h'], QImage.Format_ARGB32)
        result.setDotsPerMeterX(3780)
        result.setDotsPerMeterY(3780)
        result.fill(Qt.white)
        painter = QPainter(result)
        try:
            for key in model.keys:
                source = model.objects[key]
                if not source.view['visible']:
                    continue
                bounds = source.bounds
                visual = CanvasLayer()
                visual.source = source
                visual.setWidth(bounds.width())
                visual.setHeight(bounds.height())
                # A textura de cada item tem limites próprios: exercer o recorte real.
                tile = QImage(int(bounds.width()), int(bounds.height()), QImage.Format_ARGB32_Premultiplied)
                tile.setDotsPerMeterX(3780)
                tile.setDotsPerMeterY(3780)
                tile.fill(Qt.transparent)
                local = QPainter(tile)
                visual.paint(local)
                local.end()
                painter.drawImage(source.view['x']+bounds.x(), source.view['y']+bounds.y(), tile)
                visual.source = None
        finally:
            painter.end()
        return result

    def test_real_models_composed_with_individual_bounds(self):
        for name in ('teste', 'teste2', 'teste3'):
            with self.subTest(name=name):
                self.assertTrue(self.bridge.load(str(ROOT/'models'/name/'template_v3.json')))
                self.bridge.attachCanvas()
                actual = self.compose()
                expected = NativeRenderer(self.bridge.render_data()).render_preview_image()
                # Compor texturas transparentes adiciona arredondamento de alpha.
                # Limite estrito por canal, sem tolerar deslocamento ou cortes de tinta.
                self.assertEqual(actual.size(), expected.size())
                differences = [abs(a-b) for a, b in zip(bytes(actual.constBits()), bytes(expected.constBits())) if a != b]
                self.assertLessEqual(max(differences, default=0), 2)

    def test_move_reorder_and_edit_keep_objects_without_full_preview(self):
        self.bridge.addItem('text')
        first = self.bridge._selected
        self.bridge.addItem('shape')
        second = self.bridge._selected
        self.bridge.attachCanvas()
        model = self.bridge.canvasLayers
        objects = dict(model.objects)
        recordings = model.cache.recordings
        self.bridge.moveSelected(100, 200)
        self.bridge.moveLayer(first, second)
        self.assertEqual(model.objects, objects)
        self.assertEqual(model.keys, self.bridge._data['layer_order'])
        self.assertEqual(model.cache.recordings, recordings)
        self.assertFalse(self.bridge._render_timer.isActive())
        edit = CanvasTextEditor()
        self.bridge.attachTextEditor(edit)
        with patch.object(self.bridge, 'render', side_effect=AssertionError('Prévia completa durante edição')):
            self.bridge.startTextSession(first)
            edit.insertText('Teste')
            self.bridge.finishTextSession()
        self.assertEqual(model.objects, objects)
        self.assertEqual(model.cache.recordings, recordings+1)

    def test_rotated_outline_and_text_overflow_are_not_clipped(self):
        self.bridge.addItem('text')
        self.bridge.setValue('html', '<p>Texto longo<br>segunda linha<br>terceira linha</p>')
        self.bridge.setValue('h', 20)
        self.bridge.setValue('font_size', 24)
        self.bridge.setValue('outline_enabled', True)
        self.bridge.setValue('outline_width', 8)
        self.bridge.setValue('rotation', 20)
        self.bridge.attachCanvas()
        self.assertEqual(self.compose(), NativeRenderer(self.bridge.render_data()).render_preview_image())


if __name__ == '__main__':
    unittest.main()
