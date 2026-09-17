import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QGraphicsItem

from .canvas_items import DesignerBox, ImageItem, RectangleItem, SignatureItem
from .editor_window import EditorWindow
from core.model_document import load_model_document


class EditorPagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_window(self):
        window = EditorWindow()
        window.show()
        self.app.processEvents()
        return window

    def close_window(self, window):
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()

    def test_add_switch_undo_and_redo_page(self):
        window = self.make_window()
        try:
            window.add_new_box()
            front_html = next(
                item.state.html_content for item in window.scene.items()
                if isinstance(item, DesignerBox)
            )
            window.add_model_page()
            self.assertEqual(window._active_page_id, "back")
            self.assertEqual(len(window._model_document["pages"]), 2)
            self.app.processEvents()
            self.assertGreater(window._footer_save_alignment.pages.width(), 200)
            self.assertEqual(
                [button.text() for button in window._footer_save_alignment.pages.findChildren(
                    QPushButton
                ) if button.objectName() == "pageMain"],
                ["Página 1", "Página 2"],
            )
            self.assertFalse(any(isinstance(item, DesignerBox) for item in window.scene.items()))

            window.add_new_box()
            history_index = window.history._current_index
            window.switch_model_page("front")
            self.assertEqual(window.history._current_index, history_index)
            self.assertEqual(
                next(item.state.html_content for item in window.scene.items()
                     if isinstance(item, DesignerBox)),
                front_html,
            )
            window.switch_model_page("back")
            self.assertEqual(window.history._current_index, history_index)
            window.switch_model_page("front")

            window.undo()
            self.assertEqual(window._active_page_id, "back")
            self.assertFalse(any(isinstance(item, DesignerBox) for item in window.scene.items()))
            window.redo()
            self.assertEqual(window._active_page_id, "back")
            self.assertTrue(any(isinstance(item, DesignerBox) for item in window.scene.items()))
        finally:
            self.close_window(window)

    def test_clear_page_and_remove_first_page_are_undoable(self):
        window = self.make_window()
        try:
            window.add_new_box()
            window.add_model_page()
            window.add_new_box()
            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                window.clear_model_page("back")
            self.assertFalse(any(isinstance(item, DesignerBox) for item in window.scene.items()))
            window.undo()
            self.assertTrue(any(isinstance(item, DesignerBox) for item in window.scene.items()))

            window.switch_model_page("front")
            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                window.remove_model_page("front")
            self.assertEqual(len(window._model_document["pages"]), 1)
            self.assertEqual(window._active_page_id, "front")
            self.assertTrue(any(isinstance(item, DesignerBox) for item in window.scene.items()))
            window.undo()
            self.assertEqual(len(window._model_document["pages"]), 2)
            self.assertEqual(window._active_page_id, "front")
        finally:
            self.close_window(window)

    def test_page_controls_stay_centered_under_canvas(self):
        window = self.make_window()
        try:
            alignment = window._footer_save_alignment

            def center_x(widget):
                return widget.mapToGlobal(QPoint(widget.width() // 2, 0)).x()

            self.assertLessEqual(abs(center_x(alignment.pages) - center_x(alignment.canvas)), 1)
            alignment.canvas.parentWidget().setSizes([310, 640, 550])
            self.app.processEvents()
            self.assertLessEqual(abs(center_x(alignment.pages) - center_x(alignment.canvas)), 1)
        finally:
            self.close_window(window)

    def test_document_dimensions_update_both_page_backgrounds(self):
        window = self.make_window()
        try:
            window.add_model_page()
            window.chk_doc_proporcao.setChecked(False)
            window.spin_phys_w.setValue(200.0)
            window.spin_phys_h.setValue(90.0)
            window.save_snapshot()
            canvas = window._model_document["canvas_size"]
            for page in window._model_document["pages"]:
                background = next(
                    shape for shape in page["shapes"]
                    if shape.get("is_document_background")
                )
                self.assertEqual(background["width"], float(canvas["w"]))
                self.assertEqual(background["height"], float(canvas["h"]))
        finally:
            self.close_window(window)

    def test_each_page_restores_its_own_selection_without_history_entry(self):
        window = self.make_window()
        try:
            window.add_new_box()
            front_box = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
            front_box.setSelected(True)
            window.add_model_page()
            window.add_new_box()
            back_box = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
            back_box.setSelected(True)
            history_index = window.history._current_index

            window.switch_model_page("front")
            selected_front = [item for item in window.scene.selectedItems() if isinstance(item, DesignerBox)]
            self.assertEqual(len(selected_front), 1)
            window.switch_model_page("back")
            selected_back = [item for item in window.scene.selectedItems() if isinstance(item, DesignerBox)]
            self.assertEqual(len(selected_back), 1)
            self.assertEqual(window.history._current_index, history_index)
        finally:
            self.close_window(window)

    def test_save_and_reopen_preserves_both_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            models_dir = Path(directory)
            with patch("features.editor.editor_window.get_models_dir", return_value=models_dir):
                window = self.make_window()
                window._current_model_name = "Modelo Duas Páginas"
                window.add_new_box()
                window.add_model_page()
                window.add_new_box()
                window.export_to_json(skip_close_dialog=True)

                model_dir = models_dir / "modelo_duas_paginas"
                document = load_model_document(model_dir)
                self.assertEqual(len(document["pages"]), 2)
                self.assertEqual(len(document["pages"][0]["boxes"]), 1)
                self.assertEqual(len(document["pages"][1]["boxes"]), 1)

                reopened = self.make_window()
                try:
                    reopened.load_from_json(model_dir)
                    self.assertEqual(reopened._active_page_id, "front")
                    reopened.switch_model_page("back")
                    self.assertTrue(any(
                        isinstance(item, DesignerBox) for item in reopened.scene.items()
                    ))
                finally:
                    self.close_window(reopened)

    def test_field_list_is_the_union_of_both_pages(self):
        window = self.make_window()
        try:
            window.add_new_box()
            front_box = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
            front_box.state.html_content = "<p>{Frente}</p>"
            front_box.apply_state()
            window.sync_placeholders_list()

            window.add_model_page()
            window.add_new_box()
            back_box = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
            back_box.state.html_content = "<p>{Verso}</p>"
            back_box.apply_state()
            window.sync_placeholders_list()

            self.assertEqual(
                [window.lst_placeholders.item(i).text()
                 for i in range(window.lst_placeholders.count())],
                ["Frente", "Verso"],
            )
            window.switch_model_page("front")
            self.assertEqual(set(window.get_all_model_placeholders()), {"Frente", "Verso"})
        finally:
            self.close_window(window)

    def test_copy_and_paste_between_pages_preserves_styles_and_asset_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / "imagem.png"
            image = QImage(24, 16, QImage.Format_ARGB32)
            image.fill(QColor("#336699"))
            self.assertTrue(image.save(str(asset), "PNG"))
            window = self.make_window()
            try:
                window.add_new_box()
                box = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
                box.state.font_family = "Amiri"
                box.state.font_size = 37
                box.state.html_content = '<p><span style="font-family:Amiri; font-size:37pt; color:#923456">Texto rico</span></p>'
                box.custom_name = "Texto"
                box.setRotation(17)
                box.setOpacity(0.65)
                box.state.has_link = True
                box.state.link_key = "Site do texto"
                box.setZValue(8)
                box.apply_state()
                picture = ImageItem(str(asset))
                picture.custom_name = "Imagem compartilhada"
                picture.layer_id = window._get_next_layer_id()
                picture.setPos(80, 90)
                picture.setRotation(-12)
                picture.setOpacity(0.7)
                picture.has_link = True
                picture.link_key = "Site da imagem"
                picture.setZValue(4)
                window.scene.addItem(picture)
                window.scene.clearSelection()
                box.setSelected(True)
                picture.setSelected(True)
                window.copy_selected_items()

                window.add_model_page()
                history_before = window.history._current_index
                window.paste_copied_items()

                pasted_box = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
                pasted_image = next(item for item in window.scene.items() if type(item) is ImageItem)
                self.assertEqual(pasted_box.state.font_family, "Amiri")
                self.assertEqual(pasted_box.state.font_size, 37)
                self.assertIn("Texto rico", pasted_box.state.html_content)
                self.assertEqual(pasted_box.rotation(), 17)
                self.assertAlmostEqual(pasted_box.opacity(), 0.65)
                self.assertTrue(pasted_box.state.has_link)
                self.assertEqual(pasted_box.state.link_key, "Site do texto")
                self.assertEqual(Path(pasted_image._original_path), asset)
                self.assertEqual((pasted_image.x(), pasted_image.y()), (80.0, 90.0))
                self.assertEqual(pasted_image.rotation(), -12)
                self.assertAlmostEqual(pasted_image.opacity(), 0.7)
                self.assertTrue(pasted_image.has_link)
                self.assertEqual(pasted_image.link_key, "Site da imagem")
                self.assertLess(pasted_image.zValue(), pasted_box.zValue())
                self.assertEqual(window.history._current_index, history_before + 1)

                window.switch_model_page("front")
                original_image = next(item for item in window.scene.items() if type(item) is ImageItem)
                self.assertEqual(Path(original_image._original_path), asset)
                self.assertNotEqual(pasted_image.layer_id, original_image.layer_id)
            finally:
                self.close_window(window)

    def test_copy_mixed_selection_preserves_layer_order_shapes_signatures_and_names(self):
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / "assinatura.png"
            image = QImage(30, 12, QImage.Format_ARGB32)
            image.fill(QColor("#552288"))
            self.assertTrue(image.save(str(asset), "PNG"))
            window = self.make_window()
            try:
                window.add_new_box()
                text = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
                text.custom_name = "Texto 2"
                text.setZValue(9)

                shape = RectangleItem(70, 45, "#abc123")
                shape.layer_id = window._get_next_layer_id()
                shape.custom_name = "Quadrado"
                shape.outline_enabled = True
                shape.outline_width = 3.5
                shape.has_link = True
                shape.link_key = "Site da forma"
                shape.setPos(25, 35)
                shape.setRotation(23)
                shape.setZValue(3)
                window.scene.addItem(shape)

                signature = SignatureItem(str(asset))
                signature.layer_id = window._get_next_layer_id()
                signature.custom_name = "Assinatura"
                signature.resize_custom(90, 36)
                signature.setPos(100, 120)
                signature.setRotation(-8)
                signature.setOpacity(0.55)
                signature.setZValue(6)
                window.scene.addItem(signature)

                window.scene.clearSelection()
                for item in (text, shape, signature):
                    item.setSelected(True)
                window.copy_selected_items()
                self.assertEqual([kind for kind, _entry in window._object_clipboard], [
                    "shape", "signature", "text",
                ])

                window.add_model_page()
                window.add_new_box()
                existing_text = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
                existing_text.custom_name = "Texto"
                existing_text_2 = DesignerBox(text="Outro")
                existing_text_2.layer_id = window._get_next_layer_id()
                existing_text_2.custom_name = "Texto 2"
                window.scene.addItem(existing_text_2)
                window.save_snapshot()
                history_before = window.history._current_index

                window.paste_copied_items()

                selected = window.scene.selectedItems()
                pasted_shape = next(item for item in selected if isinstance(item, RectangleItem))
                pasted_signature = next(item for item in selected if isinstance(item, SignatureItem))
                pasted_text = next(item for item in selected if isinstance(item, DesignerBox))
                self.assertEqual(pasted_text.custom_name, "Texto 3")
                self.assertEqual(pasted_shape.fill_color, "#abc123")
                self.assertTrue(pasted_shape.outline_enabled)
                self.assertEqual(pasted_shape.outline_width, 3.5)
                self.assertTrue(pasted_shape.has_link)
                self.assertEqual(pasted_shape.link_key, "Site da forma")
                self.assertEqual((pasted_shape.x(), pasted_shape.y()), (25.0, 35.0))
                self.assertEqual(pasted_shape.rotation(), 23)
                self.assertEqual(Path(pasted_signature._original_path), asset)
                self.assertEqual((pasted_signature.x(), pasted_signature.y()), (100.0, 120.0))
                self.assertEqual(pasted_signature.rotation(), -8)
                self.assertAlmostEqual(pasted_signature.opacity(), 0.55)
                self.assertLess(pasted_shape.zValue(), pasted_signature.zValue())
                self.assertLess(pasted_signature.zValue(), pasted_text.zValue())
                self.assertEqual(window.history._current_index, history_before + 1)
                self.assertEqual(len({getattr(item, "layer_id", None) for item in selected}), 3)

                window.undo()
                self.assertFalse(any(
                    getattr(item, "custom_name", "") in {"Quadrado", "Assinatura", "Texto 3"}
                    for item in window.scene.items()
                ))
                window.redo()
                self.assertEqual(
                    {
                        getattr(item, "custom_name", "") for item in window.scene.items()
                        if getattr(item, "custom_name", "") in {"Quadrado", "Assinatura", "Texto 3"}
                    },
                    {"Quadrado", "Assinatura", "Texto 3"},
                )
            finally:
                self.close_window(window)

    def test_select_all_chooses_only_visible_unlocked_layers(self):
        window = self.make_window()
        try:
            window.add_new_box()
            first = next(item for item in window.scene.items() if isinstance(item, DesignerBox))
            second = DesignerBox(text="Segundo")
            second.layer_id = window._get_next_layer_id()
            window.scene.addItem(second)
            hidden = RectangleItem(40, 30, "#112233")
            hidden.layer_id = window._get_next_layer_id()
            hidden.setVisible(False)
            window.scene.addItem(hidden)
            locked = RectangleItem(40, 30, "#445566")
            locked.layer_id = window._get_next_layer_id()
            locked.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            window.scene.addItem(locked)

            window.scene.clearSelection()
            window.select_all_items()

            self.assertEqual(set(window.scene.selectedItems()), {first, second})
            self.assertFalse(any(
                getattr(item, "is_document_background", False)
                for item in window.scene.selectedItems()
            ))
        finally:
            self.close_window(window)


if __name__ == "__main__":
    unittest.main()
