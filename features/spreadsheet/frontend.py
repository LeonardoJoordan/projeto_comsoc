from core.themes import themed_style, theme_color, theme_manager
"""Apresentação da planilha; preserva os controles e as operações da tabela."""
from PySide6.QtCore import Qt, QSize, QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QPlainTextEdit,
)
from PySide6.QtGui import QIcon, QPixmap, QPainter
from shiboken6 import isValid
from pathlib import Path
from features.editor.frontend import icon


class CellContentEditor(QPlainTextEdit):
    """Campo superior: Enter confirma; Shift+Enter cria uma nova linha."""

    commitRequested = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.commitRequested.emit()
                event.accept()
                return
        super().keyPressEvent(event)


def sheet_icon(path):
    return icon(path)


def install_frontend(panel):
    layout = panel.layout()
    while layout.count():
        entry = layout.takeAt(0)
        if entry.widget():
            entry.widget().hide()
        if entry.layout():
            old = entry.layout()
            while old.count():
                old.takeAt(0)
            old.deleteLater()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

    heading = QFrame()
    heading.setObjectName('sheetHeading')
    head = QHBoxLayout(heading)
    head.setContentsMargins(14, 14, 14, 14)
    title = QLabel('Dados para o modelo')
    title.setObjectName('sheetTitle')
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    head.addSpacing(70)
    head.addStretch(1)
    head.addWidget(title)
    head.addStretch(1)
    count = QLabel()
    count.setObjectName('sheetCount')
    count.setFixedWidth(70)
    count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    head.addWidget(count)
    layout.addWidget(heading)

    toolbar = QFrame()
    toolbar.setObjectName('sheetToolbar')
    toolbar_layout = QVBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)
    toolbar_layout.setSpacing(0)
    line_tools_title = QLabel('LINHAS')
    line_tools_title.setObjectName('sheetSectionTitle')
    line_tools_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    line_tools_title.setContentsMargins(14, 9, 14, 0)
    toolbar_layout.addWidget(line_tools_title)
    actions = QHBoxLayout()
    actions.setContentsMargins(4, 5, 4, 9)
    actions.setSpacing(4)
    panel.spin_add_rows.setFixedWidth(46)
    panel.spin_add_rows.setAccessibleName('Quantidade de linhas a adicionar')
    specs = (
        (panel.btn_add_rows, 'Adicionar', 'Adicionar linhas', None),
        (panel.btn_duplicate_row, 'Duplicar', 'Duplicar linhas selecionadas', None),
        (panel.btn_delete_rows, 'Excluir', 'Excluir linhas selecionadas', None),
    )
    for button, text, tip, path in specs:
        button.setText(text)
        button.setToolTip(tip)
        button.setAccessibleName(tip)
        button.setIcon(sheet_icon(path) if path else QIcon())
        button.setIconSize(QSize(18, 18))
        button.setObjectName('sheetLineAction' if text else 'sheetSquare')
        if not text:
            button.setFixedSize(30, 30)
    actions.addWidget(panel.spin_add_rows)
    actions.addWidget(panel.btn_add_rows)
    separator = QFrame()
    separator.setFixedSize(1, 20)
    themed_style(separator, 'background: @border@; border: none;')
    actions.addWidget(separator)
    actions.addWidget(panel.btn_duplicate_row)
    actions.addWidget(panel.btn_delete_rows)
    actions.addStretch()
    panel.btn_toggle_wrap.setText('Exibir conteúdo completo')
    panel.btn_toggle_wrap.setToolTip(
        'Alterna entre linhas compactas e altura automática para mostrar todo o conteúdo'
    )
    panel.btn_toggle_wrap.setIcon(sheet_icon('<path d="M4 6h16M4 11h12a4 4 0 0 1 0 8h-4m3-3-3 3 3 3M4 16h3"/>'))
    panel.btn_toggle_wrap.setObjectName('sheetLineAction')
    actions.addWidget(panel.btn_toggle_wrap)
    toolbar_layout.addLayout(actions)
    layout.addWidget(toolbar)

    formula_bar = QFrame()
    formula_bar.setObjectName('formulaBar')
    formula_layout = QVBoxLayout(formula_bar)
    formula_layout.setContentsMargins(0, 0, 0, 0)
    formula_layout.setSpacing(0)
    editor_row = QHBoxLayout()
    editor_row.setContentsMargins(12, 8, 12, 5)
    editor_row.setSpacing(8)
    formula_label = QLabel('fx')
    formula_label.setObjectName('formulaLabel')
    formula_label.setFixedWidth(24)
    formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    editor_row.addWidget(formula_label)
    cell_editor = CellContentEditor()
    cell_editor.setObjectName('cellEditor')
    cell_editor.setPlaceholderText('Selecione uma célula para visualizar ou editar seu conteúdo')
    cell_editor.setFixedHeight(58)
    cell_editor.setEnabled(False)
    editor_row.addWidget(cell_editor, 1)
    formula_layout.addLayout(editor_row)
    format_row = QHBoxLayout()
    format_row.setContentsMargins(44, 0, 12, 8)
    format_row.setSpacing(8)
    for caption, tag, tooltip in [('B', 'b', 'Negrito · Ctrl+B'), ('I', 'i', 'Itálico · Ctrl+I'), ('U', 'u', 'Sublinhado · Ctrl+U')]:
        button = QPushButton(caption)
        button.setObjectName('sheetSquare')
        button.setFixedSize(30, 30)
        button.setToolTip(tooltip)
        font = button.font()
        font.setBold(tag == 'b')
        font.setItalic(tag == 'i')
        font.setUnderline(tag == 'u')
        button.setFont(font)
        button.clicked.connect(lambda checked=False, t=tag: panel.table._toggle_format(t))
        format_row.addWidget(button)
    format_row.addStretch(1)
    formula_layout.addLayout(format_row)
    layout.addWidget(formula_bar)

    hint = QLabel('Selecione uma célula para começar · Cole do Excel ou Google Sheets com Ctrl+V')
    hint.setObjectName('sheetHint')
    layout.addWidget(hint)
    table = panel.table
    cell_editor.commitRequested.connect(lambda: table.setFocus(Qt.FocusReason.OtherFocusReason))
    table.setObjectName('dataGrid')
    table.setAlternatingRowColors(False)
    table.verticalHeader().setDefaultSectionSize(25)
    table.verticalHeader().setMinimumSectionSize(25)
    table.verticalHeader().setMinimumWidth(38)
    table.horizontalHeader().setMinimumSectionSize(64)
    table.horizontalHeader().setDefaultSectionSize(150)
    table.horizontalHeader().setFixedHeight(36)
    table.setCornerButtonEnabled(False)
    table.setWordWrap(False)
    panel.btn_toggle_wrap.setChecked(False)
    table.setTextElideMode(Qt.TextElideMode.ElideRight)
    themed_style(table, '')
    layout.addWidget(table, 1)
    table.show()

    def update_state(*_):
        if not isValid(table) or not isValid(count):
            return
        rows = table.rowCount()
        count.setText(f'{rows} linha' if rows == 1 else f'{rows} linhas')
        selected = bool(table.selectedIndexes())
        panel.btn_duplicate_row.setEnabled(selected)
        panel.btn_delete_rows.setEnabled(selected)
    table.model().rowsInserted.connect(update_state)
    table.model().rowsRemoved.connect(update_state)
    table.model().modelReset.connect(update_state)
    table.itemSelectionChanged.connect(update_state)
    def load_cell_editor(row, column, *_):
        header = table.horizontalHeaderItem(column) if column >= 0 else None
        hint.setText(f'Linha {row + 1}  /  {header.text()}    ·    Duplo clique para editar' if row >= 0 and header else 'Cole do Excel ou Google Sheets com Ctrl+V')
        item = table.item(row, column) if row >= 0 and column >= 0 else None
        with QSignalBlocker(cell_editor):
            cell_editor.setPlainText(item.text() if item else '')
        cell_editor.setEnabled(row >= 0 and column >= 0)

    def update_from_formula():
        row, column = table.currentRow(), table.currentColumn()
        if row < 0 or column < 0:
            return
        item = table.item(row, column)
        if item is None:
            from PySide6.QtWidgets import QTableWidgetItem
            item = QTableWidgetItem()
            table.setItem(row, column, item)
        value = cell_editor.toPlainText()
        if item.text() != value:
            item.setText(value)
            item.setData(table.RICH_ROLE, None)

    def refresh_formula_from_item(item):
        if item.row() == table.currentRow() and item.column() == table.currentColumn():
            # A edição no campo superior já contém este mesmo valor. Recarregá-lo
            # a cada tecla levaria o cursor para o início e inverteria a digitação.
            if cell_editor.toPlainText() == item.text():
                return
            with QSignalBlocker(cell_editor):
                cell_editor.setPlainText(item.text())

    table.currentCellChanged.connect(load_cell_editor)
    table.itemChanged.connect(refresh_formula_from_item)
    cell_editor.textChanged.connect(update_from_formula)
    update_state()
    themed_style(panel, '''
        QFrame#sheetHeading, QFrame#sheetToolbar { background: @panel@; border: none; border-bottom: 1px solid @border@; }
        QLabel#sheetTitle { color: @text@; font-size: 12px; font-weight: 600; }
        QLabel#sheetCount { color: @muted@; font-size: 11px; }
        QLabel#sheetSectionTitle { color: @muted@; font-size: 10px; font-weight: 600; }
        QLabel#sheetHint { background: @surface@; color: @muted@; padding: 10px 14px; font-size: 11px; }
        QPushButton#sheetSquare { padding: 0; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; }
        QPushButton#sheetAction { padding: 0 10px; min-height: 28px; max-height: 28px; }
        QPushButton#sheetLineAction { padding: 0 3px; min-height: 28px; max-height: 28px; }
        QSpinBox { padding: 0 5px; min-height: 28px; max-height: 28px; }
        QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 18px; background: @border@; border-left: 1px solid @border_strong@; }
        QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 18px; background: @border@; border-left: 1px solid @border_strong@; }
        QSpinBox::up-arrow { image: url(@spin_up@); width: 10px; height: 6px; }
        QSpinBox::down-arrow { image: url(@spin_down@); width: 10px; height: 6px; }
        QTableWidget#dataGrid { background: @field@; alternate-background-color: @alternate@; border: none; border-radius: 0; gridline-color: @grid@; selection-background-color: @selection@; selection-color: @text@; }
        QTableWidget#dataGrid::item { padding: 6px 10px; }
        QHeaderView::section { background: @header@; color: @icon@; font-weight: 600; border: none; border-right: 1px solid @border@; border-bottom: 1px solid @border@; padding: 6px 10px; }
        QTableCornerButton::section { background: @header@; border: none; }
    '''.replace('__ICONS__', (Path(__file__).resolve().parents[1] / 'editor' / 'icons').as_posix()) + '''
        QWidget#dataPanel { background: @field@; border: 1px solid @border@; border-radius: 8px; padding: 0; }
        QFrame#sheetHeading { background: @panel@; border: none; }
        QLabel#sheetTitle { color: @text@; font-size: 18px; font-weight: 600; }
        QLabel#sheetCount { color: @muted@; font-size: 12px; }
        QLabel#sheetSectionTitle { color: @muted@; font-size: 10px; font-weight: 600; }
        QFrame#sheetToolbar { background: @surface@; border: none; border-bottom: 1px solid @border@; }
        QFrame#formulaBar { background: @panel@; border: none; border-bottom: 1px solid @border@; }
        QLabel#formulaLabel { color: @accent@; font-size: 13px; font-style: italic; }
        QPlainTextEdit#cellEditor { background: @field@; color: @text@; border: 1px solid @border@; border-radius: 5px; padding: 5px 8px; selection-background-color: @selection@; }
        QPlainTextEdit#cellEditor:focus { border-color: @accent@; }
        QPlainTextEdit#cellEditor:disabled { color: @disabled@; background: @panel@; }
        QLabel#sheetHint { background: @panel@; color: @muted@; padding: 9px 14px; font-size: 11px; border-bottom: 1px solid @border@; }
        QPushButton#sheetSquare, QPushButton#sheetAction, QPushButton#sheetLineAction { background: transparent; color: @text@; border: 1px solid transparent; border-radius: 5px; }
        QPushButton#sheetSquare:hover, QPushButton#sheetAction:hover, QPushButton#sheetLineAction:hover { background: @hover@; }
        QPushButton#sheetSquare:pressed, QPushButton#sheetAction:checked, QPushButton#sheetLineAction:checked { background: @selection@; color: @text@; }
        QPushButton#sheetSquare:disabled { color: @disabled@; }
        QSpinBox { background: @field@; color: @text@; border: 1px solid @border@; border-radius: 5px; }
        QSpinBox::up-button, QSpinBox::down-button { background: @border@; border: none; }
        QTableWidget#dataGrid { background: @field@; color: @text@; alternate-background-color: @field@; gridline-color: @grid@; selection-background-color: @selection@; selection-color: @text@; font-size: 13px; }
        QHeaderView { background: @surface@; }
        QHeaderView::section { background: @surface@; color: @muted@; font-size: 11px; font-weight: 500; border: none; border-right: 1px solid @grid@; border-bottom: 1px solid @border@; padding: 6px 8px; }
        QHeaderView::section:checked { background: @selection@; color: @accent@; }
        QTableCornerButton::section { background: @surface@; border: none; }
        QTextEdit { background: @field@; color: @text@; border: 2px solid @accent@; border-radius: 0; padding: 2px 6px; selection-background-color: @selection@; selection-color: @text@; }
        QScrollBar:vertical, QScrollBar:horizontal { background: @scroll_track@; }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: @scroll_handle@; border-radius: 2px; }
        QScrollBar::handle:hover { background: @scroll_hover@; }
        QAbstractScrollArea::corner { background: @scroll_track@; }
    ''')
