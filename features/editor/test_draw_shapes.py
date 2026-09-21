import unittest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication, QDoubleSpinBox, QLabel, QLineEdit, QPushButton
from PySide6.QtTest import QTest
from .editor_window import EditorWindow
from .canvas_items import RectangleItem


class DrawShapesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.w = EditorWindow()
        self.w.show()
        self.app.processEvents()

    def tearDown(self):
        self.w.shape_drawing.cancel()
        self.w._last_saved_state = self.w.get_current_scene_state()
        self.w.close()

    def draw(self, kind, end, modifiers=Qt.NoModifier):
        self.w.shape_drawing.activate(kind)
        viewport = self.w.view.viewport()
        QTest.mousePress(viewport, Qt.LeftButton, pos=QPoint(200, 250))
        QTest.mouseMove(viewport, end)
        QTest.mouseRelease(viewport, Qt.LeftButton, modifiers, end)
        self.app.processEvents()
        return self.w.scene.selectedItems()[0]

    def test_proportions_and_cancel(self):
        rectangle = self.draw('rectangle', QPoint(350, 330))
        self.assertEqual(rectangle.fill_color, '#d9d9d9')
        self.assertNotAlmostEqual(rectangle.rect().width(), rectangle.rect().height())
        circle = self.draw('ellipse', QPoint(350, 330), Qt.ShiftModifier)
        self.assertAlmostEqual(circle.rect().width(), circle.rect().height())
        before = self.w.get_current_scene_state()
        self.w.shape_drawing.activate('line')
        QTest.mousePress(self.w.view.viewport(), Qt.LeftButton, pos=QPoint(200, 200))
        QTest.keyClick(self.w.view.viewport(), Qt.Key_Escape)
        self.assertEqual(before, self.w.get_current_scene_state())

    def test_line_angle_history_and_persistence(self):
        line = self.draw('line', QPoint(350, 100))
        self.assertAlmostEqual(line.rotation(), -45)
        angle = self.w.findChild(QDoubleSpinBox, 'lineAngle')
        self.assertEqual(angle.value(), 45)
        self.assertFalse(self.w.caixa_texto_panel.spin_h.isEnabled())
        saved = self.w.get_current_scene_state()
        self.w.undo()
        self.assertFalse(any(getattr(i, 'shape_type', '') == 'line' for i in self.w.scene.items()))
        self.w.redo()
        lines = [i for i in self.w.scene.items() if getattr(i, 'shape_type', '') == 'line']
        self.assertEqual(len(lines), 1)
        self.assertAlmostEqual(lines[0].rotation(), -45)
        self.w.apply_scene_state(saved)
        lines = [i for i in self.w.scene.items() if getattr(i, 'shape_type', '') == 'line']
        self.assertAlmostEqual(lines[0].rotation(), -45)
        snapped = self.draw('line', QPoint(360, 210), Qt.ShiftModifier)
        self.assertAlmostEqual(snapped.rotation(), 0)

    def test_line_renderer(self):
        from features.generator.renderer import NativeRenderer
        self.draw('line', QPoint(350, 100))
        state = self.w.get_current_scene_state()
        state['shapes'] = [s for s in state['shapes'] if s['shape_type'] == 'line']
        image = NativeRenderer(state).render_preview_image(transparent=True, max_side=400)
        opaque = sum(image.pixelColor(x, y).alpha() > 0 for y in range(image.height()) for x in range(image.width()))
        self.assertGreater(opaque, 10)
        self.assertLess(opaque, image.width()*image.height()/10)

    def test_shift_resizes_proportionally(self):
        from PySide6.QtWidgets import QGraphicsSceneMouseEvent
        from PySide6.QtCore import QEvent, QPointF
        from .canvas_items import ResizeHandle
        item = self.draw('rectangle', QPoint(350, 330))
        handle = next(h for h in item.childItems() if isinstance(h, ResizeHandle) and h.name == 'bottom_right')
        ratio = item.rect().width()/item.rect().height()
        press = QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMousePress)
        press.setButton(Qt.LeftButton)
        handle.mousePressEvent(press)
        anchor = QPointF(handle._anchor_scene)
        move = QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseMove)
        move.setModifiers(Qt.ShiftModifier)
        move.setScenePos(anchor + QPointF(700, 200))
        handle.mouseMoveEvent(move)
        self.assertAlmostEqual(item.rect().width()/item.rect().height(), ratio)
        self.assertLess((item.mapToScene(QPointF(0,0))-anchor).manhattanLength(), 0.001)
        self.assertFalse(item.keep_proportion)
        move.setModifiers(Qt.NoModifier)
        move.setScenePos(anchor + QPointF(800, 200))
        handle.mouseMoveEvent(move)
        self.assertNotAlmostEqual(item.rect().width()/item.rect().height(), ratio)
        release = QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseRelease)
        release.setButton(Qt.LeftButton)
        handle.mouseReleaseEvent(release)

    def test_independent_and_synchronized_corner_radii(self):
        rectangle = self.draw('rectangle', QPoint(350, 330))
        top_left = self.w.findChild(QDoubleSpinBox, 'shapeCornerRadius_top_left')
        top_right = self.w.findChild(QDoubleSpinBox, 'shapeCornerRadius_top_right')
        bottom_right = self.w.findChild(QDoubleSpinBox, 'shapeCornerRadius_bottom_right')
        top_left_icon = self.w.findChild(QLabel, 'cornerRadiusIcon_top_left')
        top_right_icon = self.w.findChild(QLabel, 'cornerRadiusIcon_top_right')
        sync = self.w.findChild(QPushButton, 'syncCornerRadii')
        self.app.processEvents()
        top_box = top_right.parentWidget()
        bottom_box = bottom_right.parentWidget()
        desired_center = (
            top_box.mapTo(self.w, QPoint(0, 0)).y()
            + bottom_box.mapTo(self.w, QPoint(0, bottom_box.height())).y()
        ) / 2
        actual_center = sync.mapTo(self.w, QPoint(0, sync.height() // 2)).y()
        self.assertAlmostEqual(actual_center, desired_center, delta=1)
        left_box = top_left.parentWidget()
        left_x = left_box.mapTo(self.w, QPoint(0, 0)).x()
        left_icon_x = top_left_icon.mapTo(self.w, QPoint(0, 0)).x()
        sync_x = sync.mapTo(self.w, QPoint(sync.width() // 2, 0)).x()
        right_icon_x = top_right_icon.mapTo(self.w, QPoint(0, 0)).x()
        right_box_x = top_box.mapTo(self.w, QPoint(0, 0)).x()
        self.assertLess(left_x, left_icon_x)
        self.assertLess(left_icon_x, sync_x)
        self.assertLess(sync_x, right_icon_x)
        self.assertLess(right_icon_x, right_box_x)
        outer_center = (left_x + right_box_x + top_box.width()) / 2
        self.assertAlmostEqual(sync_x, outer_center, delta=1)
        self.assertTrue(sync.isChecked())
        top_left.setValue(4)
        top_left.editingFinished.emit()
        self.assertEqual(top_right.value(), 4)
        sync.click()
        top_right.setValue(8)
        top_right.editingFinished.emit()
        self.assertEqual(top_left.value(), 4)
        self.assertEqual(top_right.value(), 8)
        bottom_left = self.w.findChild(QDoubleSpinBox, 'shapeCornerRadius_bottom_left')
        sync.click()
        self.assertEqual(top_left.value(), 4)
        self.assertEqual(top_right.value(), 8)
        bottom_left.setValue(6)
        bottom_left.editingFinished.emit()
        self.assertTrue(all(spin.value() == 6 for spin in (
            top_left, top_right, bottom_left, bottom_right,
        )))
        sync.click()
        state = self.w.get_current_scene_state()
        self.w.apply_scene_state(state)
        restored = next(i for i in self.w.scene.items()
                        if getattr(i, 'shape_type', '') == 'rectangle'
                        and not getattr(i, 'is_document_background', False))
        self.assertFalse(restored.corner_radii_linked)
        self.assertAlmostEqual(restored.corner_radii['top_left'], rectangle.corner_radii['top_left'])
        self.assertAlmostEqual(restored.corner_radii['top_right'], rectangle.corner_radii['top_right'])

    def test_shape_link_is_available_and_persisted(self):
        rectangle = self.draw('rectangle', QPoint(350, 330))
        self.assertFalse(self.w.caixa_texto_panel.btn_restore.isVisible())
        link = self.w.caixa_texto_panel.chk_link
        self.assertTrue(link.isEnabled())
        link.click()
        link_field = self.w.findChild(QLineEdit, 'linkField')
        self.assertTrue(link_field.isVisible())
        self.assertEqual(link_field.text(), 'Link')
        self.assertTrue(rectangle.has_link)
        self.assertEqual(rectangle.link_key, 'Link')
        link_field.setText('Site institucional')
        link_field.editingFinished.emit()
        state = self.w.get_current_scene_state()
        saved_shape = next(shape for shape in state['shapes']
                           if not shape.get('is_document_background'))
        self.assertTrue(saved_shape['has_link'])
        self.assertEqual(saved_shape['link_key'], 'Site institucional')
        self.w.apply_scene_state(state)
        restored = next(i for i in self.w.scene.items()
                        if getattr(i, 'shape_type', '') == 'rectangle'
                        and not getattr(i, 'is_document_background', False))
        self.assertTrue(restored.has_link)
        self.assertEqual(restored.link_key, 'Site institucional')
        self.assertIn('Site institucional', self.w.get_all_model_placeholders())

    def test_shape_property_sections_keep_order_and_disable_incompatible_options(self):
        self.draw('rectangle', QPoint(350, 330))
        self.app.processEvents()

        expected_headings = {
            'PREENCHIMENTO', 'ARREDONDAMENTO DE BORDAS', 'CONTORNO',
            'MÁSCARA', 'LINK', 'IMAGEM VARIÁVEL',
        }
        headings = [
            label for label in self.w.findChildren(QLabel, 'propertySectionHeading')
            if label.isVisible() and label.text() in expected_headings
        ]
        headings.sort(key=lambda label: label.mapTo(self.w, QPoint(0, 0)).y())
        self.assertEqual(
            [label.text() for label in headings],
            ['PREENCHIMENTO', 'ARREDONDAMENTO DE BORDAS', 'CONTORNO',
             'MÁSCARA', 'LINK', 'IMAGEM VARIÁVEL'],
        )

        dynamic = self.w.findChild(QPushButton, 'dynamicImageEnabled')
        mask = self.w.findChild(QPushButton, 'maskEnabled')
        outline = self.w.findChild(QPushButton, 'shapeOutlineEnabled')
        link = self.w.caixa_texto_panel.chk_link
        for button in (outline, mask, link, dynamic):
            self.assertEqual(button.height(), 22)
            # Native font/style metrics may require more than 65% to fit text.
            wrapper_width = button.parentWidget().width()
            expected_width = max(wrapper_width * 0.65, button.minimumSizeHint().width())
            self.assertAlmostEqual(button.width(), expected_width, delta=wrapper_width * 0.03)
            self.assertAlmostEqual(
                button.x() + button.width() / 2, wrapper_width / 2, delta=1
            )
        self.assertTrue(mask.isVisible())
        self.assertFalse(mask.isEnabled())
        dynamic.click()
        self.app.processEvents()
        self.assertTrue(mask.isVisible())
        self.assertFalse(mask.isEnabled())

    def test_outline_join_uses_centered_exclusive_icon_buttons(self):
        rectangle = self.draw('rectangle', QPoint(350, 330))
        outline = self.w.findChild(QPushButton, 'shapeOutlineEnabled')
        straight = self.w.findChild(QPushButton, 'outlineJoinStraight')
        curved = self.w.findChild(QPushButton, 'outlineJoinRound')
        outline.click()
        self.app.processEvents()

        self.assertTrue(straight.isChecked())
        self.assertFalse(curved.isChecked())
        self.assertEqual((straight.width(), straight.height()), (30, 30))
        self.assertEqual((curved.width(), curved.height()), (30, 30))
        self.assertEqual(curved.x() - (straight.x() + straight.width()), 6)
        group_center = (straight.x() + curved.x() + curved.width()) / 2
        self.assertAlmostEqual(group_center, straight.parentWidget().width() / 2, delta=1)

        curved.click()
        self.assertFalse(straight.isChecked())
        self.assertTrue(curved.isChecked())
        self.assertEqual(rectangle.outline_join, 'round')
