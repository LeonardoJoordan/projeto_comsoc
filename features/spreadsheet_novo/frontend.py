"""Apresentação da planilha; preserva os controles e as operações da tabela."""
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout
from shiboken6 import isValid
from pathlib import Path
from features.editor_novo.frontend import icon


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
    title = QLabel('DADOS DO MODELO')
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
        button.setIcon(icon(path))
        button.setIconSize(QSize(18, 18))
        button.setObjectName('sheetAction' if text else 'sheetSquare')
        if not text:
            button.setFixedSize(30, 30)
        actions.addWidget(button)
    actions.addStretch()
    panel.btn_toggle_wrap.setText('Quebrar texto')
    panel.btn_toggle_wrap.setIcon(icon('<path d="M4 6h16M4 11h12a4 4 0 0 1 0 8h-4m3-3-3 3 3 3M4 16h3"/>'))
    panel.btn_toggle_wrap.setObjectName('sheetAction')
    actions.addWidget(panel.btn_toggle_wrap)
    layout.addWidget(toolbar)

    hint = QLabel('Cole seus dados na tabela • Duplo clique para editar')
    hint.setObjectName('sheetHint')
    layout.addWidget(hint)
    table = panel.table
    table.setObjectName('dataGrid')
    table.verticalHeader().setDefaultSectionSize(34)
    table.verticalHeader().setMinimumWidth(38)
    table.horizontalHeader().setMinimumSectionSize(64)
    table.horizontalHeader().setDefaultSectionSize(150)
    table.horizontalHeader().setFixedHeight(36)
    table.setCornerButtonEnabled(False)
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
    '''.replace('__ICONS__', (Path(__file__).resolve().parents[1] / 'editor_novo' / 'icons').as_posix()))
