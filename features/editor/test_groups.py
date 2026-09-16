import unittest

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import QApplication, QGraphicsSceneMouseEvent, QPushButton
from PySide6.QtTest import QTest

from .canvas_items import DesignerBox, ImageItem, RectangleItem, ResizeHandle
from .editor_window import EditorWindow, LayerGroupBadge


class BasicGroupsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_window(self):
        window = EditorWindow()
        first = RectangleItem(80, 60, '#cccccc')
        first.layer_id = window._get_next_layer_id()
        first.custom_name = 'Forma 1'
        first.setPos(20, 30)
        window.scene.addItem(first)
        second = RectangleItem(50, 40, '#aaaaaa')
        second.layer_id = window._get_next_layer_id()
        second.custom_name = 'Forma 2'
        second.setPos(150, 90)
        window.scene.addItem(second)
        window.refresh_layer_list()
        window.save_snapshot()
        return window, first, second

    @staticmethod
    def close(window):
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()

    def test_group_selects_members_persists_and_ungroups_as_one_action(self):
        window, first, second = self.make_window()
        try:
            first.setSelected(True)
            second.setSelected(True)
            self.assertTrue(window.group_selected_items())
            self.assertEqual(first.group_id, 1)
            self.assertEqual(second.group_id, 1)

            window.scene.clearSelection()
            first.setSelected(True)
            self.app.processEvents()
            self.assertEqual(set(window.scene.selectedItems()), {first, second})

            state = window.get_current_scene_state()
            grouped_shapes = [entry for entry in state['shapes']
                              if not entry.get('is_document_background')]
            self.assertEqual({entry.get('group_id') for entry in grouped_shapes}, {1})
            window.apply_scene_state(state)
            restored = [item for item in window._groupable_items()
                        if getattr(item, 'group_id', None) == 1]
            self.assertEqual(len(restored), 2)
            restored[0].setSelected(True)
            self.app.processEvents()
            self.assertEqual(set(window.scene.selectedItems()), set(restored))
            self.assertTrue(window.ungroup_selected_items())
            self.assertTrue(all(getattr(item, 'group_id', None) is None for item in restored))
        finally:
            self.close(window)

    def test_copying_group_creates_a_new_independent_group(self):
        window, first, second = self.make_window()
        try:
            first.setSelected(True)
            second.setSelected(True)
            window.group_selected_items()
            window.copy_selected_items()
            window.paste_copied_items()
            groups = {}
            for item in window._groupable_items():
                groups.setdefault(getattr(item, 'group_id', None), []).append(item)
            self.assertEqual(len(groups[1]), 2)
            self.assertEqual(len(groups[2]), 2)
            self.assertEqual(set(window.scene.selectedItems()), set(groups[2]))
        finally:
            self.close(window)

    def test_layer_rows_show_clickable_group_badges(self):
        window, first, second = self.make_window()
        try:
            first.setSelected(True)
            second.setSelected(True)
            window.group_selected_items()
            badges = [button for button in window.layer_list.findChildren(QPushButton)
                      if button.text() == '1']
            self.assertEqual(len(badges), 2)
            window.scene.clearSelection()
            badges[0].click()
            self.assertEqual(set(window.scene.selectedItems()), {first, second})

            rows = [window.layer_list.item(index)
                    for index in range(window.layer_list.count())]
            first_row = next(row for row in rows
                             if row.data(Qt.ItemDataRole.UserRole) is first)
            window.layer_list.clearSelection()
            first_row.setSelected(True)
            self.app.processEvents()
            self.assertEqual(window.scene.selectedItems(), [first])

            badge = window.layer_list.itemWidget(first_row).findChild(LayerGroupBadge)
            window.show()
            self.app.processEvents()
            QTest.mousePress(badge, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            self.assertIs(window.layer_list.currentItem(), first_row)
            self.assertEqual(
                {row.data(Qt.ItemDataRole.UserRole)
                 for row in window.layer_list.selectedItems()},
                {first, second},
            )
            QTest.mouseRelease(badge, Qt.MouseButton.LeftButton)
        finally:
            self.close(window)

    def test_group_button_is_in_the_visible_layer_header(self):
        window, first, second = self.make_window()
        try:
            self.assertIs(window.btn_group_layer.parent(), window.btn_dup_layer.parent())
            self.assertIs(window.btn_group_layer.parent(), window.btn_del_layer.parent())
            self.assertFalse(window.btn_group_layer.isHidden())
            self.assertFalse(window.btn_group_layer.icon().isNull())
            ungrouped = window.btn_group_layer.icon().pixmap(18, 18).toImage()
            first.setSelected(True)
            second.setSelected(True)
            window.group_selected_items()
            grouped = window.btn_group_layer.icon().pixmap(18, 18).toImage()
            self.assertNotEqual(grouped, ungrouped)
        finally:
            self.close(window)

    def test_group_position_rotation_and_resize_transform_members_together(self):
        window, first, second = self.make_window()
        try:
            first.setSelected(True)
            second.setSelected(True)
            window.group_selected_items()

            distance = second.x() - first.x()
            target_x = first.x() + 25
            window.apply_position_x(target_x / (96.0 / 25.4))
            self.assertAlmostEqual(second.x() - first.x(), distance)

            old_centers = {
                item: item.mapToScene(item.transformOriginPoint())
                for item in (first, second)
            }
            window.update_rotation(90)
            self.assertAlmostEqual(first.rotation(), 90)
            self.assertAlmostEqual(second.rotation(), 90)
            self.assertNotEqual(
                second.mapToScene(second.transformOriginPoint()), old_centers[second]
            )

            initial_width = first.rect().width()
            initial_height = first.rect().height()
            first.keep_proportion = False
            second_size = second.rect().size()
            anchor = first.mapToScene(QPointF(0, 0))
            window.begin_group_resize(first, anchor, initial_width, initial_height)
            first.resize_custom(initial_width * 2, initial_height * 1.25)
            window.update_group_resize(first, initial_width * 2, initial_height * 1.25)
            window.end_group_resize()
            self.assertAlmostEqual(first.rect().width(), initial_width * 2)
            self.assertAlmostEqual(first.rect().height(), initial_height * 2)
            self.assertAlmostEqual(second.rect().width(), second_size.width() * 2)
            self.assertAlmostEqual(second.rect().height(), second_size.height() * 2)
        finally:
            self.close(window)

    def test_group_resize_scales_text_typography_and_rich_character_sizes(self):
        window, first, _second = self.make_window()
        try:
            text = DesignerBox(130, 25, 140, 50, 'Texto')
            text.layer_id = window._get_next_layer_id()
            text.custom_name = 'Texto'
            text.state.font_size = 12
            text.state.indent_px = 4
            text.state.rich_text_version = 1
            text.state.html_content = '<p><span style="font-size:10pt">Texto</span></p>'
            text.apply_state()
            window.scene.addItem(text)
            first.setSelected(True)
            text.setSelected(True)
            window.group_selected_items()

            initial_width = first.rect().width()
            initial_height = first.rect().height()
            text_size = text.rect().size()
            anchor = first.mapToScene(QPointF(0, 0))
            window.begin_group_resize(first, anchor, initial_width, initial_height)
            window.update_group_resize(first, initial_width * 2, initial_height * 2)
            window.end_group_resize()

            self.assertEqual(text.state.font_size, 24)
            self.assertAlmostEqual(text.state.indent_px, 8)
            self.assertAlmostEqual(text.rect().width(), text_size.width() * 2)
            self.assertAlmostEqual(text.rect().height(), text_size.height() * 2)
            document = QTextDocument()
            document.setHtml(text.state.html_content)
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.NextCharacter,
                                QTextCursor.MoveMode.KeepAnchor)
            self.assertAlmostEqual(cursor.charFormat().fontPointSize(), 20)
        finally:
            self.close(window)

    def test_group_resize_scales_mask_contents_once(self):
        window, shape, second = self.make_window()
        try:
            image = ImageItem()
            image.layer_id = window._get_next_layer_id()
            image.custom_name = 'Foto'
            image.resize_custom(60, 30)
            window.scene.addItem(image)
            window.create_mask(image, shape)
            window.finish_mask_edit(True)
            image.setPos(10, 8)
            child_size = image.rect().size()
            child_position = QPointF(image.pos())

            shape.setSelected(True)
            second.setSelected(True)
            window.group_selected_items()
            initial_width = shape.rect().width()
            initial_height = shape.rect().height()
            anchor = shape.mapToScene(QPointF(0, 0))
            window.begin_group_resize(shape, anchor, initial_width, initial_height)
            window.update_group_resize(shape, initial_width * 2, initial_height * 2)
            window.end_group_resize()

            self.assertAlmostEqual(image.rect().width(), child_size.width() * 2)
            self.assertAlmostEqual(image.rect().height(), child_size.height() * 2)
            self.assertAlmostEqual(image.x(), child_position.x() * 2)
            self.assertAlmostEqual(image.y(), child_position.y() * 2)
        finally:
            self.close(window)

    def test_group_handle_forces_proportion_and_creates_one_history_action(self):
        window, first, second = self.make_window()
        try:
            first.keep_proportion = False
            second.keep_proportion = False
            first.setSelected(True)
            second.setSelected(True)
            window.group_selected_items()
            initial_index = window.history._current_index
            initial_first_size = first.rect().size()
            initial_second_size = second.rect().size()
            handle = next(
                child for child in first.childItems()
                if isinstance(child, ResizeHandle) and child.name == 'bottom_right'
            )
            press = QGraphicsSceneMouseEvent(QEvent.Type.GraphicsSceneMousePress)
            press.setButton(Qt.MouseButton.LeftButton)
            press.setScenePos(handle.scenePos())
            handle.mousePressEvent(press)
            anchor = QPointF(handle._anchor_scene)
            move = QGraphicsSceneMouseEvent(QEvent.Type.GraphicsSceneMouseMove)
            move.setScenePos(anchor + QPointF(220, 45))
            handle.mouseMoveEvent(move)
            release = QGraphicsSceneMouseEvent(QEvent.Type.GraphicsSceneMouseRelease)
            release.setButton(Qt.MouseButton.LeftButton)
            handle.mouseReleaseEvent(release)

            first_factor = first.rect().width() / initial_first_size.width()
            self.assertAlmostEqual(
                first.rect().height() / initial_first_size.height(), first_factor
            )
            self.assertAlmostEqual(
                second.rect().width() / initial_second_size.width(), first_factor
            )
            self.assertAlmostEqual(
                second.rect().height() / initial_second_size.height(), first_factor
            )
            self.assertEqual(window.history._current_index, initial_index + 1)

            window.undo()
            restored = sorted(window._group_members(1), key=lambda item: item.layer_id)
            self.assertAlmostEqual(restored[0].rect().width(), initial_first_size.width())
            self.assertAlmostEqual(restored[1].rect().width(), initial_second_size.width())
            window.redo()
            redone = sorted(window._group_members(1), key=lambda item: item.layer_id)
            self.assertAlmostEqual(
                redone[1].rect().width() / initial_second_size.width(), first_factor
            )
        finally:
            self.close(window)

    def test_individually_selected_group_member_keeps_individual_resize(self):
        window, first, second = self.make_window()
        try:
            first.setSelected(True)
            second.setSelected(True)
            window.group_selected_items()
            window._selecting_from_layer_list = True
            try:
                window.scene.clearSelection()
                first.setSelected(True)
            finally:
                window._selecting_from_layer_list = False
            window.begin_group_resize(
                first, first.mapToScene(QPointF(0, 0)),
                first.rect().width(), first.rect().height(),
            )
            self.assertIsNone(window._group_resize_session)
        finally:
            self.close(window)

    def test_multiple_selection_uses_one_frame_and_resizes_ungrouped_items(self):
        window, first, second = self.make_window()
        try:
            first.setSelected(True)
            second.setSelected(True)
            self.app.processEvents()
            frame = window._selection_frame
            self.assertTrue(frame.isVisible())
            self.assertEqual(
                window.view.rubberBandSelectionMode(),
                Qt.ItemSelectionMode.ContainsItemShape,
            )
            self.assertTrue(all(not handle.isVisible() for handle in first.resize_handles.values()))
            self.assertTrue(all(not handle.isVisible() for handle in second.resize_handles.values()))
            first_size = first.rect().size()
            second_size = second.rect().size()
            initial_index = window.history._current_index
            handle = next(
                handle for handle in frame.handles
                if handle.x_dir == 1 and handle.y_dir == 1
            )
            press = QGraphicsSceneMouseEvent(QEvent.Type.GraphicsSceneMousePress)
            press.setButton(Qt.MouseButton.LeftButton)
            press.setScenePos(handle.scenePos())
            handle.mousePressEvent(press)
            bounds = QRectF(handle._initial_rect)
            move = QGraphicsSceneMouseEvent(QEvent.Type.GraphicsSceneMouseMove)
            move.setScenePos(handle._anchor + QPointF(
                bounds.width() * 1.5, bounds.height() * 1.5
            ))
            handle.mouseMoveEvent(move)
            release = QGraphicsSceneMouseEvent(QEvent.Type.GraphicsSceneMouseRelease)
            release.setButton(Qt.MouseButton.LeftButton)
            handle.mouseReleaseEvent(release)

            self.assertAlmostEqual(first.rect().width(), first_size.width() * 1.5)
            self.assertAlmostEqual(first.rect().height(), first_size.height() * 1.5)
            self.assertAlmostEqual(second.rect().width(), second_size.width() * 1.5)
            self.assertAlmostEqual(second.rect().height(), second_size.height() * 1.5)
            self.assertEqual(window.history._current_index, initial_index + 1)
            self.assertEqual(set(window.scene.selectedItems()), {first, second})
        finally:
            self.close(window)

    def test_rubber_band_selects_only_fully_contained_items(self):
        window, first, second = self.make_window()
        try:
            window.show()
            self.app.processEvents()
            viewport = window.view.viewport()
            start = window.view.mapFromScene(QPointF(60, 20))
            end = window.view.mapFromScene(QPointF(210, 140))
            QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=start)
            QTest.mouseMove(viewport, end, delay=20)
            QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=end)
            self.app.processEvents()

            self.assertNotIn(first, window.scene.selectedItems())
            self.assertIn(second, window.scene.selectedItems())
        finally:
            self.close(window)

    def test_badge_anchor_moves_noncontiguous_group_as_an_ordered_block(self):
        window, first, second = self.make_window()
        try:
            third = RectangleItem(40, 40, '#999999')
            third.layer_id = window._get_next_layer_id()
            third.custom_name = 'Forma 3'
            window.scene.addItem(third)
            fourth = RectangleItem(40, 40, '#888888')
            fourth.layer_id = window._get_next_layer_id()
            fourth.custom_name = 'Forma 4'
            window.scene.addItem(fourth)
            window.refresh_layer_list()

            for item in (first, third, fourth):
                item.setSelected(True)
            window.group_selected_items()
            rows = {
                window.layer_list.item(index).data(Qt.ItemDataRole.UserRole):
                    window.layer_list.item(index)
                for index in range(window.layer_list.count())
            }
            window.show()
            self.app.processEvents()
            window.show_layer_group_drop_indicator(
                rows[third], rows[second], after=False
            )
            self.assertTrue(window._layer_group_drop_indicator.isVisible())
            self.assertEqual(
                window._layer_group_drop_indicator.y(),
                max(0, window.layer_list.visualItemRect(rows[second]).top() - 1),
            )
            self.assertTrue(window.move_layer_group_from_badge(
                rows[third], rows[second], after=False
            ))
            self.assertFalse(window._layer_group_drop_indicator.isVisible())
            order = [
                window.layer_list.item(index).data(Qt.ItemDataRole.UserRole)
                for index in range(window.layer_list.count())
                if window.layer_list.item(index).data(Qt.ItemDataRole.UserRole)
                in {first, second, third, fourth}
            ]
            self.assertEqual(order, [first, third, fourth, second])
        finally:
            self.close(window)


if __name__ == '__main__':
    unittest.main()
