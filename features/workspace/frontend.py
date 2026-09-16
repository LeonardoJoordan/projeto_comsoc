from core.themes import themed_style, theme_color, theme_manager
"""Identidade visual do workspace, compartilhando o padrão do editor."""
import os
import re
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QSize, QProcess
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QToolButton, QHBoxLayout, QVBoxLayout,
    QMessageBox, QMenu, QGridLayout, QSizePolicy, QListView,
)
from core.paths import get_models_dir
from core.resources import action_icon_path, navigation_icon_path
from core.theme_icons import themed_svg_icon
from core.i18n import SUPPORTED_LANGUAGES, current_locale, set_preferred_locale, tr


def _restart_application(window):
    """Inicia uma nova instância e encerra a atual após confirmar o processo."""
    if getattr(sys, "frozen", False):
        program = sys.executable
        arguments = sys.argv[1:]
    else:
        program = sys.executable
        arguments = [str(Path(sys.argv[0]).resolve()), *sys.argv[1:]]

    result = QProcess.startDetached(program, arguments, os.getcwd())
    started = result[0] if isinstance(result, tuple) else bool(result)
    if started:
        window.close()
        return

    QMessageBox.critical(
        window,
        tr('Não foi possível reiniciar'),
        tr('Feche e abra o FORNAX Forge para aplicar o novo idioma.'),
    )


