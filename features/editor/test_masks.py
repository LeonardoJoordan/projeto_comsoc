import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import (
    QApplication, QComboBox, QGraphicsScene, QLineEdit,
    QPushButton, QWidget,
)

from features.generator.renderer import NativeRenderer
from .canvas_items import (
    Guideline,
    ImageItem,
    RectangleItem,
    _item_pos_for_local_scene_point,
    _snap_position_to_guides,
)
from .editor_window import EditorWindow


class ImageMaskTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _asset(folder, color='#e53935'):
        path = Path(folder) / 'image.png'
        image = QImage(80, 40, QImage.Format.Format_ARGB32)
        image.fill(QColor(color))
        assert image.save(str(path), 'PNG')
        return path

    def _window_objects(self, asset):
        window = EditorWindow()
        shape = RectangleItem(100, 80, '#ffffff')
        shape.layer_id = window._get_next_layer_id()
        shape.custom_name = 'Retrato'
        shape.setPos(40, 30)
        shape.setZValue(2)
        window.scene.addItem(shape)
        image = ImageItem(str(asset))
        image.layer_id = window._get_next_layer_id()
        image.custom_name = 'Foto'
        image.resize_custom(160, 60)
        image.setPos(10, 10)
        image.setRotation(12)
        image.setOpacity(0.7)
        image.setZValue(3)
        window.scene.addItem(image)
        window.refresh_layer_list()
        window.save_snapshot()
        return window, shape, image

    def _close(self, window):
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()

    def test_mask_creation_centers_without_changing_image_properties_and_roundtrips(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, image = self._window_objects(asset)
            try:
                image.has_link = True
                image.link_key = 'Perfil'
                history_index = window.history._current_index
                self.assertTrue(window.create_mask(image, shape))
                self.assertFalse(image.has_link)
                self.assertEqual(image.link_key, '')
                self.assertIs(image.parentItem(), shape)
                self.assertEqual(image.rect().size(), QRectF(0, 0, 160, 60).size())
                self.assertEqual(image.rotation(), 12)
                self.assertAlmostEqual(image.opacity(), 0.7)
                self.assertEqual(image.pos(), QPointF(-30, 10))
                window.finish_mask_edit(True)
                self.assertEqual(window.history._current_index, history_index + 1)
                self.assertEqual(shape.mask_group_id, 1)
                self.assertTrue(image.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                self.assertEqual(image.acceptedMouseButtons(), Qt.MouseButton.NoButton)
                self.assertFalse(image.handle_br.isVisible())
                self.assertTrue(shape.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                local_position = QPointF(image.pos())
                scene_position = image.mapToScene(QPointF(0, 0))
                shape.moveBy(15, 8)
                self.assertEqual(image.pos(), local_position)
                self.assertEqual(
                    image.mapToScene(QPointF(0, 0)), scene_position + QPointF(15, 8)
                )

                state = window.get_current_scene_state()
                saved = state['images'][0]
                self.assertFalse(saved['has_link'])
                self.assertEqual(saved['link_key'], '')
                self.assertEqual(saved['mask_shape_id'], f'shape:{shape.layer_id}')
                self.assertEqual(saved['mask_order'], 0)
                saved_shape = next(entry for entry in state['shapes']
                                   if entry.get('object_id') == saved['mask_shape_id'])
                self.assertEqual(saved_shape['mask_group_id'], 1)

                window.apply_scene_state(state)
                restored_shape = next(item for item in window.scene.items()
                                      if isinstance(item, RectangleItem)
                                      and not getattr(item, 'is_document_background', False))
                restored_image = restored_shape.masked_images()[0]
                self.assertEqual(restored_image.pos(), QPointF(-30, 10))
                self.assertEqual(restored_shape.mask_group_id, 1)
                self.assertTrue(
                    restored_image.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                )
                self.assertEqual(
                    restored_image.acceptedMouseButtons(), Qt.MouseButton.NoButton
                )
                window.scene.clearSelection()
                restored_image.setSelected(True)
                self.app.processEvents()
                link_controls = window.findChild(QWidget, 'linkControls')
                self.assertFalse(link_controls.isEnabled())
                self.assertFalse(window.caixa_texto_panel.chk_link.isChecked())

                rendered = NativeRenderer(state).render_preview_image(transparent=True)
                self.assertFalse(rendered.isNull())

                window.refresh_layer_list()
                badges = [
                    button
                    for index in range(window.layer_list.count())
                    for button in window.layer_list.itemWidget(
                        window.layer_list.item(index)
                    ).findChildren(QPushButton)
                    if button.text() == '1'
                ]
                self.assertEqual(len(badges), 2)
                badges[0].click()
                selected_rows = {
                    row.data(Qt.ItemDataRole.UserRole)
                    for row in window.layer_list.selectedItems()
                }
                self.assertEqual(selected_rows, {restored_shape, restored_image})
                self.assertEqual(window.scene.selectedItems(), [restored_shape])
            finally:
                self._close(window)

    def test_first_mask_resize_keeps_the_handle_anchor_in_place(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, image = self._window_objects(asset)
            try:
                self.assertTrue(window.create_mask(image, shape))
                self.assertEqual(image.pos(), QPointF(-30, 10))

                # O canto superior esquerdo é o ponto fixo ao arrastar a alça
                # inferior direita. Ele deve permanecer na mesma coordenada
                # de cena mesmo com forma-pai deslocada e imagem rotacionada.
                fixed_local = QPointF(0, 0)
                fixed_scene = image.mapToScene(fixed_local)
                image.resize_from_handle(220, 82.5)
                image.setPos(_item_pos_for_local_scene_point(
                    image, fixed_local, fixed_scene
                ))

                actual = image.mapToScene(fixed_local)
                self.assertAlmostEqual(actual.x(), fixed_scene.x(), places=6)
                self.assertAlmostEqual(actual.y(), fixed_scene.y(), places=6)
                # A coordenada local continua relacionada à forma; não recebe
                # novamente o deslocamento (40, 30) da máscara.
                self.assertLess(abs(image.pos().x()), 60)
                self.assertLess(abs(image.pos().y()), 60)
                window.finish_mask_edit(True)
            finally:
                self._close(window)

    def test_properties_panel_can_create_mask_starting_from_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, image = self._window_objects(asset)
            try:
                shape.setSelected(True)
                self.app.processEvents()
                enabled = window.findChild(QPushButton, 'maskEnabled')
                details = window.findChild(QWidget, 'maskDetails')
                target = window.findChild(QComboBox, 'maskTarget')
                create = window.findChild(QPushButton, 'maskCreate')
                self.assertIsNotNone(enabled)
                self.assertFalse(enabled.isChecked())
                self.assertTrue(details.isHidden())
                self.assertIsNotNone(target)
                self.assertIsNotNone(create)
                self.assertIs(target.currentData(), image)

                enabled.click()
                self.app.processEvents()
                self.assertFalse(details.isHidden())
                create.click()
                self.app.processEvents()
                self.assertIs(image.parentItem(), shape)
                self.assertIsNotNone(window._mask_edit_session)
                shape_controls = window.findChild(QWidget, 'shapeControls')
                self.assertFalse(shape_controls.isHidden())
                self.assertTrue(shape_controls.isEnabled())
                self.assertTrue(
                    window._inspector_sections['properties'].header.isChecked()
                )
                cancel = window.findChild(QPushButton, 'maskCancel')
                finish = details.findChild(QPushButton, 'primary')
                link_height = window.caixa_texto_panel.chk_link.height()
                self.assertEqual(cancel.height(), link_height)
                self.assertEqual(finish.height(), link_height)
                window.finish_mask_edit(True)
                self.app.processEvents()
                self.assertTrue(enabled.isChecked())
                self.assertFalse(enabled.isEnabled())
                edit = window.findChild(QPushButton, 'maskEdit')
                remove = window.findChild(QPushButton, 'maskRemove')
                self.assertEqual(edit.height(), window.caixa_texto_panel.chk_link.height())
                self.assertEqual(remove.height(), window.caixa_texto_panel.chk_link.height())
                remove.click()
                self.app.processEvents()
                self.assertIsNone(image.parentItem())
            finally:
                self._close(window)

    def test_existing_mask_reveals_new_image_picker_only_on_request(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, image = self._window_objects(asset)
            try:
                window.create_mask(image, shape)
                window.finish_mask_edit(True)
                second = ImageItem(str(asset))
                second.layer_id = window._get_next_layer_id()
                second.custom_name = 'Foto 2'
                window.scene.addItem(second)
                window.refresh_layer_list()
                window.scene.clearSelection()
                shape.setSelected(True)
                self.app.processEvents()

                add_image = window.findChild(QPushButton, 'maskAddImage')
                insert_controls = window.findChild(QWidget, 'maskInsertControls')
                self.assertFalse(add_image.isHidden())
                self.assertTrue(insert_controls.isHidden())
                add_image.click()
                self.app.processEvents()
                self.assertFalse(insert_controls.isHidden())
            finally:
                self._close(window)

    def test_disabling_dynamic_image_fully_releases_shape_for_masking(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, _image = self._window_objects(asset)
            try:
                shape.setSelected(True)
                self.app.processEvents()
                dynamic = window.findChild(QPushButton, 'dynamicImageEnabled')
                field = window.findChild(QLineEdit, 'dynamicImageField')
                dynamic.setChecked(True)
                self.app.processEvents()
                self.assertTrue(shape.dynamic_image_field)

                dynamic.setChecked(False)
                self.app.processEvents()

                self.assertEqual(shape.dynamic_image_field, '')
                self.assertEqual(field.text(), '')
                self.assertIn(shape, window._mask_shapes())
            finally:
                self._close(window)

    def test_mask_edit_shows_excess_at_quarter_opacity_then_clips_it(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            scene = QGraphicsScene(0, 0, 200, 150)
            scene._document_rect = QRectF(0, 0, 200, 150)
            shape = RectangleItem(100, 80, '#ffffff')
            shape.fill_opacity = 0
            shape.setPos(50, 30)
            scene.addItem(shape)
            image = ImageItem(str(asset))
            image.resize_custom(160, 60)
            image.setParentItem(shape)
            image.setPos(-30, 10)
            image.mask_shape_id = 'shape:1'
            shape.refresh_mask_structure()

            def render():
                output = QImage(200, 150, QImage.Format.Format_ARGB32)
                output.fill(QColor(0, 0, 0, 0))
                painter = QPainter(output)
                scene.render(painter, QRectF(0, 0, 200, 150), QRectF(0, 0, 200, 150))
                painter.end()
                return output

            normal = render()
            self.assertEqual(normal.pixelColor(30, 60).alpha(), 0)
            self.assertGreater(normal.pixelColor(80, 60).alpha(), 245)
            shape._mask_editing = True
            shape.refresh_mask_structure()
            editing = render()
            self.assertAlmostEqual(editing.pixelColor(30, 60).alpha(), 64, delta=2)
            self.assertGreater(editing.pixelColor(80, 60).alpha(), 245)

    def test_masked_image_snaps_to_scene_guides_while_editing(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            scene = QGraphicsScene(0, 0, 400, 300)
            scene._document_rect = QRectF(0, 0, 400, 300)
            shape = RectangleItem(180, 120, '#ffffff')
            shape.setPos(100, 50)
            shape._mask_editing = True
            scene.addItem(shape)
            image = ImageItem(str(asset))
            image.resize_custom(40, 30)
            image.setParentItem(shape)
            image.setPos(20, 20)
            image.setSelected(True)
            image._is_mouse_dragging = True
            guide = Guideline(200, is_vertical=True)
            scene.addItem(guide)
            scene._drag_start_positions = {image: QPointF(20, 20)}
            scene._group_raw_delta = None

            snapped = _snap_position_to_guides(image, QPointF(98, 20), 40, 30)
            self.assertEqual(snapped, QPointF(100, 20))

    def test_final_renderer_uses_the_same_mask_geometry(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            state = {
                'name': 'Máscara', 'canvas_size': {'w': 200, 'h': 150},
                'target_w_mm': 20, 'target_h_mm': 15, 'placeholders': [],
                'boxes': [], 'signatures': [], 'guidelines': [],
                'shapes': [{
                    'object_id': 'shape:1', 'layer_id': 1, 'custom_name': 'Elipse',
                    'shape_type': 'ellipse', 'x': 50, 'y': 30, 'width': 100, 'height': 80,
                    'rotation': 0, 'z_value': 1, 'visible': True, 'opacity': 1,
                    'fill_color': '#ffffff', 'fill_opacity': 0,
                    'outline_enabled': False,
                }],
                'images': [{
                    'object_id': 'image:2', 'layer_id': 2, 'custom_name': 'Foto',
                    'path': str(asset), 'x': -30, 'y': 10, 'width': 160, 'height': 60,
                    'rotation': 0, 'z_value': 1, 'visible': True, 'opacity': 1,
                    'mask_shape_id': 'shape:1', 'mask_order': 0,
                }],
                'layer_order': ['shape:1', 'image:2'],
            }
            output = NativeRenderer(state).render_preview_image(transparent=True)
            self.assertEqual(output.pixelColor(52, 32).alpha(), 0)
            self.assertGreater(output.pixelColor(100, 70).alpha(), 245)
            uncached = NativeRenderer(state).render_to_qimage({}, {})
            cached_renderer = NativeRenderer(state)
            cached_renderer.pre_render_static_base()
            self.assertIsNotNone(cached_renderer._static_base_cache)
            cached = cached_renderer.render_to_qimage({}, {})
            self.assertEqual(cached, uncached)

    def test_cancel_restores_state_and_removing_shape_mask_releases_all_images(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, first = self._window_objects(asset)
            try:
                original_position = QPointF(first.pos())
                window.create_mask(first, shape)
                first.moveBy(25, 10)
                window.finish_mask_edit(False)
                first = next(item for item in window.scene.items()
                             if window._is_mask_image(item))
                self.assertIsNone(first.parentItem())
                self.assertEqual(first.pos(), original_position)

                shape = next(item for item in window._mask_shapes()
                             if item.custom_name == 'Retrato')
                window.create_mask(first, shape)
                window.finish_mask_edit(True)
                second = ImageItem(str(asset))
                second.layer_id = window._get_next_layer_id()
                second.custom_name = 'Foto 2'
                window.scene.addItem(second)
                window.create_mask(second, shape)
                window.finish_mask_edit(True)
                self.assertEqual(len(shape.masked_images()), 2)
                window.remove_mask(shape)
                self.assertEqual(shape.masked_images(), [])
                self.assertIsNone(shape.mask_group_id)
                self.assertTrue(all(image.parentItem() is None for image in (first, second)))
                self.assertTrue(all(
                    image.acceptedMouseButtons()
                    == Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton
                    for image in (first, second)
                ))
                self.assertTrue(all(image.zValue() < shape.zValue() for image in (first, second)))
                self.assertLess(first.zValue(), second.zValue())
            finally:
                self._close(window)

    def test_copying_either_member_pastes_the_complete_mask_group(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, image = self._window_objects(asset)
            try:
                window.create_mask(image, shape)
                window.finish_mask_edit(True)
                window.scene.clearSelection()
                image.setSelected(True)
                window.copy_selected_items()
                window.paste_copied_items()

                shapes = [item for item in window._mask_shapes()
                          if item.custom_name.startswith('Retrato')]
                self.assertEqual(len(shapes), 2)
                self.assertTrue(all(len(item.masked_images()) == 1 for item in shapes))
                self.assertEqual({item.mask_group_id for item in shapes}, {1, 2})
                names = {item.custom_name for item in shapes}
                self.assertEqual(names, {'Retrato', 'Retrato 2'})
                copied = next(item for item in shapes if item.custom_name == 'Retrato 2')
                self.assertEqual(copied.masked_images()[0].custom_name, 'Foto 2')
            finally:
                self._close(window)

    def test_shape_resize_scales_internal_composition_and_new_selection_commits(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, image = self._window_objects(asset)
            try:
                window.create_mask(image, shape)
                self.assertIsNotNone(window._mask_edit_session)
                background = next(item for item in window.scene.items()
                                  if getattr(item, 'is_document_background', False))
                background.setSelected(True)
                self.app.processEvents()
                self.assertIsNone(window._mask_edit_session)

                position = QPointF(image.pos())
                size = image.rect().size()
                shape.resize_custom(200, 160)
                self.assertEqual(image.pos(), QPointF(position.x() * 2, position.y() * 2))
                self.assertEqual(image.rect().width(), size.width() * 2)
                self.assertEqual(image.rect().height(), size.height() * 2)
            finally:
                self._close(window)

    def test_mask_group_can_be_copied_to_the_second_page(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = self._asset(folder)
            window, shape, image = self._window_objects(asset)
            try:
                window.create_mask(image, shape)
                window.finish_mask_edit(True)
                window.scene.clearSelection()
                shape.setSelected(True)
                window.copy_selected_items()
                window.add_model_page()
                window.paste_copied_items()
                pasted_shapes = [item for item in window._mask_shapes()
                                 if item.custom_name == 'Retrato']
                self.assertEqual(len(pasted_shapes), 1)
                self.assertEqual(len(pasted_shapes[0].masked_images()), 1)
                self.assertEqual(pasted_shapes[0].masked_images()[0].custom_name, 'Foto')
            finally:
                self._close(window)


if __name__ == '__main__':
    unittest.main()
