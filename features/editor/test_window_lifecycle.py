import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt, QPoint, QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
from shiboken6 import isValid

from .editor_window import EditorWindow


class EditorWindowLifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_editor_replaces_workspace_and_returns_geometry(self):
        workspace = QMainWindow()
        workspace.resize(1300, 850)
        workspace.show()
        editor = EditorWindow(workspace)
        editor.show()
        self.app.processEvents()

        self.assertEqual(editor.windowModality(), Qt.WindowModality.NonModal)
        self.assertFalse(workspace.isVisible())
        self.assertEqual(editor.size(), workspace.size())
        self.assertEqual(editor.windowType(), Qt.WindowType.Window)
        self.assertIsNone(editor.findChild(QPushButton, 'closeEditor'))

        editor.showMinimized()
        self.app.processEvents()
        self.assertFalse(workspace.isVisible())

        editor.showNormal()
        self.app.processEvents()
        self.assertFalse(workspace.isVisible())
        editor.resize(1350, 880)
        editor.move(50, 60)
        self.app.processEvents()
        final_geometry = editor.geometry()

        editor._last_saved_state = editor.get_current_scene_state()
        editor.close()
        self.assertTrue(workspace.isVisible())
        self.assertEqual(workspace.geometry(), final_geometry)
        workspace.close()

    def test_cancel_close_keeps_workspace_hidden(self):
        workspace = QMainWindow()
        workspace.show()
        editor = EditorWindow(workspace)
        editor.show()
        editor.add_new_box()
        try:
            with patch('features.editor.editor_window.QMessageBox.exec', return_value=0):
                self.assertFalse(editor.close())
            self.assertTrue(editor.isVisible())
            self.assertFalse(workspace.isVisible())
        finally:
            editor._last_saved_state = editor.get_current_scene_state()
            editor.close()
            workspace.close()

    def test_save_button_tracks_inspector_center(self):
        editor = EditorWindow()
        editor.show()
        self.app.processEvents()
        alignment = editor._footer_save_alignment

        def center_x(widget):
            return widget.mapToGlobal(QPoint(widget.width() // 2, 0)).x()

        self.assertLessEqual(abs(center_x(editor.btn_save) - center_x(alignment.sidebar)), 1)
        alignment.sidebar.parentWidget().setSizes([230, 700, 500])
        self.app.processEvents()
        self.assertLessEqual(abs(center_x(editor.btn_save) - center_x(alignment.sidebar)), 1)

        editor._last_saved_state = editor.get_current_scene_state()
        editor.close()

    def test_current_frontend_survives_deferred_legacy_layout_deletion(self):
        editor = EditorWindow()

        # O layout anterior era descartado com deleteLater(). O erro original
        # só aparecia depois que o event loop efetivava essa exclusão.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

        self.assertTrue(isValid(editor.caixa_texto_panel))
        self.assertTrue(isValid(editor.editor_texto_panel))
        self.assertFalse(hasattr(editor, 'btn_clear_guides'))
        self.assertFalse(hasattr(editor, 'layer_toolbar'))

        editor.add_new_box()
        editor.update_position_ui()
        editor.toggle_guides_lock(True)
        editor.toggle_guides_lock(False)

        editor._last_saved_state = editor.get_current_scene_state()
        editor.close()


if __name__ == '__main__':
    unittest.main()
