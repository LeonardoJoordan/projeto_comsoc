import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtWidgets import QApplication, QTableWidgetItem

from features.spreadsheet.table_panel import TablePanel
from features.spreadsheet.delegates import rich_text_document


APP = QApplication.instance() or QApplication([])


def _panel_with_cell(plain, rich=None):
    panel = TablePanel()
    panel.table.setColumnCount(1)
    panel.table.setHorizontalHeaderLabels(["Nome"])
    panel.table.setRowCount(1)
    item = QTableWidgetItem(plain)
    item.setData(panel.table.RICH_ROLE, rich)
    panel.table.setItem(0, 0, item)
    panel.table.setCurrentCell(0, 0)
    APP.processEvents()
    return panel, item


def _format_for_text(document, text):
    cursor = document.find(text)
    assert not cursor.isNull()
    return cursor.charFormat()


def test_formula_editor_displays_existing_rich_formatting():
    panel, _item = _panel_with_cell(
        "normal forte",
        "<span>normal </span><b>forte</b>",
    )
    try:
        assert panel.cell_editor.toPlainText() == "normal forte"
        assert _format_for_text(panel.cell_editor.document(), "forte").fontWeight() == QFont.Weight.ExtraBold
        assert _format_for_text(panel.cell_editor.document(), "normal").fontWeight() < QFont.Weight.Bold

        cursor = panel.cell_editor.document().find("forte")
        cursor.clearSelection()
        panel.cell_editor.setTextCursor(cursor)
        panel.cell_editor._emit_format_state()
        assert panel.format_buttons["b"].isChecked()
    finally:
        panel.deleteLater()


def test_formula_buttons_apply_bold_italic_and_underline_to_selection_and_cell():
    panel, item = _panel_with_cell("normal forte")
    try:
        editor = panel.cell_editor
        cursor = editor.document().find("forte")
        editor.setTextCursor(cursor)
        panel.format_buttons["b"].click()
        panel.format_buttons["i"].click()
        panel.format_buttons["u"].click()
        APP.processEvents()

        assert item.text() == "normal forte"
        rich = item.data(panel.table.RICH_ROLE)
        assert rich
        stored = QTextDocument()
        stored.setHtml(rich)
        normal = _format_for_text(stored, "normal")
        formatted = _format_for_text(stored, "forte")
        assert normal.fontWeight() < QFont.Weight.Bold
        assert not normal.fontItalic()
        assert not normal.fontUnderline()
        assert formatted.fontWeight() == QFont.Weight.ExtraBold
        assert formatted.fontItalic()
        assert formatted.fontUnderline()
    finally:
        panel.deleteLater()


def test_table_format_shortcut_path_refreshes_formula_editor():
    panel, item = _panel_with_cell("conteúdo")
    try:
        item.setSelected(True)
        panel.table._toggle_format("b")
        APP.processEvents()

        assert item.data(panel.table.RICH_ROLE) == "<b>conteúdo</b>"
        assert _format_for_text(
            panel.cell_editor.document(), "conteúdo"
        ).fontWeight() == QFont.Weight.ExtraBold
    finally:
        panel.deleteLater()


def test_compact_cell_document_promotes_bold_to_extra_bold():
    document = rich_text_document(
        "<span>normal </span><b>forte</b>",
        QFont("Inter 18pt", 10),
        "#ffffff",
        no_wrap=True,
    )

    assert _format_for_text(document, "normal").fontWeight() < QFont.Weight.Bold
    assert _format_for_text(document, "forte").fontWeight() == QFont.Weight.ExtraBold
