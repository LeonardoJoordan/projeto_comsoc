"""Identidade visual do workspace de transição, inspirada no editor_novo."""
from PySide6.QtCore import Qt


STYLE = """
QMainWindow, QWidget { background: #1a1b21; color: #f3f5f8; font-size: 12px; }
QMainWindow { background: #0f1014; }
QWidget#workspaceRoot { background: #0f1014; }
QWidget#workspaceLeft, QWidget#previewPanel, QWidget#dataPanel,
QWidget#outputPanel, QWidget#modelActions {
    background: #15161b; border: 1px solid #30323b; border-radius: 8px;
}
QWidget#previewPanel, QWidget#dataPanel { padding: 10px; }
QLabel { background: transparent; }
QPushButton {
    background: #22232b; color: #f3f5f8; border: 1px solid #30323b;
    border-radius: 6px; padding: 7px 10px; min-height: 20px;
}
QPushButton:hover { background: #2a2c35; border-color: #454854; }
QPushButton:pressed, QPushButton:checked { background: #343159; border-color: #7c73f2; }
QPushButton:disabled { color: #777b87; background: #1a1b21; }
QPushButton#primary { background: #7c73f2; border-color: #7c73f2; color: white; font-weight: 600; }
QPushButton#primary:hover { background: #8c84f6; }
QPushButton#danger { color: #ef8d8d; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background: #121318; color: #f3f5f8; border: 1px solid #30323b;
    border-radius: 5px; padding: 5px; min-height: 20px;
    selection-background-color: #343159;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border-color: #7c73f2;
}
QComboBox::drop-down { border: none; width: 24px; }
QTableWidget {
    background: #121318; alternate-background-color: #17181e; color: #f3f5f8;
    border: 1px solid #30323b; border-radius: 6px; gridline-color: #292b33;
    selection-background-color: #343159; selection-color: #ffffff;
}
QHeaderView::section {
    background: #22232b; color: #c9cbd3; border: none;
    border-right: 1px solid #30323b; border-bottom: 1px solid #30323b;
    padding: 7px; font-weight: 600;
}
QProgressBar { background: #22232b; border: none; border-radius: 4px; }
QProgressBar::chunk { background: #7c73f2; border-radius: 4px; }
QSplitter::handle { background: #30323b; width: 1px; }
QScrollBar:vertical { background: #24262e; width: 8px; margin: 0; }
QScrollBar:horizontal { background: #24262e; height: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #5b5f6d; min-height: 24px; border-radius: 2px; }
QScrollBar::handle:horizontal { background: #5b5f6d; min-width: 24px; border-radius: 2px; }
QScrollBar::handle:hover { background: #747989; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QToolTip { background: #22232b; color: #f3f5f8; border: 1px solid #454854; padding: 6px; }
"""


def install_frontend(window):
    window.resize(1440, 860)
    central = window.centralWidget()
    central.setObjectName('workspaceRoot')
    layout = central.layout()
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(0)

    window.preview_panel.setObjectName('previewPanel')
    window.controls_panel.setObjectName('modelActions')
    window.table_panel.setObjectName('dataPanel')
    window.controls_panel.setFixedWidth(132)
    window.splitter.setHandleWidth(12)
    window.splitter.setSizes([680, 760])

    buttons = window.controls_panel
    button_labels = (
        (buttons.btn_add_model, 'Novo modelo'),
        (buttons.btn_duplicate_model, 'Duplicar'),
        (buttons.btn_remove_model, 'Remover'),
        (buttons.btn_rename_model, 'Renomear'),
        (buttons.btn_config_model, 'Editar modelo'),
        (buttons.btn_import_models, 'Importar'),
        (buttons.btn_export_models, 'Exportar'),
    )
    for button, label in button_labels:
        button.setText(label)
        button.setMinimumHeight(38)
    buttons.btn_add_model.setObjectName('primary')
    buttons.btn_remove_model.setObjectName('danger')
    window.btn_generate_cards.setObjectName('primary')
    window.btn_generate_cards.setMinimumHeight(42)
    window.progress_bar.setStyleSheet('')

    # A seleção de tecnologia pertence somente ao workspace antigo.
    window.preview_panel.cbo_editor.hide()
    window.table_panel.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    # Aplicar por último faz os seletores por objectName entrarem em vigor.
    window.setStyleSheet(STYLE)
