import tempfile
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor
from PySide6.QtCore import Qt
from core.document_layers import layer_entries
from .editor_window import EditorWindow
from .canvas_items import ImageItem, BackgroundItem, RectangleItem


class UnifiedLayersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_migration_order_and_white_base(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'background.png'
            image = QImage(40, 40, QImage.Format.Format_RGB32)
            image.fill(QColor('red'))
            image.save(str(path))
            w = EditorWindow()
            self.assertIsInstance(w.layer_list.item(w.layer_list.count()-1).data(Qt.ItemDataRole.UserRole), RectangleItem)
            w.add_new_box()
            state = w.get_current_scene_state()
            state.pop('shapes')
            state['background_path'] = str(path)
            state.pop('layer_order')
            state['bg_props'] = {'w': 40, 'h': 40, 'locked': False}
            w.apply_scene_state(state)
            objects = [i for i in w.scene.items() if isinstance(i, ImageItem) and not isinstance(i, (BackgroundItem, RectangleItem))]
            self.assertEqual(len(objects), 1)
            self.assertEqual(w.layer_list.count(), 3)
            # Move the image above the text through the actual list model.
            model = w.layer_list.model()
            from PySide6.QtCore import QModelIndex
            self.assertTrue(model.moveRow(QModelIndex(), 1, QModelIndex(), 0))
            saved = w.get_current_scene_state()
            self.assertIsNone(saved['background_path'])
            self.assertEqual([kind for _, kind, _ in layer_entries(saved)], ['shape', 'text', 'image'])
            w.apply_scene_state(saved)
            self.assertIsInstance(w.layer_list.item(0).data(Qt.ItemDataRole.UserRole), ImageItem)
            obj = w.layer_list.item(0).data(Qt.ItemDataRole.UserRole)
            w.scene.removeItem(obj)
            w.refresh_layer_list()
            self.assertEqual(w.layer_list.count(), 2)
            w._last_saved_state = w.get_current_scene_state()
            w.close()

    def test_editable_background_roundtrip(self):
        w = EditorWindow()
        shape = next(i for i in w.scene.items() if isinstance(i, RectangleItem))
        self.assertEqual(shape.rect().size(), w._get_document_rect().size())
        shape.fill_color = '#123456'
        shape.outline_enabled = True
        shape.outline_width = 8
        shape.outline_color = '#ff0000'
        shape.outline_position = 'inside'
        shape.setOpacity(0.4)
        shape.setVisible(False)
        w.save_snapshot()
        state = w.get_current_scene_state()
        self.assertEqual(state['images'], [])
        self.assertEqual(state['shapes'][0]['fill_color'], '#123456')
        w.apply_scene_state(state)
        restored = next(i for i in w.scene.items() if isinstance(i, RectangleItem))
        self.assertEqual(restored.fill_color, '#123456')
        self.assertEqual(restored.outline_width, 8)
        self.assertEqual(restored.outline_color, '#ff0000')
        self.assertEqual(restored.outline_position, 'inside')
        self.assertEqual(restored.opacity(), 0.4)
        self.assertFalse(restored.isVisible())
        w._last_saved_state = w.get_current_scene_state()
        w.close()

    def test_outline_positions(self):
        from PySide6.QtGui import QPainter
        from core.object_style import draw_shape
        expected = {'inside': (False, True), 'center': (True, True), 'outside': (True, False)}
        for position, (outside, inside) in expected.items():
            image = QImage(100, 100, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            draw_shape(painter, {'x': 20, 'y': 20, 'width': 60, 'height': 60,
                       'fill_color': '#ffffff', 'outline_enabled': True,
                       'outline_color': '#ff0000', 'outline_width': 10,
                       'outline_position': position})
            painter.end()
            self.assertEqual(image.pixelColor(17, 50) == QColor('#ff0000'), outside, position)
            self.assertEqual(image.pixelColor(22, 50) == QColor('#ff0000'), inside, position)

    def test_independent_alpha_and_corners(self):
        from PySide6.QtGui import QPainter
        from core.object_style import draw_shape
        for join, corner in [('round', 0), ('miter', 128)]:
            image = QImage(100, 100, QImage.Format.Format_ARGB32)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            draw_shape(painter, dict(x=20, y=20, width=60, height=60,
                       fill_color='#ffffff', fill_opacity=0.25,
                       outline_color='#ff0000', outline_opacity=0.5,
                       outline_enabled=True, outline_width=10,
                       outline_position='outside', outline_join=join))
            painter.end()
            self.assertAlmostEqual(image.pixelColor(50, 50).alpha(), 64, delta=1)
            self.assertAlmostEqual(image.pixelColor(15, 50).alpha(), 128, delta=1)
            self.assertAlmostEqual(image.pixelColor(11, 11).alpha(), corner, delta=1)

    def test_background_properties_from_layer_click(self):
        from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox
        from PySide6.QtTest import QTest
        from .canvas_items import px_to_mm
        w = EditorWindow()
        w.show()
        self.app.processEvents()
        row = w.layer_list.item(w.layer_list.count() - 1)
        QTest.mouseClick(w.layer_list.viewport(), Qt.MouseButton.LeftButton,
                         pos=w.layer_list.visualItemRect(row).center())
        self.app.processEvents()
        toggle = w.findChild(QCheckBox, 'shapeOutlineEnabled')
        position = w.findChild(QComboBox, 'shapeOutlinePosition')
        width = w.findChild(QDoubleSpinBox, 'shapeOutlineWidth')
        self.assertTrue(toggle.isVisible())
        self.assertTrue(toggle.isEnabled())
        self.assertFalse(position.isVisible())
        self.assertAlmostEqual(px_to_mm(row.data(Qt.ItemDataRole.UserRole).outline_width), 0.2)
        self.assertAlmostEqual(width.value(), 0.2)
        toggle.click()
        self.assertTrue(position.isVisible())
        self.assertTrue(position.isEnabled())
        self.assertEqual(position.currentData(), 'inside')
        self.assertFalse(position.model().item(1).isEnabled())
        self.assertFalse(position.model().item(2).isEnabled())
        self.assertTrue(row.data(Qt.ItemDataRole.UserRole).outline_enabled)
        self.assertFalse(w.caixa_texto_panel.spin_w.isEnabled())
        w._last_saved_state = w.get_current_scene_state()
        w.close()

    def test_background_constraints_and_transparency(self):
        from features.generator.renderer import NativeRenderer
        w = EditorWindow()
        bg = next(i for i in w.scene.items() if getattr(i, 'is_document_background', False))
        self.assertEqual(w.get_current_scene_state(), w._last_saved_state)
        bg.setPos(20, 30)
        bg.setRotation(45)
        bg.resize_custom(10, 10)
        self.assertEqual(bg.pos().x(), 0)
        self.assertEqual(bg.rotation(), 0)
        self.assertEqual(bg.rect().size(), w._get_document_rect().size())
        bg.setSelected(True)
        w.delete_selected_items()
        w.duplicate_selected()
        self.assertEqual(sum(getattr(i, 'is_document_background', False) for i in w.scene.items()), 1)
        w.spin_phys_w.setValue(180)
        self.assertEqual(bg.rect().size(), w._get_document_rect().size())
        bg.setVisible(False)
        image = NativeRenderer(w.get_current_scene_state()).render_preview_image(transparent=True)
        self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
        bg.setVisible(True)
        bg.setOpacity(0.5)
        image = NativeRenderer(w.get_current_scene_state()).render_preview_image(transparent=True)
        self.assertTrue(125 <= image.pixelColor(10, 10).alpha() <= 128)
        w._last_saved_state = w.get_current_scene_state()
        w.close()
