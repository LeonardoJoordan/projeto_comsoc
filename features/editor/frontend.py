from core.themes import themed_style, theme_color, theme_manager
"""Apresentação Widgets independente; reutiliza controles e sinais do legado."""
from pathlib import Path
from core.resources import object_icon_path, state_icon_path
from PySide6.QtCore import Qt, QSize, QObject, QEvent, QPoint, QTimer
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter
from .canvas_items import mm_to_px, px_to_mm
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSplitter, QFrame, QLineEdit, QAbstractSpinBox, QColorDialog,
    QCheckBox, QDoubleSpinBox, QComboBox, QMenu, QRadioButton, QSizePolicy, QListView,
    QGridLayout,
)


STYLE = """
QWidget { background: @surface@; color: @text@; font-size: 12px; }
QMainWindow, QWidget#root { background: @window@; }
QFrame#footer { background: @window@; border: none; }
QLabel { background: transparent; }
QLabel#muted { color: @muted@; }
QFrame#bar { background: @panel@; border-bottom: 1px solid @border@; }
QFrame#compact { background: @field@; border: 1px solid @border@; border-radius: 6px; }
QFrame#compact QAbstractSpinBox { border: none; background: transparent; padding: 0; min-height: 0; font-size: 11px; }
QFrame#compact QLabel { color: @disabled@; font-size: 10px; }
QPushButton { background: @button@; border: 1px solid @border@;
 border-radius: 6px; padding: 6px 10px; min-height: 20px; }
QPushButton:hover { background: @hover@; border-color: @border_strong@; }
QPushButton:checked { background: @selection@; border-color: @accent@; }
QPushButton:disabled { color: @disabled@; background: @surface@; }
QPushButton#primary { background: @accent@; color: @on_accent@; border: none; }
QPushButton[squareControl="true"] {
 padding: 0; min-width: 28px; max-width: 28px;
 min-height: 28px; max-height: 28px; border: 1px solid @border@;
}
QPushButton#section { text-align: left; background: @panel@;
 border: none; border-bottom: 1px solid @border@; border-radius: 0;
 padding: 12px; font-weight: 600; }
QLineEdit, QAbstractSpinBox, QComboBox, QTextEdit { background: @field@;
 border: 1px solid @border@; border-radius: 5px; padding: 5px; min-height: 20px;
 selection-background-color: @selection@; }
QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus, QTextEdit:focus { border-color: @accent@; }
QSpinBox::up-button, QDoubleSpinBox::up-button {
 subcontrol-origin: border; subcontrol-position: top right; width: 20px;
 background: @border@; border-left: 1px solid @border_strong@; border-bottom: 1px solid @border_strong@;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
 subcontrol-origin: border; subcontrol-position: bottom right; width: 20px;
 background: @border@; border-left: 1px solid @border_strong@;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: @selection@; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url(@spin_up@); width: 10px; height: 6px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url(@spin_down@); width: 10px; height: 6px; }
QSpinBox::up-button:disabled, QDoubleSpinBox::up-button:disabled,
QSpinBox::down-button:disabled, QDoubleSpinBox::down-button:disabled { background: @surface@; }
QWidget:disabled { color: @disabled@; }
QListWidget { background: @surface@; border: none; outline: none; }
QListWidget::item { padding: 7px; border-bottom: 1px solid @border@; }
QListWidget::item:selected { background: @selection@; color: @text@; }
QListWidget#layers::item { padding: 0; border: none; }
QListWidget#layers QWidget { background: transparent; }
QScrollArea { border: none; }
QScrollBar:vertical { background: @scroll_track@; width: 8px; margin: 0; }
QScrollBar:horizontal { background: @scroll_track@; height: 8px; margin: 0; }
QScrollBar::handle:vertical {
 background: @scroll_handle@; min-height: 24px; border-radius: 2px;
}
QScrollBar::handle:horizontal {
 background: @scroll_handle@; min-width: 24px; border-radius: 2px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: @scroll_hover@; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QAbstractScrollArea::corner { background: @scroll_track@; border: none; }
QSplitter::handle { background: @border@; width: 1px; }
QToolTip { background: @button@; color: @text@; border: 1px solid @border_strong@; padding: 6px; }
"""


def icon(path):
    from core.theme_icons import tool_icon
    return tool_icon(path)


def column():
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(10)
    return widget, layout


def square_control(button):
    button.setProperty('squareControl', True)
    button.setFixedSize(30, 30)


def row(layout, *widgets):
    line = QHBoxLayout()
    line.setSpacing(8)
    for widget in widgets:
        line.addWidget(widget)
    layout.addLayout(line)
    return line


def field(name, control):
    widget, layout = column()
    widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    label = QLabel(name)
    label.setObjectName('muted')
    layout.addWidget(label)
    layout.addWidget(control)
    return widget


def compact(name, control, suffix='', width=100):
    widget = QFrame()
    widget.setObjectName('compact')
    widget.setFixedHeight(30)
    if width is not None:
        widget.setFixedWidth(width)
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(8, 0, 7, 0)
    layout.setSpacing(5)
    layout.addWidget(QLabel(name))
    control.setMinimumWidth(0)
    control.setMaximumWidth(16777215)
    control.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    control.setAlignment(Qt.AlignmentFlag.AlignRight)
    control.setAccessibleName(name)
    layout.addWidget(control, 1)
    if suffix:
        layout.addWidget(QLabel(suffix))
    return widget