STYLE = """
QMainWindow, QWidget { background: @surface@; color: @text@; font-size: 12px; }
QMainWindow { background: @window@; }
QWidget#workspaceRoot { background: @window@; }
QWidget#workspaceLeft, QWidget#previewPanel, QWidget#dataPanel,
QWidget#modelActions {
    background: @panel@; border: none; border-radius: 0;
}
QWidget#previewWorkspace { background: @panel@; }
QWidget#outputPanel {
    background: @panel@; border: none; border-top: 1px solid @grid@;
    border-radius: 0;
}
QWidget#logPanel {
    background: @panel@; border: none; border-top: 1px solid @grid@;
}
QFrame#dataRail {
    background: @panel@; border: none; border-radius: 0;
}
QToolButton#dataRailToggle {
    background: @alternate@; color: @muted@; border: none;
    border-right: 1px solid @grid@; border-radius: 0; padding: 0; font-size: 15px;
}
QToolButton#dataRailToggle:hover { background: @selection@; color: @on_accent@; border-right-color: @accent@; }
QFrame#modelBar, QFrame#logHeader { background: @panel@; border-bottom: 1px solid @grid@; }
QWidget#outputControls { background: transparent; }
QLabel#contextLabel { color: @muted@; font-size: 10px; font-weight: 600; }
QToolButton#moreActions { background: @button@; border: 1px solid @border@; border-radius: 6px; padding: 7px 10px; }
QToolButton#moreActions::menu-indicator { image: none; }
QMenuBar { background: @window@; color: @text@; padding: 3px 8px; border-bottom: 1px solid @grid@; }
QMenuBar::item { padding: 6px 10px; border-radius: 4px; }
QMenuBar::item:selected { background: @hover@; }
QMenu { background: @button@; color: @text@; border: 1px solid @border_strong@; padding: 6px; }
QMenu::item { padding: 8px 28px; border-radius: 4px; }
QMenu::item:selected { background: @selection@; }
QMenu::separator { height: 1px; background: @border_strong@; margin: 8px 8px; }
QWidget#previewPanel, QWidget#dataPanel { padding: 10px; }
QLabel { background: transparent; }
QPushButton {
    background: @button@; color: @text@; border: 1px solid @border@;
    border-radius: 6px; padding: 7px 10px; min-height: 20px;
}
QPushButton:hover { background: @hover@; border-color: @border_strong@; }
QPushButton:pressed, QPushButton:checked { background: @selection@; border-color: @accent@; }
QPushButton:disabled { color: @disabled@; background: @surface@; }
QPushButton#primary { background: @accent@; border-color: @accent@; color: @on_accent@; font-weight: 600; }
QPushButton#primary:hover { background: @accent_hover@; }
QPushButton#danger { color: @danger@; }
QPushButton#previewPrevious, QPushButton#previewNext {
    min-height: 0; padding: 0; border-radius: 5px; font-size: 15px;
}
QPushButton#previewPageButton {
    min-height: 0; padding: 0 8px; border-radius: 5px;
}
QPushButton#previewPageButton:checked {
    background: @selection@; border-color: @accent@;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background: @field@; color: @text@; border: 1px solid @border@;
    border-radius: 5px; padding: 5px; min-height: 20px;
    selection-background-color: @selection@;
}
QSpinBox#previewNavigationIndex, QComboBox#previewMode {
    min-height: 0; padding-top: 0; padding-bottom: 0;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border-color: @accent@;
}
QComboBox:hover { border-color: @border_strong@; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { image: url(@combo_arrow@); width: 10px; height: 6px; }
QListView#workspaceComboOptions {
    background: @button@; color: @text@; border: 1px solid @border_strong@;
    border-radius: 8px; padding: 6px; outline: none;
    selection-background-color: transparent;
}
QListView#workspaceComboOptions::item {
    min-height: 20px; padding: 8px 12px; border: 1px solid transparent;
    border-radius: 5px; background: transparent;
}
QListView#workspaceComboOptions::item:selected,
QListView#workspaceComboOptions::item:hover {
    background: @selection@; border-color: @accent@; color: @text@;
}
QTableWidget {
    background: @field@; alternate-background-color: @alternate@; color: @text@;
    border: 1px solid @border@; border-radius: 6px; gridline-color: @grid@;
    selection-background-color: @selection@; selection-color: @on_accent@;
}
QHeaderView::section {
    background: @button@; color: @text@; border: none;
    border-right: 1px solid @border@; border-bottom: 1px solid @border@;
    padding: 7px; font-weight: 600;
}
QProgressBar { background: @button@; border: none; border-radius: 4px; }
QProgressBar::chunk { background: @accent@; border-radius: 4px; }
QSplitter::handle { background: @grid@; width: 1px; }
QScrollBar:vertical { background: @scroll_track@; width: 8px; margin: 0; }
QScrollBar:horizontal { background: @scroll_track@; height: 8px; margin: 0; }
QScrollBar::handle:vertical { background: @scroll_handle@; min-height: 24px; border-radius: 2px; }
QScrollBar::handle:horizontal { background: @scroll_handle@; min-width: 24px; border-radius: 2px; }
QScrollBar::handle:hover { background: @scroll_hover@; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QToolTip { background: @button@; color: @text@; border: 1px solid @border_strong@; padding: 6px; }
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
    window.splitter.setHandleWidth(1)

    buttons = window.controls_panel
    button_labels = (
        (buttons.btn_add_model, tr('Novo modelo'), tr('Criar um modelo em branco')),
        (buttons.btn_duplicate_model, tr('Duplicar'), tr('Duplicar o modelo selecionado')),
        (buttons.btn_remove_model, tr('Remover'), tr('Excluir o modelo selecionado')),
        (buttons.btn_rename_model, tr('Renomear'), tr('Renomear o modelo selecionado')),
        (buttons.btn_config_model, tr('Editar modelo'), tr('Abrir o modelo selecionado no editor')),
        (buttons.btn_import_models, tr('Importar'), tr('Importar modelos de um pacote ZIP')),
        (buttons.btn_export_models, tr('Exportar'), tr('Exportar modelos para um pacote ZIP')),
    )
    for button, label, tooltip in button_labels:
        button.setText(label)
        button.setToolTip(tooltip)
        button.setMinimumHeight(38)
    buttons.btn_add_model.setObjectName('primary')
    buttons.btn_remove_model.setObjectName('danger')
    window.btn_generate_cards.setObjectName('primary')
    window.btn_generate_cards.setMinimumHeight(42)
    themed_style(window.progress_bar, '')

    window.table_panel.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # Popups consistentes com o menu de Formas do editor.
    workspace_combos = (
        window.preview_panel.cbo_models,
        window.preview_panel.cbo_preview_mode,
        window.cbo_export_format,
        window.cbo_presets_main,
    )
    for combo in workspace_combos:
        popup = QListView(combo)
        popup.setObjectName('workspaceComboOptions')
        popup.setMouseTracking(True)
        popup.setUniformItemSizes(True)
        combo.setMaxVisibleItems(12)
        combo.setView(popup)

    # Retira a antiga coluna de botões e coloca a prévia diretamente no divisor.
    old_left = window.splitter.replaceWidget(0, window.preview_panel)
    if old_left:
        old_left.hide()
    window.splitter.setSizes([590, 850])
    preview_layout = window.preview_panel.layout()
    for label in window.preview_panel.findChildren(QLabel, options=Qt.FindChildOption.FindDirectChildrenOnly):
        if label is not window.preview_panel.preview and label.objectName() != 'previewNavigationLabel':
            label.hide()

    # Barra permanente do modelo.
    model_bar = QFrame()
    model_bar.setObjectName('modelBar')
    model_row = QHBoxLayout(model_bar)
    model_row.setContentsMargins(14, 10, 14, 10)
    model_row.setSpacing(8)
    context = QLabel(tr('MODELO'))
    context.setObjectName('contextLabel')
    model_row.addWidget(context)
    window.preview_panel.cbo_models.setMinimumWidth(100)
    window.preview_panel.cbo_models.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    model_row.addWidget(window.preview_panel.cbo_models, 1)
    model_row.addWidget(buttons.btn_config_model)
    more = QToolButton()
    more.setObjectName('moreActions')
    more.setText('')
    more.setIcon(themed_svg_icon(action_icon_path('more-vertical')))
    more.setIconSize(QSize(18, 18))
    more.setFixedWidth(38)
    more.setToolTip(tr('Mais ações do modelo'))
    more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    model_actions = QMenu(more)
    delete_action = None
    for action_id, label, button in (
        ('duplicate', tr('Duplicar modelo'), buttons.btn_duplicate_model),
        ('rename', tr('Renomear modelo'), buttons.btn_rename_model),
        ('delete', tr('Excluir modelo'), buttons.btn_remove_model),
    ):
        if action_id == 'delete':
            model_actions.addAction(
                tr('Informações do modelo…'), window._open_model_info_dialog
            )
            model_actions.addSeparator()
        action = model_actions.addAction(label)
        action.triggered.connect(button.click)
        if action_id == 'delete':
            delete_action = action
    def style_model_action_hover(action):
        if action is delete_action:
            themed_style(model_actions, 'QMenu::item:selected { background: @danger_background@; color: @on_danger@; }')
        else:
            themed_style(model_actions, '')
    model_actions.hovered.connect(style_model_action_hover)
    more.setMenu(model_actions)
    model_row.addWidget(more)
    for control in (window.preview_panel.cbo_models, buttons.btn_config_model, more):
        control.setFixedHeight(38)

    # As ações de saída ficam próximas, mesmo em uma tela ultrawide.
    # Reparentar os controles conserva suas conexões e os valores selecionados.
    output_controls = QWidget()
    output_controls.setObjectName('outputControls')
    output_grid = QGridLayout(output_controls)
    output_grid.setContentsMargins(0, 0, 0, 0)
    output_grid.setHorizontalSpacing(8)
    output_grid.setVerticalSpacing(8)
    destination = QHBoxLayout()
    destination.setSpacing(8)
    destination.addWidget(QLabel(tr('Salvar em')))
    destination.addWidget(window.txt_output_path, 1)
    window.txt_output_path.setPlaceholderText(tr('Escolha a pasta de destino dos arquivos'))
    window.btn_sel_out.setText('')
    window.btn_sel_out.setIcon(themed_svg_icon(action_icon_path('more')))
    window.btn_sel_out.setIconSize(QSize(18, 18))
    window.btn_sel_out.setToolTip(tr('Escolher a pasta de destino'))
    destination.addWidget(window.btn_sel_out)
    output_grid.addLayout(destination, 0, 0, 1, 5)
    output_grid.addWidget(window.cbo_export_format, 1, 0)
    export_tooltips = {
        'png': tr('Uma imagem PNG para cada item.'),
        'pdf_item': tr('Um arquivo PDF separado para cada item.'),
        'pdf_grouped': tr('Todos os itens reunidos em um único arquivo PDF.'),
    }
    for index in range(window.cbo_export_format.count()):
        mode = window.cbo_export_format.itemData(index)
        window.cbo_export_format.setItemData(index, export_tooltips[mode], Qt.ItemDataRole.ToolTipRole)
    window.cbo_export_format.setToolTip(tr('Selecionar o formato dos arquivos gerados'))
    window.cbo_presets_main.setMinimumWidth(100)
    window.cbo_presets_main.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    window.cbo_presets_main.setToolTip(tr('Selecionar uma predefinição de impressão'))
    output_grid.addWidget(window.cbo_presets_main, 1, 1, 1, 3)
    output_grid.setColumnStretch(1, 1)
    window.btn_generate_cards.setFixedWidth(140)
    window.btn_generate_cards.setFixedHeight(42)
    window.btn_generate_cards.setToolTip(tr('Gerar os arquivos usando os dados da tabela'))
    output_grid.addWidget(window.btn_generate_cards, 1, 4, 1, 1, Qt.AlignmentFlag.AlignVCenter)
    for control in (window.txt_output_path, window.btn_sel_out, window.cbo_export_format,
                    window.cbo_presets_main):
        control.setFixedHeight(34)

    # Remove somente a estrutura visual antiga, já sem os controles reutilizados.
    def clear_layout(old_layout):
        while old_layout.count():
            item = old_layout.takeAt(0)
            if item.layout():
                clear_layout(item.layout())
            elif item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    footer_layout = window.footer_container.layout()
    clear_layout(footer_layout)
    footer_layout.setContentsMargins(14, 12, 14, 12)
    footer_layout.setSpacing(0)
    footer_layout.addWidget(output_controls, 1)
    footer_layout.addStretch(0)

    # O log fica oculto durante o trabalho normal e é acessado pelo menu Exibir.
    window.log_panel.setMaximumHeight(180)
    window.log_panel.setObjectName('logPanel')
    window.log_panel.hide()
    def toggle_log(opened):
        window.log_panel.setVisible(opened)

    # A seleção, a prévia e a saída formam uma única área de trabalho.
    preview_workspace = QWidget()
    preview_workspace.setObjectName('previewWorkspace')
    preview_workspace.setMinimumWidth(500)
    preview_workspace_layout = QVBoxLayout(preview_workspace)
    preview_workspace_layout.setContentsMargins(0, 0, 0, 0)
    preview_workspace_layout.setSpacing(0)
    preview_workspace_layout.addWidget(model_bar)
    preview_workspace_layout.addWidget(window.preview_panel, 1)
    preview_workspace_layout.addWidget(window.log_panel)
    preview_workspace_layout.addWidget(window.footer_container)
    preview_workspace_layout.addWidget(window.progress_bar)

    # A tabela vive em um painel lateral que pode virar apenas uma barra estreita.
    data_rail = QFrame()
    data_rail.setObjectName('dataRail')
    data_rail_layout = QHBoxLayout(data_rail)
    data_rail_layout.setContentsMargins(0, 0, 0, 0)
    data_rail_layout.setSpacing(0)
    data_toggle = QToolButton()
    data_toggle.setObjectName('dataRailToggle')
    data_toggle.setFixedWidth(38)
    data_toggle.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
    data_toggle.setToolTip(tr('Recolher tabela de dados'))
    data_rail_layout.addWidget(data_toggle)
    data_rail_layout.addWidget(window.table_panel, 1)

    window.splitter.addWidget(preview_workspace)
    window.splitter.addWidget(data_rail)
    window.splitter.setCollapsible(0, False)
    window.splitter.setCollapsible(1, False)
    window.splitter.setSizes([700, 700])

    panel_state = {'expanded_width': 700, 'collapsed': False, 'fixed': False}

    def refresh_data_toggle_icon():
        asset_name = (
            'double-chevron-left' if panel_state['collapsed']
            else 'double-chevron-right'
        )
        data_toggle.setText('')
        data_toggle.setIcon(themed_svg_icon(navigation_icon_path(asset_name)))
        data_toggle.setIconSize(QSize(20, 20))

    def set_data_panel_collapsed(collapsed):
        collapsed = bool(collapsed)
        if collapsed and panel_state['fixed']:
            return
        if collapsed == panel_state['collapsed']:
            return
        if collapsed:
            sizes = window.splitter.sizes()
            if len(sizes) > 1 and sizes[1] > 60:
                panel_state['expanded_width'] = sizes[1]
            window.table_panel.hide()
            data_toggle.setToolTip(tr('Expandir tabela de dados'))
            data_rail.setMinimumWidth(38)
            data_rail.setMaximumWidth(38)
            window.splitter.setSizes([max(500, sum(sizes) - 38), 38])
        else:
            data_rail.setMinimumWidth(420)
            data_rail.setMaximumWidth(16777215)
            window.table_panel.show()
            data_toggle.setToolTip(tr('Recolher tabela de dados'))
            total = max(1000, sum(window.splitter.sizes()))
            right = min(max(420, panel_state['expanded_width']), total - 500)
            window.splitter.setSizes([total - right, right])
        panel_state['collapsed'] = collapsed
        refresh_data_toggle_icon()
        window.settings.setValue('workspaceDataPanelCollapsed', collapsed)

    data_toggle.clicked.connect(lambda: set_data_panel_collapsed(not panel_state['collapsed']))
    refresh_data_toggle_icon()
    theme_manager().changed.connect(refresh_data_toggle_icon)

    # Recompõe a tela sem substituir os objetos responsáveis pela lógica.
    while layout.count():
        layout.takeAt(0)
    shell = QWidget()
    shell.setObjectName('workspaceRoot')
    shell_layout = QVBoxLayout(shell)
    shell_layout.setContentsMargins(0, 0, 0, 0)
    shell_layout.setSpacing(0)
    shell_layout.addWidget(window.splitter, 1)
    layout.addWidget(shell)

    # Menus conhecidos de aplicativos de criação, reutilizando as ações existentes.
    menu = window.menuBar()
    menu.clear()
    programa = menu.addMenu(tr('Programa'))
    programa.addAction(tr('Configuração de exportação…'), window._open_config_dialog)
    programa.addAction(tr('Temas…'), window._open_theme_dialog)
    idioma = programa.addMenu(tr('Idioma'))
    language_group = QActionGroup(idioma)
    language_group.setExclusive(True)
    for locale, native_name in SUPPORTED_LANGUAGES:
        language_action = idioma.addAction(native_name)
        language_action.setCheckable(True)
        language_action.setChecked(locale == current_locale())
        language_group.addAction(language_action)
        def choose_language(_checked=False, selected=locale):
            set_preferred_locale(window.settings, selected)
            if selected == current_locale():
                return
            prompt = QMessageBox(window)
            prompt.setIcon(QMessageBox.Icon.Question)
            prompt.setWindowTitle(tr('Reiniciar o programa'))
            prompt.setText(tr('Reinicie o programa para aplicar o novo idioma.'))
            restart_now = prompt.addButton(
                tr('Reiniciar agora'), QMessageBox.ButtonRole.AcceptRole
            )
            prompt.addButton(
                tr('Reiniciar depois'), QMessageBox.ButtonRole.RejectRole
            )
            prompt.setDefaultButton(restart_now)
            prompt.exec()
            if prompt.clickedButton() is restart_now:
                _restart_application(window)
        language_action.triggered.connect(choose_language)
    modelo = menu.addMenu(tr('Modelo'))
    modelo.addAction(tr('Novo modelo'), buttons.btn_add_model.click)
    modelo.addAction(tr('Importar modelos…'), buttons.btn_import_models.click)
    modelo.addAction(tr('Exportar modelos…'), buttons.btn_export_models.click)
    modelo.addSeparator()
    modelo.addAction(
        tr('Abrir pasta de modelos'),
        lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(get_models_dir())))
    )
    exibir = menu.addMenu(tr('Exibir'))
    show_log = exibir.addAction(tr('Log de processamento'))
    show_log.setCheckable(True)
    show_log.toggled.connect(toggle_log)
    fixed_data = exibir.addAction(tr('Tabela de dados fixa'))
    fixed_data.setCheckable(True)
    def set_data_panel_fixed(fixed):
        panel_state['fixed'] = bool(fixed)
        if fixed:
            set_data_panel_collapsed(False)
        data_toggle.setVisible(not fixed)
        if not fixed:
            data_toggle.setToolTip(
                tr('Expandir tabela de dados') if panel_state['collapsed'] else tr('Recolher tabela de dados')
            )
        window.settings.setValue('workspaceDataPanelFixed', bool(fixed))
    fixed_data.toggled.connect(set_data_panel_fixed)
    ajuda = menu.addMenu(tr('Sobre'))
    ajuda.addAction(tr('Sobre o FORNAX Forge'), lambda: QMessageBox.about(
        window, tr('Sobre o FORNAX Forge'),
        tr('<b>FORNAX Forge</b><br>Geração de material personalizado em lote.<br><br>'
           'Interface desenvolvida com <a href="https://www.qt.io/qt-for-python">Qt for Python (PySide6)</a>.')
    ))
    ajuda.addAction(tr('Licenças de terceiros'), lambda: QMessageBox.information(
        window, tr('Licenças de terceiros'),
        tr('Este programa utiliza Qt for Python (PySide6), disponibilizado sob opções de licença LGPLv3/GPLv3 ou comercial. '
           'Os textos completos das licenças serão incluídos no pacote de distribuição.')
    ))
    # Mantém wrappers Python vivos durante toda a janela (necessário no PySide).
    window._workspace_menus = (
        programa, idioma, language_group, modelo, exibir, ajuda, model_actions,
    )
    window._workspace_log_toggle = show_log
    window._workspace_data_toggle = data_toggle
    window._workspace_data_fixed_action = fixed_data
    window._workspace_data_rail = data_rail
    data_panel_fixed = window.settings.value('workspaceDataPanelFixed', False, type=bool)
    if data_panel_fixed:
        fixed_data.setChecked(True)
    elif window.settings.value('workspaceDataPanelCollapsed', False, type=bool):
        set_data_panel_collapsed(True)
    combo_arrow = (Path(__file__).resolve().parent / 'icons' / 'combo-down.svg').as_posix()
    themed_style(window, STYLE)
