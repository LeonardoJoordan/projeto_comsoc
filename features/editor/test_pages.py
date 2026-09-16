import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from .canvas_items import DesignerBox, ImageItem
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
                box.apply_state()
                picture = ImageItem(str(asset))
                picture.custom_name = "Imagem compartilhada"
                picture.layer_id = window._get_next_layer_id()
                picture.setPos(80, 90)
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
                self.assertEqual(Path(pasted_image._original_path), asset)
                self.assertEqual((pasted_image.x(), pasted_image.y()), (80.0, 90.0))
                self.assertEqual(window.history._current_index, history_before + 1)

                window.switch_model_page("front")
                original_image = next(item for item in window.scene.items() if type(item) is ImageItem)
                self.assertEqual(Path(original_image._original_path), asset)
                self.assertNotEqual(pasted_image.layer_id, original_image.layer_id)
            finally:
                self.close_window(window)


if __name__ == "__main__":
    unittest.main()
