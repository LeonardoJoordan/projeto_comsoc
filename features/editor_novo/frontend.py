"""Apresentação Widgets independente; reutiliza controles e sinais do legado."""
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter
from .canvas_items import mm_to_px, px_to_mm
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSplitter, QFrame, QLineEdit, QAbstractSpinBox, QColorDialog,
    QCheckBox, QDoubleSpinBox, QComboBox, QMenu,
)


STYLE = """
QWidget { background: #1a1b21; color: #f3f5f8; font-size: 12px; }
QMainWindow, QWidget#root { background: #0f1014; }
QLabel { background: transparent; }
QLabel#muted { color: #a8abb5; }
QFrame#bar { background: #15161b; border-bottom: 1px solid #30323b; }
QFrame#compact { background: #121318; border: 1px solid #30323b; border-radius: 6px; }
QFrame#compact QAbstractSpinBox { border: none; background: transparent; padding: 0; min-height: 0; font-size: 11px; }
QFrame#compact QLabel { color: #777b87; font-size: 10px; }
QPushButton { background: #22232b; border: 1px solid #30323b;
 border-radius: 6px; padding: 6px 10px; min-height: 20px; }
QPushButton:hover { background: #2a2c35; border-color: #454854; }
QPushButton:checked { background: #343159; border-color: #7c73f2; }
QPushButton:disabled { color: #777b87; background: #1a1b21; }
QPushButton#primary { background: #7c73f2; color: white; border: none; }
QPushButton#section { text-align: left; background: #15161b;
 border: none; border-bottom: 1px solid #30323b; border-radius: 0;
 padding: 12px; font-weight: 600; }
QLineEdit, QAbstractSpinBox, QComboBox, QTextEdit { background: #121318;
 border: 1px solid #30323b; border-radius: 5px; padding: 5px; min-height: 20px;
 selection-background-color: #343159; }
QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus, QTextEdit:focus { border-color: #7c73f2; }
QWidget:disabled { color: #777b87; }
QListWidget { background: #1a1b21; border: none; outline: none; }
QListWidget::item { padding: 7px; border-bottom: 1px solid #292a31; }
QListWidget::item:selected { background: #343159; color: #f3f5f8; }
QListWidget#layers::item { padding: 0; border: none; }
QListWidget#layers QWidget { background: transparent; }
QScrollArea { border: none; }
QScrollBar:vertical { background: #15161b; width: 8px; }
QScrollBar::handle:vertical { background: #454854; min-height: 24px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background: #30323b; width: 1px; }
QToolTip { background: #22232b; color: #f3f5f8; border: 1px solid #454854; padding: 6px; }
"""


def icon(path):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="#c5c3df" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{path}</g></svg>'
    pix = QPixmap(24, 24)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    QSvgRenderer(svg.encode()).render(painter)
    painter.end()
    return QIcon(pix)


def column():
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(10)
    return widget, layout


def row(layout, *widgets):
    line = QHBoxLayout()
    line.setSpacing(8)
    for widget in widgets:
        line.addWidget(widget)
    layout.addLayout(line)
    return line


