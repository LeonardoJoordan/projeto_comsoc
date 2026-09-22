import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QFontMetrics, QTextCursor
from PySide6.QtTest import QTest
from core.text_layout import (
    REFERENCE_GLYPHS, build_document, line_reference_ink_bounds, resolve_rich_text, text_geometry,
)
from .editor_window import EditorWindow
from .canvas_items import DesignerBox


class CanvasEditingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_arrow_moves_keep_canvas_focus_after_reselecting_text(self):
        from unittest.mock import patch
        from .canvas_items import px_to_mm
        w = EditorWindow()
        w.show()
        try:
            w.add_new_box()
            self.app.processEvents()
            box = next(i for i in w.scene.items() if isinstance(i, DesignerBox))
            w.scene.clearSelection()
            self.app.processEvents()
            point = w.view.mapFromScene(box.mapToScene(box.rect().center()))
            QTest.mouseClick(w.view.viewport(), Qt.LeftButton, pos=point)
            self.app.processEvents()
            initial_y = box.y()
            previous_y = initial_y
            for _ in range(4):
                # Envia ao foco real: enviar sempre à view esconderia o bug.
                self.assertIs(self.app.focusWidget(), w.view)
                QTest.keyClick(self.app.focusWidget(), Qt.Key_Up)
                self.app.processEvents()
                self.assertLess(box.y(), previous_y)
                previous_y = box.y()
                self.assertTrue(box.isSelected())
                self.assertAlmostEqual(w.spin_pos_y.value(), px_to_mm(box.y()), places=2)
            self.assertIs(self.app.focusWidget(), w.view)
            # Sincronizar uma fonte diferente também não deve tomar o foco.
            with patch.object(w.editor_texto_panel.txt_content, 'setFocus') as focus:
                box.state.font_family = 'monospace'
                w.on_selection_changed()
                focus.assert_not_called()
            w.undo()
            restored = next(i for i in w.scene.items() if isinstance(i, DesignerBox))
            self.assertGreater(restored.y(), previous_y)
            self.assertLess(restored.y(), initial_y)
        finally:
            w._last_saved_state = w.get_current_scene_state()
            w.close()
            w.deleteLater()

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

    def test_rich_amiri_uses_actual_font_for_vertical_alignment(self):
        if "Amiri" not in QFontDatabase.families():
            self.skipTest("Fonte Amiri não instalada")
        html = '<p><span style="font-family:Amiri; font-size:36pt">مرحبا {nome}</span></p>'
        data = {
            "w": 300, "h": 120, "html": html,
            "font_family": "Liberation Sans", "font_size": 12,
            "rich_text_version": 1, "vertical_align": "bottom",
        }
        doc = build_document(data, html)
        doc.documentLayout().documentSize()
        block = doc.begin()
        line = block.layout().lineAt(0)
        ink_bounds = line_reference_ink_bounds(doc, block, line)
        expected = QFontMetrics(QFont("Amiri", 36)).tightBoundingRect(REFERENCE_GLYPHS)
        self.assertEqual(ink_bounds, (expected.top(), expected.bottom()))

        renderer_y, _, _ = text_geometry(doc, data)
        box = DesignerBox(w=300, h=120)
        box.state.html_content = html
        box.state.font_family = "Liberation Sans"
        box.state.font_size = 12
        box.state.vertical_align = "bottom"
        box.state.rich_text_version = 1
        box.apply_state()
        self.assertAlmostEqual(box.text_item.pos().y(), renderer_y)

    def test_rich_placeholder_replacement_preserves_its_font_and_size(self):
        if "Amiri" not in QFontDatabase.families():
            self.skipTest("Fonte Amiri não instalada")
        html = '<p><span style="font-family:Amiri; font-size:45pt">{nome}</span></p>'
        data = {
            "w": 500, "h": 100, "html": html,
            "font_family": "Liberation Sans", "font_size": 16,
            "rich_text_version": 1,
        }

        resolved = resolve_rich_text(data, {"nome": "Leonardo"})
        doc = build_document(data, resolved)
        cursor = QTextCursor(doc)
        cursor.setPosition(1)
        fmt = cursor.charFormat()

        self.assertEqual(doc.toPlainText(), "Leonardo")
        self.assertEqual(fmt.fontFamilies()[0], "Amiri")
        self.assertEqual(round(fmt.fontPointSize()), 45)

    def test_rich_placeholder_ignores_qt_cell_font_and_size(self):
        html = '<p><span style="font-family:Liberation Serif; font-size:31pt; color:#123456">{nome}</span></p>'
        qt_cell_html = (
            '<html><head><meta name="qrichtext" content="1" /></head>'
            '<body style="font-family:Inter; font-size:9pt; color:#abcdef">'
            '<p><span style="font-family:Arial; font-size:7pt; font-weight:700;">Leonardo</span></p>'
            '</body></html>'
        )
        data = {
            "w": 500, "h": 100, "html": html,
            "font_family": "Liberation Sans", "font_size": 16,
            "rich_text_version": 1,
        }

        resolved = resolve_rich_text(data, {"nome": qt_cell_html})
        doc = build_document(data, resolved)
        cursor = QTextCursor(doc)
        cursor.setPosition(1)
        fmt = cursor.charFormat()

        self.assertEqual(doc.toPlainText(), "Leonardo")
        self.assertEqual(fmt.fontFamilies()[0], "Liberation Serif")
        self.assertEqual(round(fmt.fontPointSize()), 31)
        self.assertEqual(fmt.foreground().color().name(), "#123456")
        self.assertGreater(fmt.fontWeight(), QFont.Weight.Normal)

    def test_rich_placeholder_keeps_cell_italic_and_underline_only(self):
        html = '<p><span style="font-family:Liberation Sans; font-size:22pt">{nome}</span></p>'
        qt_cell_html = (
            '<span style="font-family:Arial; font-size:8pt; font-style:italic; '
            'text-decoration: underline;">Texto</span>'
        )
        data = {
            "w": 500, "h": 100, "html": html,
            "font_family": "Liberation Sans", "font_size": 16,
            "rich_text_version": 1,
        }

        resolved = resolve_rich_text(data, {"nome": qt_cell_html})
        doc = build_document(data, resolved)
        cursor = QTextCursor(doc)
        cursor.setPosition(1)
        fmt = cursor.charFormat()

        self.assertEqual(doc.toPlainText(), "Texto")
        self.assertEqual(round(fmt.fontPointSize()), 22)
        self.assertTrue(fmt.fontItalic())
        self.assertTrue(fmt.fontUnderline())

    def test_undo_redo_preserves_collapsed_inspector_section(self):
        w = EditorWindow()
        w.show()
        w.add_new_box()
        self.app.processEvents()
        box = w.scene.selectedItems()[0]
        properties = w._inspector_sections['properties']
        properties.header.setChecked(False)

        box.moveBy(20, 0)
        w.save_snapshot()
        w.undo()
        self.assertFalse(properties.header.isChecked())
        self.assertEqual(len(w.scene.selectedItems()), 1)

        w.redo()
        self.assertFalse(properties.header.isChecked())
        self.assertEqual(len(w.scene.selectedItems()), 1)
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
