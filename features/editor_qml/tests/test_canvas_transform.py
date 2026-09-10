from copy import deepcopy
import math
import os
import unittest
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from features.editor_qml.bridge import EditorBridge

APP = QApplication.instance() or QApplication([])


class CanvasTransformTest(unittest.TestCase):
    def setUp(self):
        self.bridge = EditorBridge()
        self.bridge.addItem('shape')
        self.other = self.bridge._selected
        self.bridge.addItem('text')
        self.key = self.bridge._selected
        self.bridge.setValue('keep_proportion', False)
        self.bridge.attachCanvas()
        self.model = self.bridge.canvasLayers

    def tearDown(self):
        self.bridge.shutdown()

    def test_move_is_transient_reuses_paint_and_commits_one_history_entry(self):
        original = deepcopy(self.bridge._data)
        view = dict(self.model.objects[self.key].view)
        recordings = self.model.cache.recordings
        index = self.bridge.history._current_index
        self.assertTrue(self.bridge.beginTransform(self.key, False))
        for i in range(1, 100):
            self.bridge.updateTransform(i, i*2)
        self.assertEqual(self.bridge._data, original)
        self.assertEqual(self.bridge.history._current_index, index)
        self.assertEqual(self.model.cache.recordings, recordings)
        self.assertEqual(self.model.objects[self.key].view['x'], view['x']+99)
        self.assertFalse(self.bridge._render_timer.isActive())
        self.bridge.finishTransform()
        self.assertEqual(self.bridge.history._current_index, index+1)
        final = deepcopy(self.bridge._data)
        self.bridge.undo()
        self.assertEqual(self.bridge._data, original)
        self.bridge.redo()
        self.assertEqual(self.bridge._data, final)

    def test_cancel_resize_restores_picture_document_history_and_redo(self):
        self.bridge.setValue('font_size', 30)
        self.bridge.undo()
        original = deepcopy(self.bridge._data)
        layer = self.model.objects[self.key]
        view, picture = dict(layer.view), layer.picture
        index = self.bridge.history._current_index
        other = self.model.objects[self.other].picture
        self.assertTrue(self.bridge.beginTransform(self.key, True))
        self.bridge.updateTransform(80, 35)
        self.assertIsNot(layer.picture, picture)
        self.assertIs(self.model.objects[self.other].picture, other)
        self.assertEqual(layer.view['w'], view['w']+80)
        self.assertEqual(self.bridge._data, original)
        self.bridge.cancelTransform()
        self.assertIs(layer.picture, picture)
        self.assertEqual(layer.view, view)
        self.assertEqual(self.bridge.history._current_index, index)
        self.assertTrue(self.bridge.history.can_redo())
        self.bridge.finishTransform()
        self.assertEqual(self.bridge._data, original)

    def test_rotated_resize_preserves_anchor_and_reflows_only_selected_text(self):
        self.bridge.setValue('rotation', 45)
        original = dict(self.model.objects[self.key].view)
        self.bridge.beginTransform(self.key, True)
        c = math.sqrt(.5)
        count = self.model.cache.recordings
        self.bridge.updateTransform(c*60-c*20, c*60+c*20)
        transient = dict(self.model.objects[self.key].view)
        self.assertEqual(transient['w'], original['w']+60)
        self.assertEqual(transient['h'], original['h']+20)
        def anchor(v):
            return (v['x']+v['w']/2-c*v['w']/2+c*v['h']/2,
                    v['y']+v['h']/2-c*v['w']/2-c*v['h']/2)
        for a, b in zip(anchor(original), anchor(transient)):
            self.assertAlmostEqual(a, b, delta=.01)
        self.assertEqual(self.model.cache.recordings, count+1)
        self.bridge.finishTransform()
        self.assertEqual(self.model.cache.recordings, count+1)
        self.assertEqual(self.bridge.state['selected']['w'], transient['w'])
        self.bridge.undo()
        self.assertEqual(self.model.objects[self.key].view, original)

    def test_lock_proportion_square_and_invalid_deltas(self):
        self.bridge.setValue('locked', True)
        self.assertFalse(self.bridge.beginTransform(self.key, False))
        self.bridge.select(self.other)
        self.bridge.setValue('shape_type', 'square')
        self.bridge.beginTransform(self.other, True)
        before = dict(self.model.objects[self.other].view)
        self.bridge.updateTransform(float('nan'), 1)
        self.assertEqual(self.model.objects[self.other].view, before)
        self.bridge.updateTransform(30, 100)
        view = self.model.objects[self.other].view
        self.assertEqual(view['w'], view['h'])
        self.bridge.cancelTransform()
        self.bridge.setValue('shape_type', 'rectangle')
        self.bridge.setValue('keep_proportion', True)
        self.bridge.beginTransform(self.other, True)
        self.bridge.updateTransform(-100000, -100000)
        view = self.model.objects[self.other].view
        self.assertGreaterEqual(view['w'], 1)
        self.assertGreaterEqual(view['h'], 1)

    def test_guide_gestures_commit_once_cancel_and_do_not_repaint_objects(self):
        self.bridge.addGuide(True)
        self.bridge.addGuide(False)
        for index in (0, 1):
            original = deepcopy(self.bridge._data)
            history = self.bridge.history._current_index
            records = self.model.cache.recordings
            self.assertTrue(self.bridge.beginGuideTransform(index))
            for position in range(100, 200):
                self.bridge.updateGuideTransform(position)
            self.assertEqual(self.bridge._data, original)
            self.assertEqual(self.bridge.guideGesture['position'], 199)
            self.assertEqual(self.model.cache.recordings, records)
            self.bridge.finishGuideTransform()
            self.assertEqual(self.bridge.history._current_index, history+1)
            self.assertEqual(self.bridge._data['guidelines'][index]['pos'], 199)
            self.bridge.undo()
            self.assertEqual(self.bridge._data, original)
            self.bridge.beginGuideTransform(index)
            self.bridge.updateGuideTransform(250)
            self.bridge.cancelTransform()
            self.bridge.finishGuideTransform()
            self.assertEqual(self.bridge._data, original)
            self.assertTrue(self.bridge.history.can_redo())

    def test_guides_respect_lock_visibility_selection_and_invalid_positions(self):
        self.bridge.addGuide(True)
        self.bridge.guideOption('guidelines_locked', True)
        self.assertFalse(self.bridge.beginGuideTransform(0))
        self.bridge.guideOption('guidelines_locked', False)
        self.bridge.guideOption('guidelines_visible', False)
        self.assertFalse(self.bridge.beginGuideTransform(0))
        self.bridge.guideOption('guidelines_visible', True)
        self.assertFalse(self.bridge.beginGuideTransform(100))
        self.bridge.beginGuideTransform(0)
        before = self.bridge.guideGesture
        self.bridge.updateGuideTransform(float('nan'))
        self.assertEqual(self.bridge.guideGesture, before)
        self.bridge.select(self.key)
        self.assertFalse(self.bridge.transforming)


if __name__ == '__main__':
    unittest.main()
