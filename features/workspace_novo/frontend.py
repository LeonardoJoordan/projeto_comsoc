"""Identidade visual do workspace de transição, inspirada no editor_novo."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QToolButton, QHBoxLayout, QVBoxLayout,
    QMessageBox, QMenu,
)


STYLE = """
QMainWindow, QWidget { background: #1a1b21; color: #f3f5f8; font-size: 12px; }
QMainWindow { background: #0f1014; }
QWidget#workspaceRoot { background: #0f1014; }
QWidget#workspaceLeft, QWidget#previewPanel, QWidget#dataPanel,
QWidget#outputPanel, QWidget#modelActions {
    background: #15161b; border: 1px solid #30323b; border-radius: 8px;
}
QFrame#modelBar, QFrame#logHeader { background: #15161b; border-bottom: 1px solid #30323b; }
QLabel#contextLabel { color: #8f939f; font-size: 10px; font-weight: 600; }
QToolButton#moreActions { background: #22232b; border: 1px solid #30323b; border-radius: 6px; padding: 7px 10px; }
QMenuBar { background: #101116; color: #d8dae2; padding: 3px 8px; border-bottom: 1px solid #30323b; }
QMenuBar::item { padding: 6px 10px; border-radius: 4px; }
QMenuBar::item:selected { background: #2a2c35; }
QMenu { background: #22232b; color: #f3f5f8; border: 1px solid #454854; padding: 6px; }
QMenu::item { padding: 8px 28px; border-radius: 4px; }
QMenu::item:selected { background: #343159; }
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
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    window.preview_panel.setObjectName('previewPanel')
    window.controls_panel.setObjectName('modelActions')
    window.table_panel.setObjectName('dataPanel')
    window.splitter.setHandleWidth(12)

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

    # Retira a antiga coluna de botões e coloca a prévia diretamente no divisor.
    old_left = window.splitter.replaceWidget(0, window.preview_panel)
    if old_left:
        old_left.hide()
    window.splitter.setSizes([590, 850])
    preview_layout = window.preview_panel.layout()
    for label in window.preview_panel.findChildren(QLabel, options=Qt.FindChildOption.FindDirectChildrenOnly):
        if label is not window.preview_panel.preview:
            label.hide()

    # Barra permanente do modelo.
    model_bar = QFrame()
    model_bar.setObjectName('modelBar')
    model_row = QHBoxLayout(model_bar)
    model_row.setContentsMargins(14, 10, 14, 10)
    model_row.setSpacing(8)
    context = QLabel('MODELO')
    context.setObjectName('contextLabel')
    model_row.addWidget(context)
    model_row.addWidget(window.preview_panel.cbo_models, 1)
    model_row.addWidget(buttons.btn_add_model)
    model_row.addWidget(buttons.btn_config_model)
    more = QToolButton()
    more.setObjectName('moreActions')
    more.setText('Mais ações  ⋮')
    more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    model_actions = QMenu(more)
    for label, button in (
        ('Duplicar modelo', buttons.btn_duplicate_model),
        ('Renomear modelo', buttons.btn_rename_model),
        ('Importar modelos…', buttons.btn_import_models),
        ('Exportar modelos…', buttons.btn_export_models),
        ('Remover modelo', buttons.btn_remove_model),
    ):
        action = model_actions.addAction(label)
        action.triggered.connect(button.click)
        if label == 'Renomear modelo':
            model_actions.addSeparator()
        if label == 'Exportar modelos…':
            model_actions.addSeparator()
    more.setMenu(model_actions)
    model_row.addWidget(more)

    # Log recolhível, sem roubar espaço durante o trabalho normal.
    log_header = QFrame()
    log_header.setObjectName('logHeader')
    log_row = QHBoxLayout(log_header)
    log_row.setContentsMargins(14, 5, 14, 5)
    log_toggle = QPushButton('›  Mensagens de processamento')
    log_toggle.setObjectName('logToggle')
    log_toggle.setCheckable(True)
    log_toggle.setStyleSheet('text-align: left; background: transparent; border: none;')
    log_row.addWidget(log_toggle)
    window.log_panel.setMaximumHeight(180)
    window.log_panel.hide()
    def toggle_log(opened):
        log_toggle.setText(('⌄  ' if opened else '›  ') + 'Mensagens de processamento')
        window.log_panel.setVisible(opened)
    log_toggle.toggled.connect(toggle_log)

    # Recompõe a tela sem substituir os objetos responsáveis pela lógica.
    while layout.count():
        layout.takeAt(0)
    shell = QWidget()
    shell.setObjectName('workspaceRoot')
    shell_layout = QVBoxLayout(shell)
    shell_layout.setContentsMargins(14, 0, 14, 14)
    shell_layout.setSpacing(8)
    shell_layout.addWidget(model_bar)
    shell_layout.addWidget(window.splitter, 1)
    shell_layout.addWidget(log_header)
    shell_layout.addWidget(window.log_panel)
    shell_layout.addWidget(window.footer_container)
    layout.addWidget(shell)

    # Menus conhecidos de aplicativos de criação, reutilizando as ações existentes.
    menu = window.menuBar()
    menu.clear()
    arquivo = menu.addMenu('Arquivo')
    arquivo.addAction('Novo modelo', buttons.btn_add_model.click)
    arquivo.addAction('Importar modelos…', buttons.btn_import_models.click)
    arquivo.addAction('Exportar modelos…', buttons.btn_export_models.click)
    arquivo.addSeparator()
    arquivo.addAction('Sair', window.close)
    modelo = menu.addMenu('Modelo')
    modelo.addAction('Editar modelo', buttons.btn_config_model.click)
    modelo.addAction('Duplicar modelo', buttons.btn_duplicate_model.click)
    modelo.addAction('Renomear modelo', buttons.btn_rename_model.click)
    modelo.addSeparator()
    modelo.addAction('Remover modelo', buttons.btn_remove_model.click)
    dados = menu.addMenu('Dados')
    dados.addAction('Colar', window.table_panel.table._paste_from_clipboard)
    dados.addAction('Adicionar linhas', lambda: window.table_panel.table._add_rows(window.table_panel.spin_add_rows.value()))
    dados.addAction('Duplicar linhas', window.table_panel.table._duplicate_selected_rows)
    dados.addAction('Excluir linhas', window.table_panel.table._delete_selected_rows_action)
    exibir = menu.addMenu('Exibir')
    show_log = exibir.addAction('Mensagens de processamento')
    show_log.setCheckable(True)
    show_log.toggled.connect(log_toggle.setChecked)
    log_toggle.toggled.connect(show_log.setChecked)
    exibir.addAction('Restaurar divisão dos painéis', lambda: window.splitter.setSizes([590, 850]))
    ajuda = menu.addMenu('Ajuda')
    ajuda.addAction('Sobre o COMSOC', lambda: QMessageBox.about(
        window, 'Sobre o COMSOC',
        '<b>COMSOC</b><br>Construtor de materiais gráficos personalizados.<br><br>'
        'Interface desenvolvida com <a href="https://www.qt.io/qt-for-python">Qt for Python (PySide6)</a>.'
    ))
    ajuda.addAction('Licenças de terceiros', lambda: QMessageBox.information(
        window, 'Licenças de terceiros',
        'Este programa utiliza Qt for Python (PySide6), disponibilizado sob opções de licença LGPLv3/GPLv3 ou comercial. '
        'Os textos completos das licenças serão incluídos no pacote de distribuição.'
    ))
    # Mantém wrappers Python vivos durante toda a janela (necessário no PySide).
    window._workspace_menus = (arquivo, modelo, dados, exibir, ajuda, model_actions)
    window._workspace_log_toggle = log_toggle
    # Aplicar por último faz os seletores por objectName entrarem em vigor.
    window.setStyleSheet(STYLE)
