import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from .editor_window import EditorWindow
from .canvas_items import DesignerBox


class CanvasEditingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_typing_commit_and_history(self):
        w = EditorWindow()
        w.show()
        w.add_new_box()
        self.app.processEvents()
        self.assertFalse(w.caixa_texto_panel.btn_restore.isVisible())
        box = w.scene.selectedItems()[0]
        original = box.state.html_content
        position = box.pos()
        w.canvas_edit.begin(box)
        QTest.keyClicks(w.view.viewport(), 'abc ')
        QTest.keyClick(w.view.viewport(), Qt.Key.Key_Left)
        QTest.keyClick(w.view.viewport(), Qt.Key.Key_Delete)
        self.assertEqual(box.pos(), position)
        self.assertIn('abc', box.text_item.toPlainText())
        QTest.keyClick(w.view.viewport(), Qt.Key.Key_Escape)
        self.assertIsNone(w.canvas_edit.box)
        committed = box.state.html_content
        self.assertNotEqual(committed, original)
        w.undo()
        boxes = [i for i in w.scene.items() if isinstance(i, DesignerBox)]
        self.assertEqual(boxes[0].state.html_content, original)
        w.redo()
        boxes = [i for i in w.scene.items() if isinstance(i, DesignerBox)]
        self.assertEqual(boxes[0].state.html_content, committed)
        w._last_saved_state = w.get_current_scene_state()
        w.close()
        w.deleteLater()

    def test_double_click_empty_area_appends(self):
        from PySide6.QtCore import QPointF, QEvent
        from PySide6.QtWidgets import QGraphicsSceneMouseEvent
        w = EditorWindow()
        w.show()
        w.add_new_box()
        box = w.scene.selectedItems()[0]
        for content in ('', 'abc'):
            w.canvas_edit.finish()
            box.state.html_content = content
            box.apply_state()
            event = QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseDoubleClick)
            event.setButton(Qt.LeftButton)
            event.setPos(QPointF(290, 50))
            box.mouseDoubleClickEvent(event)
            self.assertEqual(box.text_item.textCursor().position(), len(content))
            QTest.keyClicks(w.view.viewport(), 'z')
            self.assertEqual(box.text_item.toPlainText(), content+'z')
        w.canvas_edit.finish()
        w._last_saved_state = w.get_current_scene_state()
        w.close()


if __name__ == '__main__':
    unittest.main()