def field(name, control):
    widget, layout = column()
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
    widget.setFixedSize(width, 30)
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
        child.setStyleSheet('')
    w.setStyleSheet(STYLE)
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
    w.btn_close_editor.setText('‹  Modelos')
    w.btn_close_editor.setFixedSize(90, 34)
    h.addWidget(w.btn_close_editor)
    badge = QLabel('C')
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setFixedSize(28, 28)
    badge.setStyleSheet('background: #343159; color: #9087ff; border-radius: 7px; font-weight: bold;')
    h.addWidget(badge)
    title_block, title_layout = column()
    title_layout.setContentsMargins(8, 0, 0, 0)
    title_layout.setSpacing(3)
    title = QLabel(w._current_model_name or 'Novo modelo')
    title.setStyleSheet('font-size: 13px; font-weight: 600;')
    title_layout.addWidget(title)
    subtitle = QLabel('Editor de modelo')
    subtitle.setObjectName('muted')
    title_layout.addWidget(subtitle)
    w.windowTitleChanged.connect(lambda _: title.setText(w._current_model_name or 'Novo modelo'))
    h.addWidget(title_block)
    h.addStretch()
    for button, text in [(w.btn_undo, '↶'), (w.btn_redo, '↷'), (w.btn_save, 'Salvar modelo')]:
        button.setText(text)
        button.setMinimumSize(0, 0)
        button.setMaximumSize(16777215, 16777215)
        button.setFixedHeight(34)
        h.addWidget(button)
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
    selection.setStyleSheet('color: #a8abb5; font-size: 10px;')
    tools.addWidget(selection)
    moved = [p.spin_w, p.spin_h, p.chk_proporcao, p.spin_rot, p.spin_opacity]
    for name, control in [('X', w.spin_pos_x), ('Y', w.spin_pos_y), ('L', p.spin_w), ('A', p.spin_h)]:
        tools.addWidget(compact(name, control, 'mm'))
    p.chk_proporcao.setText('')
    p.chk_proporcao.setIcon(icon('<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2"/>'))
    p.chk_proporcao.setFixedSize(30, 30)
    tools.addWidget(p.chk_proporcao)
    tools.addWidget(compact('↻', p.spin_rot, '°', 78))
    tools.addWidget(compact('Op.', p.spin_opacity, '%', 88))
    guide_label = QLabel('GUIAS')
    guide_label.setObjectName('muted')
    tools.addWidget(guide_label)
    for vertical, label, path in [(False, 'Adicionar guia horizontal', '<path d="M3 12h18M12 3v4m0 10v4"/>'), (True, 'Adicionar guia vertical', '<path d="M12 3v18M3 12h4m10 0h4"/>')]:
        button = QPushButton()
        button.setIcon(icon(path))
        button.setFixedSize(30, 30)
        button.setStyleSheet('padding: 0;')
        button.setToolTip(label)
        button.clicked.connect(lambda checked=False, v=vertical: w.add_guide(v))
        tools.addWidget(button)
    w.btn_toggle_guides.setText('Guias')
    w.btn_toggle_guides.setFixedSize(70, 34)
    tools.addWidget(w.btn_toggle_guides)
    tools.addStretch()
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
    shape_menu.setStyleSheet('''
        QMenu#shapeMenu {
            background-color: #22232b;
            border: 1px solid #454854;
            border-radius: 8px;
            padding: 6px;
        }
        QMenu#shapeMenu::item {
            color: #f3f5f8;
            background-color: transparent;
            padding: 10px 28px 10px 36px;
            border: 1px solid transparent;
            border-radius: 5px;
        }
        QMenu#shapeMenu::item:selected {
            background-color: #343159;
            border-color: #7c73f2;
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
    for button, label, path in [
        (w.btn_add, 'Texto', '<path d="M4 5h16M12 5v15M8 20h8"/>'),
        (forms, 'Formas', '<rect x="4" y="4" width="16" height="16" rx="3"/>'),
        (w.btn_add_img, 'Imagens', '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m3 16 5-5 5 5 3-3 5 5"/>'),
        (w.btn_add_sig, 'Assinatura', '<path d="m4 17 3-1L19 4l2 2L9 18l-5 1zM4 22h16"/>')]:
        detail = {'Texto': 'Campo dinâmico', 'Formas': 'Preenchimento e borda', 'Imagens': 'Foto, logo ou QR', 'Assinatura': 'Imagem opcional'}[label]
        button.setText('')
        contents = QHBoxLayout(button)
        contents.setContentsMargins(42, 3, 8, 3)
        caption = QLabel(f'<b>{label}</b><br><span style="font-size:9px;color:#777b87">{detail}</span>')
        caption.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        contents.addWidget(caption)
        button.setIcon(icon(path))
        button.setIconSize(QSize(20, 20))
        button.setObjectName('add' + label)
        # QSS mede a área de conteúdo: 36 + 12 de padding + 2 de borda = 50.
        # Fixar também no estilo evita que o polish restaure o mínimo global.
        button.setStyleSheet('QPushButton#' + button.objectName() + ' { '
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
        b.setStyleSheet('padding: 6px 3px;')
        b.setFixedSize(28, 28)
        paths = {'Renomear': '<path d="m4 17 3-1L19 4l2 2L9 18l-5 1z"/>', 'Duplicar': '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M15 8V4H4v11h4"/>', 'Excluir': '<path d="M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>'}
        b.setIcon(icon(paths[label]))
        layer_heading.addWidget(b)
    ll.addLayout(layer_heading)
    w.layer_list.setObjectName('layers')
    ll.addWidget(w.layer_list, 1)
    split.addWidget(left)
    w.view.setBackgroundBrush(QColor('#26272c'))
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
    shape_color.setMaximumWidth(110)
    fill_alpha = QDoubleSpinBox()
    fill_alpha.setObjectName('shapeFillAlpha')
    fill_alpha.setRange(0, 100)
    fill_alpha.setDecimals(0)
    fill_alpha.setKeyboardTracking(False)
    shape_swatch = QPushButton()
    shape_swatch.setFixedSize(32, 32)
    shape_controls, shape_layout = column()
    shape_layout.setContentsMargins(0, 0, 0, 0)
    fill_controls, fill_layout = column()
    fill_layout.setContentsMargins(0, 0, 0, 0)
    fill_layout.addWidget(QLabel('Preenchimento'))
    row(fill_layout, shape_swatch, shape_color, compact('α', fill_alpha, '%', 85))
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
            shape_swatch.setStyleSheet(f'background: {color.name()};')
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
    outline_color.setMaximumWidth(110)
    outline_alpha = QDoubleSpinBox()
    outline_alpha.setObjectName('shapeOutlineAlpha')
    outline_alpha.setRange(0, 100)
    outline_alpha.setDecimals(0)
    outline_alpha.setKeyboardTracking(False)
    outline_swatch = QPushButton()
    outline_swatch.setFixedSize(32, 32)
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
    row(shape_layout, outline_swatch, outline_color, compact('α', outline_alpha, '%', 85))
    outline_join = QComboBox()
    outline_join.setObjectName('shapeOutlineJoin')
    outline_join.addItem('Arredondados', 'round')
    outline_join.addItem('Retos', 'miter')
    join_field = field('Cantos do contorno', outline_join)
    shape_layout.addWidget(join_field)
    radius = QDoubleSpinBox()
    radius.setObjectName('shapeCornerRadius')
    radius.setDecimals(2)
    radius.setRange(0, 1000)
    radius.setSingleStep(0.1)
    radius.setKeyboardTracking(False)
    radius_field = field('Raio de arredondamento', compact('', radius, 'mm'))
    radius_field.setToolTip('Zero mantém os cantos retos. Na linha, o raio é limitado à metade da espessura; no retângulo, à metade do menor lado.')
    shape_layout.addWidget(radius_field)
    def apply_radius():
        selected = w.scene.selectedItems()
        if len(selected) == 1 and getattr(selected[0], 'shape_type', '') in ('rectangle', 'line'):
            item = selected[0]
            item.prepareGeometryChange()
            item.corner_radius = mm_to_px(radius.value())
            item.update()
            w.save_snapshot()
    radius.editingFinished.connect(apply_radius)
    position_field = field('Posição', outline_position)
    row(shape_layout, field('Espessura', compact('', outline_width, 'mm')), position_field)
    line_geometry, line_layout = column()
    line_layout.setContentsMargins(0, 0, 0, 0)
    line_length = QDoubleSpinBox()
    line_length.setObjectName('lineLength')
    line_length.setDecimals(2)
    line_length.setRange(0.01, 5000)
    line_length.setSuffix(' mm')
    line_length.setKeyboardTracking(False)
    line_angle = QDoubleSpinBox()
    line_angle.setObjectName('lineAngle')
    line_angle.setRange(0, 359.99)
    line_angle.setDecimals(2)
    line_angle.setSuffix(' °')
    line_angle.setWrapping(True)
    line_angle.setKeyboardTracking(False)
    row(line_layout, field('Comprimento', line_length), field('Ângulo', line_angle))
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
        item.outline_join = outline_join.currentData()
        # Não arredondar a medida original ao alterar apenas cor/posição.
        if outline_width.value() != round(px_to_mm(item.outline_width), 2):
            item.outline_width = mm_to_px(outline_width.value())
        item.outline_position = 'center' if is_line else ('inside' if getattr(item, 'is_document_background', False) else outline_position.currentData())
        item.update()
        outline_swatch.setStyleSheet(f'background: {color.name()};')
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
    outline_enabled.toggled.connect(apply_outline)
    outline_width.editingFinished.connect(apply_outline)
    outline_position.activated.connect(apply_outline)
    outline_join.activated.connect(apply_outline)
    outline_alpha.editingFinished.connect(apply_outline)
    p.btn_restore.setText('Restaurar original')
    p.btn_restore.setMinimumSize(0, 0)
    p.btn_restore.setMaximumSize(16777215, 16777215)
    row(pl, p.btn_restore, p.chk_link)
    prop_section = Section('Propriedades', props, True)
    il.addWidget(prop_section)
    t = w.editor_texto_panel
    text_body, tl = column()
    hint = QLabel('Duplo clique no texto para editar no canvas.')
    hint.setWordWrap(True)
    hint.setObjectName('muted')
    tl.addWidget(hint)
    row(tl, field('Fonte', t.cbo_font), field('Tamanho', t.spin_size))
    row(tl, t.btn_bold, t.btn_italic, t.btn_underline)
    t.color_hex = QLineEdit('#000000')
    t.color_hex.setMaxLength(7)
    t.color_hex.setPlaceholderText('#RRGGBB')
    color_row, color_layout = column()
    color_layout.setContentsMargins(0, 0, 0, 0)
    row(color_layout, t.btn_color, t.color_hex)
    tl.addWidget(field('Cor', color_row))
    def apply_hex():
        value = t.color_hex.text().strip()
        color = QColor(value)
        if len(value) == 7 and value.startswith('#') and color.isValid():
            t.btn_color.setStyleSheet(f'background: {color.name()}; border: 1px solid #454854;')
            t.fontColorChanged.emit(color.name())
            t.snapshotRequested.emit()
        else:
            t.color_hex.setText(t.color_hex.property('lastColor') or '#000000')
    t.color_hex.editingFinished.connect(apply_hex)
    def color_changed(value):
        t.color_hex.setText(value)
        t.color_hex.setProperty('lastColor', value)
    t.fontColorChanged.connect(color_changed)
    row(tl, field('Horizontal', t.cbo_align), field('Vertical', t.cbo_valign))
    spacing = row(tl, field('Entrelinha', t.spin_lh), field('Recuo · px', t.spin_indent))
    spacing.setStretch(0, 1)
    spacing.setStretch(1, 1)
    text_section = Section('Texto', text_body)
    il.addWidget(text_section)
    table, table_layout = column()
    table_layout.addWidget(QLabel('Ordem na tabela · arraste para reorganizar'))
    table_layout.addWidget(w.lst_placeholders)
    il.addWidget(Section('Campos da tabela', table))
    doc, dl = column()
    w.chk_doc_proporcao.setText('')
    w.chk_doc_proporcao.setIcon(p.chk_proporcao.icon())
    w.chk_doc_proporcao.setFixedSize(30, 30)
    dimensions = row(dl, compact('L', w.spin_phys_w, 'mm'),
                     compact('A', w.spin_phys_h, 'mm'), w.chk_doc_proporcao)
    dimensions.addStretch()
    w.btn_fit_bg.hide()
    w.btn_add_bg.hide()
    il.insertWidget(0, Section('Documento', doc))
    il.addStretch()
    right = QScrollArea()
    right.setWidgetResizable(True)
    right.setWidget(inspector)
    right.setMinimumWidth(322)
    split.addWidget(right)
    split.setSizes([262, 916, 322])
    split.setStretchFactor(1, 1)
    split.setChildrenCollapsible(False)
    footer = QHBoxLayout()
    footer.setContentsMargins(14, 5, 14, 5)
    footer.addWidget(QLabel('Página 1 de 1'))
    footer.addStretch()
    fit = QPushButton('Ajustar à janela')
    fit.clicked.connect(w._zoom_to_fit)
    footer.addWidget(fit)
    outer.addLayout(footer)

    def sync_enabled():
        from shiboken6 import isValid
        if not isValid(w.scene):
            return
        for control in moved:
            control.setEnabled(p.isEnabled())
        props.setEnabled(p.isEnabled())
        text_section.setEnabled(t.isEnabled())
        text_body.setEnabled(t.isEnabled())
        selected = w.scene.selectedItems()
        from .canvas_items import RectangleItem
        is_shape = len(selected) == 1 and isinstance(selected[0], RectangleItem)
        background_selected = any(getattr(item, 'is_document_background', False) for item in selected)
        if background_selected:
            for control in (w.spin_pos_x, w.spin_pos_y, p.spin_w, p.spin_h, p.spin_rot, p.chk_proporcao):
                control.setEnabled(False)
        w.btn_dup_layer.setEnabled(bool(selected) and not background_selected)
        w.btn_del_layer.setEnabled(bool(selected) and not background_selected)
        shape_controls.setVisible(is_shape)
        if is_shape:
            item = selected[0]
            is_line = item.shape_type == 'line'
            fill_controls.setVisible(not is_line)
            outline_enabled.setVisible(not is_line)
            position_field.setVisible(not is_line)
            join_field.setVisible(item.shape_type == 'rectangle')
            radius_field.setVisible(item.shape_type in ('rectangle', 'line'))
            radius.setValue(px_to_mm(item.corner_radius))
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
            outline_color.setText(item.outline_color)
            fill_alpha.setValue(item.fill_opacity * 100)
            outline_alpha.setValue(item.outline_opacity * 100)
            outline_join.setCurrentIndex(max(0, outline_join.findData(item.outline_join)))
            outline_swatch.setStyleSheet(f'background: {item.outline_color};')
            outline_width.setValue(px_to_mm(item.outline_width))
            for index in range(outline_position.count()):
                outline_position.model().item(index).setEnabled(
                    not background_selected or outline_position.itemData(index) == 'inside')
            outline_position.setCurrentIndex(max(0, outline_position.findData(item.outline_position)))
            for control in (outline_color, outline_swatch, outline_width, outline_position, outline_alpha, outline_join):
                control.setEnabled(item.outline_enabled)
            background_outline_hint.setVisible(background_selected)
            shape_color.setText(selected[0].fill_color)
            shape_swatch.setStyleSheet(f'background: {selected[0].fill_color};')
            p.btn_restore.setEnabled(False)
            p.chk_link.setEnabled(False)
        selection.setText('SELEÇÃO\n' + (getattr(selected[0], 'layer_name', '') or 'Objeto selecionado' if selected else 'Nenhum objeto'))
        if t.isEnabled() and len(selected) == 1:
            color_changed(getattr(selected[0].state, 'font_color', '#000000'))
    w.scene.selectionChanged.connect(sync_enabled)
    # O seletor legado bloqueia os sinais da cena enquanto seleciona pela lista.
    # Atualizar depois dele também cobre o único acesso ao plano de fundo.
    w.layer_list.itemSelectionChanged.connect(sync_enabled)
    sync_enabled()