class FooterSaveAlignment(QObject):
    """Mantém o botão do rodapé centralizado sob o inspetor lateral."""
    def __init__(self, window, sidebar, footer_bar, footer_layout, button):
        super().__init__(window)
        self.window = window
        self.sidebar = sidebar
        self.footer_bar = footer_bar
        self.footer_layout = footer_layout
        self.button = button
        self._update_pending = False
        for watched in (window, sidebar, footer_bar):
            watched.installEventFilter(self)

    def schedule(self):
        if self._update_pending:
            return
        self._update_pending = True
        QTimer.singleShot(0, self.align)

    def align(self):
        self._update_pending = False
        if not self.sidebar.isVisible() or self.footer_bar.width() <= 0:
            return
        sidebar_center_global = self.sidebar.mapToGlobal(
            QPoint(self.sidebar.width() // 2, 0)
        )
        sidebar_center = self.footer_bar.mapFromGlobal(sidebar_center_global).x()
        right_margin = round(
            self.footer_bar.width() - sidebar_center - self.button.width() / 2
        )
        self.footer_layout.setContentsMargins(14, 5, max(14, right_margin), 5)
        self.footer_layout.activate()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.schedule()
        return False


class Section(QWidget):
    def __init__(self, title, content, expanded=False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = QPushButton()
        self.header.setObjectName('section')
        self.header.setCheckable(True)
        self.header.setChecked(expanded)
        layout.addWidget(self.header)
        layout.addWidget(content)
        def toggle(opened):
            self.header.setText(('⌄  ' if opened else '›  ') + title.upper())
            content.setVisible(opened)
        self.header.toggled.connect(toggle)
        toggle(expanded)


def install_frontend(w):
    # Keep old containers alive: existing handlers still reference their controls.
    old = w.takeCentralWidget()
    old.setParent(w)
    old.hide()
    w._original_ui = old
    for child in old.findChildren(QWidget):
        themed_style(child, '')
    themed_style(w, STYLE.replace('__ICONS__', (Path(__file__).parent / 'icons').as_posix()))
    w.resize(1500, 930)
    root, outer = column()
    root.setObjectName('root')
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    w.setCentralWidget(root)

    header = QFrame()
    header.setObjectName('bar')
    header.setFixedHeight(64)
    h = QHBoxLayout(header)
    h.addStretch()
    model_title = QLabel(w._current_model_name or 'Novo modelo')
    model_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    themed_style(model_title, 'font-size: 16px; font-weight: 600;')
    w.windowTitleChanged.connect(
        lambda _, label=model_title: label.setText(w._current_model_name or 'Novo modelo')
    )
    h.addWidget(model_title)
    h.addStretch()
    w.btn_save.setObjectName('primary')
    outer.addWidget(header)

    p = w.caixa_texto_panel
    toolbar = QFrame()
    toolbar.setObjectName('bar')
    tools = QHBoxLayout(toolbar)
    tools.setContentsMargins(14, 8, 14, 8)
    tools.setSpacing(8)
    selection = QLabel('SELEÇÃO\nNenhum objeto')
    selection.setFixedWidth(138)
    themed_style(selection, 'color: @muted@; font-size: 10px;')
    tools.addWidget(selection)
    def toolbar_separator():
        # O layout já fornece 8 px externamente; os 12 px internos completam
        # os 20 px de respiro desejados em cada lado da linha de 1 px.
        spacing = QWidget()
        spacing.setFixedSize(25, 24)
        themed_style(spacing, 'background: transparent;')
        separator = QFrame(spacing)
        separator.setObjectName('toolbarSeparator')
        separator.setGeometry(12, 0, 1, 24)
        themed_style(separator, 'QFrame#toolbarSeparator { background: @border@; border: none; }')
        tools.addWidget(spacing)
    moved = [p.spin_w, p.spin_h, p.chk_proporcao, p.spin_rot, p.spin_opacity]
    for name, control in [('X', w.spin_pos_x), ('Y', w.spin_pos_y), ('L', p.spin_w), ('A', p.spin_h)]:
        if name == 'L':
            toolbar_separator()
        tools.addWidget(compact(name, control, 'mm'))
    p.chk_proporcao.setText('')
    p.chk_proporcao.setIcon(icon('<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2"/>'))
    p.chk_proporcao.setFixedSize(30, 30)
    p._refresh_proportion_button(p.isEnabled())
    tools.addWidget(p.chk_proporcao)
    toolbar_separator()
    tools.addWidget(compact('↻', p.spin_rot, '°', 78))
    tools.addWidget(compact('Op.', p.spin_opacity, '%', 88))
    toolbar_separator()
    guide_label = QLabel('GUIAS')
    guide_label.setObjectName('muted')
    tools.addWidget(guide_label)
    for vertical, label, asset_name in [
        (False, 'Adicionar guia horizontal', 'h.guide'),
        (True, 'Adicionar guia vertical', 'v.guide'),
    ]:
        button = QPushButton()
        button.setIcon(QIcon(str(state_icon_path(asset_name))))
        button.setIconSize(QSize(20, 20))
        button.setFixedSize(30, 30)
        themed_style(button, 'padding: 0;')
        button.setToolTip(label)
        button.clicked.connect(lambda checked=False, v=vertical: w.add_guide(v))
        tools.addWidget(button)
    for button, asset_name, tip in (
        (w.btn_toggle_guides, 'guide', 'Exibir ou ocultar guias'),
        (w.btn_lock_guides, 'l.guide', 'Bloquear ou desbloquear a movimentação das guias'),
    ):
        button.setText('')
        button.setIcon(QIcon(str(state_icon_path(asset_name))))
        button.setIconSize(QSize(20, 20))
        button.setToolTip(tip)
        themed_style(button, 'QPushButton { padding: 0; min-width: 28px; max-width: 28px; '
                            'min-height: 28px; max-height: 28px; font-size: 14px; }')
        button.setFixedSize(30, 30)
        tools.addWidget(button)
    toolbar_separator()
    for button, symbol, tip in (
        (w.btn_undo, '↶', 'Desfazer'),
        (w.btn_redo, '↷', 'Refazer'),
    ):
        button.setText(symbol)
        button.setToolTip(tip)
        button.setMinimumSize(0, 0)
        button.setMaximumSize(16777215, 16777215)
        themed_style(button, 'padding: 0; font-size: 16px;')
        button.setFixedSize(30, 30)
        tools.addWidget(button)
    tools.addStretch()
    fit = QPushButton('Ajustar à janela')
    fit.setFixedSize(116, 34)
    fit.clicked.connect(w._zoom_to_fit)
    tools.addWidget(fit)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(toolbar)
    scroll.setFixedHeight(54)
    outer.addWidget(scroll)

    split = QSplitter(Qt.Orientation.Horizontal)
    outer.addWidget(split, 1)
    left, ll = column()
    left.setMinimumWidth(220)
    ll.addWidget(QLabel('ADICIONAR AO MODELO'))
    forms = QPushButton('Formas')
    from .draw_shapes import ShapeDrawing
    w.shape_drawing = ShapeDrawing(w)
    forms.setToolTip('Escolha uma forma e arraste no canvas. Shift restringe proporções ou ângulo; Esc cancela.')
    shape_menu = QMenu(forms)
    shape_menu.setObjectName('shapeMenu')
    themed_style(shape_menu, '''
        QMenu#shapeMenu {
            background-color: @button@;
            border: 1px solid @border_strong@;
            border-radius: 8px;
            padding: 6px;
        }
        QMenu#shapeMenu::item {
            color: @text@;
            background-color: transparent;
            padding: 10px 28px 10px 36px;
            border: 1px solid transparent;
            border-radius: 5px;
        }
        QMenu#shapeMenu::item:selected {
            background-color: @selection@;
            border-color: @accent@;
        }
        QMenu#shapeMenu::icon { left: 10px; }
    ''')
    shape_menu.aboutToShow.connect(lambda: shape_menu.setMinimumWidth(forms.width()))
    for name, kind, path in [('Quadrado', 'rectangle', '<rect x="4" y="4" width="16" height="16"/>'),
                              ('Círculo', 'ellipse', '<circle cx="12" cy="12" r="8"/>'),
                              ('Linha', 'line', '<path d="M4 20 20 4"/>')]:
        action = shape_menu.addAction(icon(path), name)
        action.triggered.connect(lambda checked=False, k=kind: w.shape_drawing.activate(k))
    forms.setMenu(shape_menu)
    for button, label, path, asset_name in [
        (w.btn_add, 'Texto', '<path d="M4 5h16M12 5v15M8 20h8"/>', 'text'),
        (forms, 'Formas', '<rect x="4" y="4" width="16" height="16" rx="3"/>', 'shapes'),
        (w.btn_add_img, 'Imagens', '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m3 16 5-5 5 5 3-3 5 5"/>', 'image'),
        (w.btn_add_sig, 'Assinatura', '<path d="m4 17 3-1L19 4l2 2L9 18l-5 1zM4 22h16"/>', 'signature')]:
        detail = {'Texto': 'Campo dinâmico', 'Formas': 'Preenchimento e borda', 'Imagens': 'Foto, logo ou QR', 'Assinatura': 'Imagem opcional'}[label]
        button.setText('')
        contents = QHBoxLayout(button)
        contents.setContentsMargins(42, 3, 8, 3)
        caption = QLabel(f'<b>{label}</b><br><span style="font-size:9px">{detail}</span>')
        caption.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        contents.addWidget(caption)
        button.setIcon(QIcon(str(object_icon_path(asset_name))) if asset_name else icon(path))
        button.setIconSize(QSize(20, 20))
        button.setObjectName('add' + label)
        # QSS mede a área de conteúdo: 36 + 12 de padding + 2 de borda = 50.
        # Fixar também no estilo evita que o polish restaure o mínimo global.
        themed_style(button, 'QPushButton#' + button.objectName() + ' { '
                            'text-align: left; padding: 6px 10px 6px 12px; '
                            'min-height: 36px; max-height: 36px; }')
        button.setFixedHeight(50)
        ll.addWidget(button)
    layer_heading = QHBoxLayout()
    layer_heading.addWidget(QLabel('CAMADAS'), 1)
    for b, label in [(w.btn_ren_layer, 'Renomear'), (w.btn_dup_layer, 'Duplicar'), (w.btn_del_layer, 'Excluir')]:
        b.setText('')
        b.setToolTip(label)
        b.setMinimumSize(0, 0)
        b.setMaximumSize(16777215, 16777215)
        themed_style(b, '')
        square_control(b)
        paths = {'Renomear': '<path d="m4 17 3-1L19 4l2 2L9 18l-5 1z"/>', 'Duplicar': '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M15 8V4H4v11h4"/>', 'Excluir': '<path d="M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>'}
        b.setIcon(icon(paths[label]))
        layer_heading.addWidget(b)
    ll.addLayout(layer_heading)
    w.layer_list.setObjectName('layers')
    w.layer_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    ll.addWidget(w.layer_list, 1)
    split.addWidget(left)
    def update_canvas_theme():
        w.view.setBackgroundBrush(QColor(theme_color('canvas')))
        from .canvas_items import Guideline, ResizeHandle
        for item in w.scene.items():
            if isinstance(item, Guideline):
                pen = item.pen()
                pen.setColor(QColor(theme_color('warning' if item.isSelected() else 'guide')))
                item.setPen(pen)
            elif isinstance(item, ResizeHandle):
                item.setBrush(QColor(theme_color('handle')))
        w.view.viewport().update()
    theme_manager().changed.connect(update_canvas_theme)
    manager = theme_manager()
    def disconnect_theme():
        from shiboken6 import isValid
        if isValid(manager):
            manager.changed.disconnect(update_canvas_theme)
    w.destroyed.connect(disconnect_theme)
    update_canvas_theme()
    w.view.setFrameShape(QFrame.Shape.NoFrame)
    from .rulers import RulerWorkspace
    w.ruler_workspace = RulerWorkspace(w)
    split.addWidget(w.ruler_workspace)

    inspector, il = column()
    il.setContentsMargins(0, 0, 0, 0)
    il.setSpacing(1)
    props, pl = column()
    shape_color = QLineEdit('#ffffff')
    shape_color.setMaxLength(7)
    fill_alpha = QDoubleSpinBox()
    fill_alpha.setObjectName('shapeFillAlpha')
    fill_alpha.setRange(0, 100)
    fill_alpha.setDecimals(0)
    fill_alpha.setKeyboardTracking(False)
    shape_swatch = QPushButton()
    shape_swatch.setObjectName('shapeFillSwatch')
    square_control(shape_swatch)
    shape_controls, shape_layout = column()
    shape_layout.setContentsMargins(0, 0, 0, 0)
    fill_controls, fill_layout = column()
    fill_layout.setContentsMargins(0, 0, 0, 0)
    fill_heading = QLabel('PREENCHIMENTO')
    fill_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
    themed_style(fill_heading, 'color: @icon@; font-size: 11px; font-weight: 600;')
    fill_layout.addWidget(fill_heading)
    fill_row = row(fill_layout, shape_swatch, shape_color, compact('α', fill_alpha, '%', 85))
    fill_row.setStretch(1, 1)
    shape_layout.addWidget(fill_controls)
    pl.addWidget(shape_controls)
    def set_shape_color(value):
        from .canvas_items import RectangleItem
        color = QColor(value)
        selected = w.scene.selectedItems()
        if color.isValid() and len(selected) == 1 and isinstance(selected[0], RectangleItem):
            selected[0].fill_color = color.name()
            selected[0].fill_opacity = fill_alpha.value() / 100
            selected[0].update()
            shape_color.setText(color.name())
            themed_style(shape_swatch, f'background: {color.name()};')
            w.save_snapshot()
    def choose_shape_color():
        color = QColorDialog.getColor(QColor(shape_color.text()), w, 'Cor do preenchimento')
        if color.isValid():
            set_shape_color(color.name())
    shape_swatch.clicked.connect(choose_shape_color)
    shape_color.editingFinished.connect(lambda: set_shape_color(shape_color.text()))
    fill_alpha.editingFinished.connect(lambda: set_shape_color(shape_color.text()))
    outline_enabled = QCheckBox('Contorno')
    outline_enabled.setObjectName('shapeOutlineEnabled')
    outline_color = QLineEdit('#000000')
    outline_color.setMaxLength(7)
    outline_alpha = QDoubleSpinBox()
    outline_alpha.setObjectName('shapeOutlineAlpha')
    outline_alpha.setRange(0, 100)
    outline_alpha.setDecimals(0)
    outline_alpha.setKeyboardTracking(False)
    outline_swatch = QPushButton()
    outline_swatch.setObjectName('shapeOutlineSwatch')
    square_control(outline_swatch)
    outline_width = QDoubleSpinBox()
    outline_width.setObjectName('shapeOutlineWidth')
    outline_width.setDecimals(2)
    outline_width.setRange(0.01, 1000)
    outline_width.setSingleStep(0.1)
    outline_width.setKeyboardTracking(False)
    outline_position = QComboBox()
    outline_position.setObjectName('shapeOutlinePosition')
    for title, value in [('Interno', 'inside'), ('Centralizado', 'center'), ('Externo', 'outside')]:
        outline_position.addItem(title, value)
    outline_position.setToolTip('Interno: para dentro. Externo: para fora. Centralizado: metade para cada lado.')
    shape_layout.addWidget(outline_enabled)
    outline_details, outline_details_layout = column()
    outline_details_layout.setContentsMargins(0, 0, 0, 0)
    outline_color_row = row(outline_details_layout, outline_swatch, outline_color, compact('α', outline_alpha, '%', 85))
    outline_color_row.setStretch(1, 1)
    outline_join, join_layout = column()
    join_layout.setContentsMargins(0, 0, 0, 0)
    outline_join.setObjectName('shapeOutlineJoin')
    join_straight = QRadioButton('Retos')
    join_round = QRadioButton('Arredondados')
    row(join_layout, join_straight, join_round)
    join_field = field('Cantos do contorno', outline_join)
    outline_details_layout.addWidget(join_field)
    rectangle_radius, rectangle_radius_layout = column()
    rectangle_radius_layout.setContentsMargins(0, 0, 0, 0)
    radius_heading = QLabel('ARREDONDAMENTO DE BORDAS')
    radius_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
    themed_style(radius_heading, 'color: @icon@; font-size: 11px; font-weight: 600;')
    rectangle_radius_layout.addWidget(radius_heading)
    sync_radii = QPushButton()
    sync_radii.setObjectName('syncCornerRadii')
    sync_radii.setCheckable(True)
    sync_radii.setChecked(True)
    sync_radii.setIcon(icon('<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2"/>'))
    sync_radii.setToolTip('Sincronizar o arredondamento dos quatro cantos')
    square_control(sync_radii)
    corner_grid = QGridLayout()
    corner_grid.setContentsMargins(0, 0, 0, 0)
    corner_grid.setHorizontalSpacing(8)
    corner_grid.setVerticalSpacing(8)
    corner_spins = {}
    for index, (key, title) in enumerate((
        ('top_left', 'Sup. esquerdo'), ('top_right', 'Sup. direito'),
        ('bottom_left', 'Inf. esquerdo'), ('bottom_right', 'Inf. direito'),
    )):
        spin = QDoubleSpinBox()
        spin.setObjectName('shapeCornerRadius_' + key)
        spin.setDecimals(2)
        spin.setRange(0, 1000)
        spin.setSingleStep(0.1)
        spin.setKeyboardTracking(False)
        control = field(title, compact('', spin, 'mm', None))
        corner_grid.addWidget(control, index // 2, index % 2)
        corner_spins[key] = spin
    corner_grid.setColumnStretch(0, 1)
    corner_grid.setColumnStretch(1, 1)
    corner_grid.addWidget(sync_radii, 0, 2, 2, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
    rectangle_radius_layout.addLayout(corner_grid)
    shape_layout.insertWidget(shape_layout.indexOf(outline_enabled), rectangle_radius)

    radius = QDoubleSpinBox()
    radius.setObjectName('shapeCornerRadius')
    radius.setDecimals(2)
    radius.setRange(0, 1000)
    radius.setSingleStep(0.1)
    radius.setKeyboardTracking(False)
    radius_field = field('Arredondamento', compact('', radius, 'mm', None))
    radius_field.setToolTip('Arredonda as extremidades da linha, limitado à metade da espessura.')
    def apply_line_radius():
        selected = w.scene.selectedItems()
        if len(selected) == 1 and getattr(selected[0], 'shape_type', '') == 'line':
            item = selected[0]
            item.prepareGeometryChange()
            item.corner_radius = mm_to_px(radius.value())
            item.update()
            w.save_snapshot()
    radius.editingFinished.connect(apply_line_radius)
    updating_radii = {'active': False}
    def apply_corner_radius(changed_key):
        if updating_radii['active']:
            return
        selected = w.scene.selectedItems()
        if len(selected) != 1 or getattr(selected[0], 'shape_type', '') != 'rectangle':
            return
        updating_radii['active'] = True
        try:
            if sync_radii.isChecked():
                value = corner_spins[changed_key].value()
                for spin in corner_spins.values():
                    spin.setValue(value)
            item = selected[0]
            item.corner_radii = {key: mm_to_px(spin.value()) for key, spin in corner_spins.items()}
            item.corner_radii_linked = sync_radii.isChecked()
            item.corner_radius = item.corner_radii['top_left']
            item.update()
            w.save_snapshot()
        finally:
            updating_radii['active'] = False
    for key, spin in corner_spins.items():
        spin.editingFinished.connect(lambda key=key: apply_corner_radius(key))
    def toggle_radius_sync(checked):
        if updating_radii['active']:
            return
        selected = w.scene.selectedItems()
        if len(selected) == 1 and getattr(selected[0], 'shape_type', '') == 'rectangle':
            selected[0].corner_radii_linked = checked
            if checked:
                apply_corner_radius('top_left')
            else:
                w.save_snapshot()
    sync_radii.toggled.connect(toggle_radius_sync)
    position_field = field('Posição', outline_position)
    thickness_row = row(outline_details_layout, field('Espessura', compact('', outline_width, 'mm')), position_field)
    thickness_row.setStretch(0, 1)
    thickness_row.setStretch(1, 1)
    for layout_index in range(outline_details_layout.count()):
        if outline_details_layout.itemAt(layout_index).layout() is thickness_row:
            outline_details_layout.takeAt(layout_index)
            break
    outline_details_layout.insertLayout(0, thickness_row)
    shape_layout.insertWidget(shape_layout.indexOf(outline_enabled) + 1, outline_details)
    line_geometry, line_layout = column()
    line_layout.setContentsMargins(0, 0, 0, 0)
    line_length = QDoubleSpinBox()
    line_length.setObjectName('lineLength')
    line_length.setDecimals(2)
    line_length.setRange(0.01, 5000)
    line_length.setKeyboardTracking(False)
    line_angle = QDoubleSpinBox()
    line_angle.setObjectName('lineAngle')
    line_angle.setRange(0, 359.99)
    line_angle.setDecimals(2)
    line_angle.setWrapping(True)
    line_angle.setKeyboardTracking(False)
    line_dimensions = row(line_layout, field('Comprimento', compact('', line_length, 'mm')),
                          field('Ângulo', compact('', line_angle, '°')))
    line_dimensions.setStretch(0, 1)
    line_dimensions.setStretch(1, 1)
    shape_layout.addWidget(line_geometry)
    def apply_line_geometry():
        selected = w.scene.selectedItems()
        if len(selected) == 1 and getattr(selected[0], 'shape_type', '') == 'line':
            item = selected[0]
            center = item.mapToScene(item.rect().center())
            item.resize_custom(mm_to_px(line_length.value()), 1)
            item.setRotation(-line_angle.value())
            item.setPos(center.x()-item.rect().width()/2, center.y()-0.5)
            w.update_position_ui()
            w.caixa_texto_panel.load_from_image(item)
            sync_enabled()
            w.save_snapshot()
    line_length.editingFinished.connect(apply_line_geometry)
    line_angle.editingFinished.connect(apply_line_geometry)
    background_outline_hint = QLabel('No plano de fundo, o contorno cresce sempre para dentro da página.')
    background_outline_hint.setWordWrap(True)
    background_outline_hint.setObjectName('muted')
    shape_layout.addWidget(background_outline_hint)
    def apply_outline(*_):
        from .canvas_items import RectangleItem
        selected = w.scene.selectedItems()
        if len(selected) != 1 or not isinstance(selected[0], RectangleItem):
            return
        item = selected[0]
        color = QColor(outline_color.text())
        if not color.isValid():
            outline_color.setText(item.outline_color)
            return
        item.prepareGeometryChange()
        is_line = item.shape_type == 'line'
        item.outline_enabled = is_line or outline_enabled.isChecked()
        item.outline_color = color.name()
        item.outline_opacity = outline_alpha.value() / 100
        item.outline_join = 'miter' if join_straight.isChecked() else 'round'
        # Não arredondar a medida original ao alterar apenas cor/posição.
        if outline_width.value() != round(px_to_mm(item.outline_width), 2):
            item.outline_width = mm_to_px(outline_width.value())
        item.outline_position = 'center' if is_line else ('inside' if getattr(item, 'is_document_background', False) else outline_position.currentData())
        item.update()
        themed_style(outline_swatch, f'background: {color.name()};')
        for control in (outline_color, outline_swatch, outline_width, outline_position, outline_alpha, outline_join):
            control.setEnabled(item.outline_enabled)
        w.save_snapshot()
    def choose_outline_color():
        color = QColorDialog.getColor(QColor(outline_color.text()), w, 'Cor do contorno')
        if color.isValid():
            outline_color.setText(color.name())
            apply_outline()
    outline_swatch.clicked.connect(choose_outline_color)
    outline_color.editingFinished.connect(apply_outline)
    outline_enabled.toggled.connect(outline_details.setVisible)
    outline_enabled.toggled.connect(apply_outline)
    outline_width.editingFinished.connect(apply_outline)
    outline_position.activated.connect(apply_outline)
    join_straight.clicked.connect(apply_outline)
    join_round.clicked.connect(apply_outline)
    outline_alpha.editingFinished.connect(apply_outline)
    p.btn_restore.setText('Restaurar original')
    p.btn_restore.setMinimumSize(0, 0)
    p.btn_restore.setMaximumSize(16777215, 16777215)
    row(pl, p.btn_restore, p.chk_link)
    prop_section = Section('Propriedades', props)
    il.addWidget(prop_section)
    t = w.editor_texto_panel
    square_control(t.btn_color)
    text_body, tl = column()
    hint = QLabel('Duplo clique no texto para editar no canvas.')
    hint.setWordWrap(True)
    hint.setObjectName('muted')
    tl.addWidget(hint)
    font_row = row(tl, field('Fonte', t.cbo_font), field('Tamanho', t.spin_size))
    font_row.setStretch(0, 3)
    font_row.setStretch(1, 1)
    styles = row(tl, t.btn_bold, t.btn_italic, t.btn_underline)
    styles.setSpacing(6)
    for button in (t.btn_bold, t.btn_italic, t.btn_underline):
        themed_style(button, 'QPushButton { padding: 0; min-width: 28px; max-width: 28px; '
                            'min-height: 28px; max-height: 28px; }')
        button.setFixedSize(30, 30)
    styles.addStretch()
    t.color_hex = QLineEdit('#000000')
    t.color_hex.setMaxLength(7)
    t.color_hex.setPlaceholderText('#RRGGBB')
    text_alpha = QDoubleSpinBox()
    text_alpha.setObjectName('textColorAlpha')
    text_alpha.setRange(0, 100)
    text_alpha.setDecimals(0)
    text_alpha.setValue(100)
    text_alpha.setKeyboardTracking(False)
    color_row, color_layout = column()
    color_layout.setContentsMargins(0, 0, 0, 0)
    text_color_row = row(color_layout, t.btn_color, t.color_hex, compact('α', text_alpha, '%', 85))
    text_color_row.setStretch(1, 1)
    tl.addWidget(field('Cor', color_row))
    def apply_hex():
        value = t.color_hex.text().strip()
        color = QColor(value)
        if len(value) == 7 and value.startswith('#') and color.isValid():
            themed_style(t.btn_color, f'background: {color.name()}; border: 1px solid @border_strong@;')
            color.setAlphaF(text_alpha.value()/100)
            t.fontColorChanged.emit(color.name(QColor.NameFormat.HexArgb))
            t.snapshotRequested.emit()
        else:
            t.color_hex.setText(t.color_hex.property('lastColor') or '#000000')
    t.color_hex.editingFinished.connect(apply_hex)
    text_alpha.editingFinished.connect(apply_hex)
    def color_changed(value):
        color = QColor(value)
        t.color_hex.setText(color.name())
        t.color_hex.setProperty('lastColor', color.name())
        text_alpha.setValue(round(color.alphaF()*100))
    t.fontColorChanged.connect(color_changed)
    alignment_heading = QLabel('ALINHAMENTO')
    themed_style(alignment_heading, 'color: @muted@; font-size: 10px; font-weight: 600; margin-top: 6px;')
    tl.addWidget(alignment_heading)
    for control in (t.cbo_align, t.cbo_valign, t.spin_lh, t.spin_indent, t.spin_size):
        selector = 'QComboBox' if isinstance(control, QComboBox) else 'QAbstractSpinBox'
        themed_style(control, selector + ' { min-height: 18px; max-height: 18px; padding-top: 5px; padding-bottom: 5px; }')
        control.setFixedHeight(30)
        control.setMinimumWidth(0)
    for control in (t.cbo_align, t.cbo_valign):
        popup = QListView(control)
        popup.setObjectName('alignmentOptions')
        themed_style(popup, '''
            QListView#alignmentOptions {
                background: @button@; color: @text@;
                border: 1px solid @border_strong@; border-radius: 8px;
                padding: 6px; outline: none;
            }
            QListView#alignmentOptions::item {
                padding: 9px 12px; border: 1px solid transparent;
                border-radius: 5px; background: transparent;
            }
            QListView#alignmentOptions::item:selected,
            QListView#alignmentOptions::item:hover {
                background: @selection@; border-color: @accent@; color: @text@;
            }
        ''')
        popup.setMouseTracking(True)
        control.setView(popup)
    alignments = row(tl, field('Horizontal', t.cbo_align), field('Vertical', t.cbo_valign))
    alignments.setStretch(0, 1)
    alignments.setStretch(1, 1)
    spacing = row(tl, field('Entrelinha', t.spin_lh), field('Recuo', t.spin_indent))
    t.spin_indent.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spacing.setStretch(0, 1)
    spacing.setStretch(1, 1)
    text_section = Section('Texto', text_body)
    il.addWidget(text_section)
    doc, dl = column()
    def document_heading(title):
        label = QLabel(title)
        themed_style(label, 'color: @muted@; font-size: 10px; font-weight: 600; margin-top: 6px;')
        dl.addWidget(label)
    document_heading('DIMENSÕES')
    w.chk_doc_proporcao.setText('')
    w.chk_doc_proporcao.setIcon(p.chk_proporcao.icon())
    w.chk_doc_proporcao.setFixedSize(30, 30)
    w._refresh_doc_proportion_button()
    dimensions = row(dl, compact('L', w.spin_phys_w, 'mm'),
                     compact('A', w.spin_phys_h, 'mm'), w.chk_doc_proporcao)
    dimensions.addStretch()
    document_heading('CAMPOS DA TABELA')
    order_hint = QLabel('Segure e arraste para ajustar a ordem')
    order_hint.setWordWrap(True)
    themed_style(order_hint, 'color: @disabled@; font-size: 10px;')
    dl.addWidget(order_hint)
    w.lst_placeholders.setObjectName('tableFields')
    themed_style(w.lst_placeholders, '''
        QListWidget#tableFields { background: @surface@; border: none; outline: none; }
        QListWidget#tableFields::item { padding: 4px 5px; border: none; }
        QListWidget#tableFields::item:selected { background: @selection@; color: @text@; }
        QListWidget#tableFields::item:hover { background: @hover@; }
    ''')
    w.lst_placeholders.setFixedHeight(180)
    w.lst_placeholders.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    dl.addWidget(w.lst_placeholders)
    w.btn_fit_bg.hide()
    w.btn_add_bg.hide()
    document_section = Section('Documento', doc, True)
    il.insertWidget(0, document_section)
    il.addStretch()
    right = QScrollArea()
    right.setObjectName('inspectorScroll')
    right.setWidgetResizable(True)
    right.setWidget(inspector)
    right.setMinimumWidth(322)
    split.addWidget(right)
    split.setSizes([262, 916, 322])
    split.setStretchFactor(1, 1)
    split.setChildrenCollapsible(False)
    footer_bar = QFrame()
    footer_bar.setObjectName('footer')
    footer_bar.setFixedHeight(44)
    footer = QHBoxLayout(footer_bar)
    footer.setContentsMargins(14, 5, 14, 5)
    footer.addWidget(QLabel('Página 1 de 1'))
    footer.addStretch()
    w.btn_save.setText('Salvar modelo')
    w.btn_save.setMinimumSize(0, 0)
    w.btn_save.setMaximumSize(16777215, 16777215)
    w.btn_save.setFixedSize(116, 34)
    footer.addWidget(w.btn_save)
    outer.addWidget(footer_bar)
    w._footer_save_alignment = FooterSaveAlignment(
        w, right, footer_bar, footer, w.btn_save
    )
    split.splitterMoved.connect(lambda *_: w._footer_save_alignment.schedule())
    w._footer_save_alignment.schedule()

    selection_state = {'kind': None}

    def clear_text_presentation():
        """Limpa somente os controles visuais; o texto continua no item da cena."""
        controls = (
            t.txt_content, t.cbo_font, t.spin_size, t.btn_bold,
            t.btn_italic, t.btn_underline, t.cbo_align, t.cbo_valign,
            t.spin_lh, t.spin_indent, t.btn_color, t.color_hex, text_alpha,
        )
        previous = [(control, control.blockSignals(True)) for control in controls]
        try:
            t.txt_content.clear()
            t.cbo_font.setCurrentIndex(-1)
            t.spin_size.lineEdit().clear()
            t.btn_bold.setChecked(False)
            t.btn_italic.setChecked(False)
            t.btn_underline.setChecked(False)
            t.cbo_align.setCurrentIndex(-1)
            t.cbo_valign.setCurrentIndex(-1)
            t.spin_lh.lineEdit().clear()
            t.spin_indent.lineEdit().clear()
            t.color_hex.clear()
            text_alpha.lineEdit().clear()
            themed_style(t.btn_color, 'background: @field@; border: 1px solid @border@; border-radius: 5px;')
        finally:
            for control, was_blocked in previous:
                control.blockSignals(was_blocked)

    def sync_enabled():
        from shiboken6 import isValid
        if not isValid(w.scene):
            return
        for control in moved:
            control.setEnabled(p.isEnabled())
        props.setEnabled(p.isEnabled())
        text_available = t.isEnabled()
        properties_available = p.isEnabled()
        prop_section.setEnabled(properties_available)
        text_section.setEnabled(text_available)
        text_body.setEnabled(t.isEnabled())
        selected = w.scene.selectedItems()
        current_kind = 'text' if text_available else ('object' if selected else 'none')
        if current_kind != selection_state['kind']:
            if current_kind != 'text':
                clear_text_presentation()
            if properties_available:
                prop_section.header.setChecked(True)
            else:
                prop_section.header.setChecked(False)
            if text_available:
                text_section.header.setChecked(True)
            else:
                text_section.header.setChecked(False)
            selection_state['kind'] = current_kind
        from .canvas_items import RectangleItem, ImageItem, BackgroundItem, SignatureItem
        is_shape = len(selected) == 1 and isinstance(selected[0], RectangleItem)
        background_selected = any(getattr(item, 'is_document_background', False) for item in selected)
        restore_visible = len(selected) == 1 and (
            isinstance(selected[0], SignatureItem)
            or (
                isinstance(selected[0], ImageItem)
                and not isinstance(selected[0], (RectangleItem, BackgroundItem))
            )
        )
        if background_selected:
            for control in (w.spin_pos_x, w.spin_pos_y, p.spin_w, p.spin_h, p.spin_rot, p.chk_proporcao):
                control.setEnabled(False)
        w.btn_dup_layer.setEnabled(bool(selected) and not background_selected)
        w.btn_del_layer.setEnabled(bool(selected) and not background_selected)
        shape_controls.setVisible(is_shape)
        p.btn_restore.setVisible(restore_visible)
        if is_shape:
            item = selected[0]
            is_line = item.shape_type == 'line'
            fill_controls.setVisible(not is_line)
            outline_enabled.setVisible(not is_line)
            position_field.setVisible(not is_line)
            join_field.setVisible(item.shape_type == 'rectangle')
            rectangle_radius.setVisible(item.shape_type == 'rectangle')
            # A linha mantém um único arredondamento para suas duas extremidades.
            shape_layout.removeWidget(radius_field)
            thickness_row.removeWidget(radius_field)
            if is_line:
                thickness_row.addWidget(radius_field, 1)
            radius_field.setVisible(is_line)
            if is_line:
                radius.setValue(px_to_mm(item.corner_radius))
            elif item.shape_type == 'rectangle':
                stored_radii = dict(getattr(item, 'corner_radii', {}) or {})
                fallback = getattr(item, 'corner_radius', 0)
                updating_radii['active'] = True
                try:
                    sync_radii.setChecked(getattr(item, 'corner_radii_linked', True))
                    for key, spin in corner_spins.items():
                        spin.setValue(px_to_mm(stored_radii.get(key, fallback)))
                finally:
                    updating_radii['active'] = False
            line_geometry.setVisible(is_line)
            if is_line:
                line_length.setValue(px_to_mm(item.rect().width()))
                line_angle.setValue((-item.rotation()) % 360)
                p.spin_h.setEnabled(False)
                p.chk_proporcao.setEnabled(False)
                p.spin_rot.blockSignals(True)
                p.spin_rot.setValue((-item.rotation()) % 360)
                p.spin_rot.blockSignals(False)
            outline_enabled.blockSignals(True)
            outline_enabled.setChecked(item.outline_enabled)
            outline_enabled.blockSignals(False)
            outline_details.setVisible(is_line or item.outline_enabled)
            outline_color.setText(item.outline_color)
            fill_alpha.setValue(item.fill_opacity * 100)
            outline_alpha.setValue(item.outline_opacity * 100)
            join_straight.setChecked(item.outline_join == 'miter')
            join_round.setChecked(item.outline_join != 'miter')
            themed_style(outline_swatch, f'background: {item.outline_color};')
            outline_width.setValue(px_to_mm(item.outline_width))
            for index in range(outline_position.count()):
                outline_position.model().item(index).setEnabled(
                    not background_selected or outline_position.itemData(index) == 'inside')
            outline_position.setCurrentIndex(max(0, outline_position.findData(item.outline_position)))
            for control in (outline_color, outline_swatch, outline_width, outline_position, outline_alpha, outline_join):
                control.setEnabled(item.outline_enabled)
            background_outline_hint.setVisible(background_selected)
            shape_color.setText(selected[0].fill_color)
            themed_style(shape_swatch, f'background: {selected[0].fill_color};')
            p.btn_restore.setEnabled(False)
            p.set_link_available(not background_selected)
        selection.setText('SELEÇÃO\n' + (getattr(selected[0], 'layer_name', '') or 'Objeto selecionado' if selected else 'Nenhum objeto'))
        if t.isEnabled() and len(selected) == 1:
            color_changed(getattr(selected[0].state, 'font_color', '#000000'))
            if hasattr(w, 'canvas_edit'):
                w.canvas_edit.sync_panel()
    w.scene.selectionChanged.connect(sync_enabled)
    # O seletor legado bloqueia os sinais da cena enquanto seleciona pela lista.
    # Atualizar depois dele também cobre o único acesso ao plano de fundo.
    w.layer_list.itemSelectionChanged.connect(sync_enabled)
    # O editor sempre começa no contexto geral do documento. As seções de
    # objeto só são habilitadas quando o usuário faz uma seleção explícita.
    w.scene.clearSelection()
    sync_enabled()
