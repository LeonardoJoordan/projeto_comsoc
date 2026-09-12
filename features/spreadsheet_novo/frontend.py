"""Apresentação da planilha; preserva os controles e as operações da tabela."""
from PySide6.QtCore import Qt, QSize, QSignalBlocker
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton, QPlainTextEdit
from PySide6.QtGui import QIcon, QPixmap, QPainter
from shiboken6 import isValid
from pathlib import Path
from features.editor_novo.frontend import icon


def sheet_icon(path):
    source = icon(path).pixmap(20, 20)
    painter = QPainter(source)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(source.rect(), '#c5c3df')
    painter.end()
    return QIcon(source)


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
    title = QLabel('Dados')
    title.setObjectName('sheetTitle')
    head.addWidget(title)
    head.addStretch()
    count = QLabel()
    count.setObjectName('sheetCount')
    head.addWidget(count)
    layout.addWidget(heading)

    toolbar = QFrame()
    toolbar.setObjectName('sheetToolbar')
    actions = QHBoxLayout(toolbar)
    actions.setContentsMargins(12, 10, 12, 10)
    actions.setSpacing(8)
    panel.spin_add_rows.setFixedWidth(58)
    panel.spin_add_rows.setAccessibleName('Quantidade de linhas a adicionar')
    actions.addWidget(panel.spin_add_rows)
    specs = (
        (panel.btn_add_rows, 'Adicionar', 'Adicionar linhas', '<path d="M12 5v14M5 12h14"/>'),
        (panel.btn_duplicate_row, '', 'Duplicar linhas selecionadas', '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M15 8V4H4v11h4"/>'),
        (panel.btn_delete_rows, '', 'Excluir linhas selecionadas', '<path d="M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>'),
    )
    for button, text, tip, path in specs:
        button.setText(text)
        button.setToolTip(tip)
        button.setAccessibleName(tip)
        button.setIcon(sheet_icon(path))
        button.setIconSize(QSize(18, 18))
        button.setObjectName('sheetAction' if text else 'sheetSquare')
        if not text:
            button.setFixedSize(30, 30)
        actions.addWidget(button)
    separator = QFrame()
    separator.setFixedSize(1, 20)
    separator.setStyleSheet('background: #30323b; border: none;')
    actions.addWidget(separator)
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
        actions.addWidget(button)
    actions.addStretch()
    panel.btn_toggle_wrap.setText('Quebrar texto')
    panel.btn_toggle_wrap.setIcon(sheet_icon('<path d="M4 6h16M4 11h12a4 4 0 0 1 0 8h-4m3-3-3 3 3 3M4 16h3"/>'))
    panel.btn_toggle_wrap.setObjectName('sheetAction')
    actions.addWidget(panel.btn_toggle_wrap)
    layout.addWidget(toolbar)

    formula_bar = QFrame()
    formula_bar.setObjectName('formulaBar')
    formula_layout = QHBoxLayout(formula_bar)
    formula_layout.setContentsMargins(12, 8, 12, 8)
    formula_layout.setSpacing(8)
    formula_label = QLabel('fx')
    formula_label.setObjectName('formulaLabel')
    formula_label.setFixedWidth(24)
    formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    formula_layout.addWidget(formula_label)
    cell_editor = QPlainTextEdit()
    cell_editor.setObjectName('cellEditor')
    cell_editor.setPlaceholderText('Selecione uma célula para visualizar ou editar seu conteúdo')
    cell_editor.setFixedHeight(58)
    cell_editor.setEnabled(False)
    formula_layout.addWidget(cell_editor, 1)
    layout.addWidget(formula_bar)

    hint = QLabel('Selecione uma célula para começar · Cole do Excel ou Google Sheets com Ctrl+V')
    hint.setObjectName('sheetHint')
    layout.addWidget(hint)
    table = panel.table
    table.setObjectName('dataGrid')
    table.setAlternatingRowColors(False)
    table.verticalHeader().setDefaultSectionSize(25)
    table.verticalHeader().setMinimumWidth(38)
    table.horizontalHeader().setMinimumSectionSize(64)
    table.horizontalHeader().setDefaultSectionSize(150)
    table.horizontalHeader().setFixedHeight(36)
    table.setCornerButtonEnabled(False)
    table.setWordWrap(False)
    panel.btn_toggle_wrap.setChecked(False)
    table.setTextElideMode(Qt.TextElideMode.ElideRight)
    table.setStyleSheet('')
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
            with QSignalBlocker(cell_editor):
                cell_editor.setPlainText(item.text())

    table.currentCellChanged.connect(load_cell_editor)
    table.itemChanged.connect(refresh_formula_from_item)
    cell_editor.textChanged.connect(update_from_formula)
    update_state()
    panel.setStyleSheet('''
        QFrame#sheetHeading, QFrame#sheetToolbar { background: #15161b; border: none; border-bottom: 1px solid #30323b; }
        QLabel#sheetTitle { color: #f3f5f8; font-size: 12px; font-weight: 600; }
        QLabel#sheetCount { color: #a8abb5; font-size: 11px; }
        QLabel#sheetHint { background: #1a1b21; color: #8f939f; padding: 10px 14px; font-size: 11px; }
        QPushButton#sheetSquare { padding: 0; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; }
        QPushButton#sheetAction { padding: 0 10px; min-height: 28px; max-height: 28px; }
        QSpinBox { padding: 0 5px; min-height: 28px; max-height: 28px; }
        QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 18px; background: #30323b; border-left: 1px solid #454854; }
        QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 18px; background: #30323b; border-left: 1px solid #454854; }
        QSpinBox::up-arrow { image: url(__ICONS__/spin-up.svg); width: 10px; height: 6px; }
        QSpinBox::down-arrow { image: url(__ICONS__/spin-down.svg); width: 10px; height: 6px; }
        QTableWidget#dataGrid { background: #121318; alternate-background-color: #18191f; border: none; border-radius: 0; gridline-color: #292b33; selection-background-color: #343159; selection-color: #f3f5f8; }
        QTableWidget#dataGrid::item { padding: 6px 10px; }
        QHeaderView::section { background: #1e2027; color: #bfc2cf; font-weight: 600; border: none; border-right: 1px solid #30323b; border-bottom: 1px solid #30323b; padding: 6px 10px; }
        QTableCornerButton::section { background: #1e2027; border: none; }
    '''.replace('__ICONS__', (Path(__file__).resolve().parents[1] / 'editor_novo' / 'icons').as_posix()) + '''
        QWidget#dataPanel { background: #121318; border: 1px solid #30323b; border-radius: 8px; padding: 0; }
        QFrame#sheetHeading { background: #15161b; border: none; }
        QLabel#sheetTitle { color: #f3f5f8; font-size: 18px; font-weight: 600; }
        QLabel#sheetCount { color: #a8abb5; font-size: 12px; }
        QFrame#sheetToolbar { background: #1a1b21; border: none; border-bottom: 1px solid #30323b; }
        QFrame#formulaBar { background: #15161b; border: none; border-bottom: 1px solid #30323b; }
        QLabel#formulaLabel { color: #9087ff; font-size: 13px; font-style: italic; }
        QPlainTextEdit#cellEditor { background: #121318; color: #f3f5f8; border: 1px solid #30323b; border-radius: 5px; padding: 5px 8px; selection-background-color: #343159; }
        QPlainTextEdit#cellEditor:focus { border-color: #7c73f2; }
        QPlainTextEdit#cellEditor:disabled { color: #777b87; background: #15161b; }
        QLabel#sheetHint { background: #15161b; color: #8f939f; padding: 9px 14px; font-size: 11px; border-bottom: 1px solid #30323b; }
        QPushButton#sheetSquare, QPushButton#sheetAction { background: transparent; color: #c9cbd3; border: 1px solid transparent; border-radius: 5px; }
        QPushButton#sheetSquare:hover, QPushButton#sheetAction:hover { background: #2a2c35; }
        QPushButton#sheetSquare:pressed, QPushButton#sheetAction:checked { background: #343159; color: #f3f5f8; }
        QPushButton#sheetSquare:disabled { color: #777b87; }
        QSpinBox { background: #121318; color: #f3f5f8; border: 1px solid #30323b; border-radius: 5px; }
        QSpinBox::up-button, QSpinBox::down-button { background: #30323b; border: none; }
        QTableWidget#dataGrid { background: #121318; color: #f3f5f8; alternate-background-color: #121318; gridline-color: #292b33; selection-background-color: #343159; selection-color: #f3f5f8; font-size: 13px; }
        QHeaderView { background: #1a1b21; }
        QHeaderView::section { background: #1a1b21; color: #a8abb5; font-size: 11px; font-weight: 500; border: none; border-right: 1px solid #292b33; border-bottom: 1px solid #30323b; padding: 6px 8px; }
        QHeaderView::section:checked { background: #343159; color: #c5bdff; }
        QTableCornerButton::section { background: #1a1b21; border: none; }
        QTextEdit { background: #121318; color: #f3f5f8; border: 2px solid #8774df; border-radius: 0; padding: 2px 6px; selection-background-color: #343159; selection-color: #f3f5f8; }
        QScrollBar:vertical, QScrollBar:horizontal { background: #24262e; }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #5b5f6d; border-radius: 2px; }
        QScrollBar::handle:hover { background: #747989; }
        QAbstractScrollArea::corner { background: #24262e; }
    ''')
