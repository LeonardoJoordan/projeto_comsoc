import json
from PySide6.QtWidgets import (QMainWindow, QGraphicsView, QGraphicsScene, QWidget, 
                               QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, 
                               QMessageBox, QInputDialog, QListWidget, QAbstractItemView,
                               QListWidgetItem, QDoubleSpinBox, QComboBox)
from PySide6.QtGui import (QPainter, QBrush, QPen, QColor, QShortcut, 
                           QKeySequence, QTextCursor, QTextCharFormat)
from PySide6.QtCore import Qt, Signal, QEvent
from pathlib import Path
import shutil

from .canvas_items import DesignerBox, Guideline, px_to_mm, SignatureItem, ImageItem
from .properties import CaixaDeTextoPanel, EditorDeTextoPanel
from core.template_manager import slugify_model_name
from core.paths import get_models_dir

class EditorWindow(QMainWindow):
    modelSaved = Signal(str, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor Visual de Modelo (Gerador de Cartões em Lote - GCL)")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        left_container = QWidget()
        left_container.setFixedWidth(220)
        left_layout = QVBoxLayout(left_container)
        
        # --- Grupo: Linhas Guia ---
        grp_guides = QFrame()
        ly_guides = QVBoxLayout(grp_guides)
        ly_guides.setContentsMargins(0, 0, 0, 10)
        lbl_guides = QLabel("<b>LINHAS GUIA</b> <small style='color:gray'>(Duplo clique p/ editar)</small>")
        ly_guides.addWidget(lbl_guides)
        
        row_guides = QHBoxLayout()
        row_guides.setSpacing(10)
        btn_guide_v = QPushButton("Vertical (|)")
        btn_guide_v.clicked.connect(lambda: self.add_guide(vertical=True))
        btn_guide_h = QPushButton("Horizontal (—)")
        btn_guide_h.clicked.connect(lambda: self.add_guide(vertical=False))
        row_guides.addWidget(btn_guide_v)
        row_guides.addWidget(btn_guide_h)
        ly_guides.addLayout(row_guides)
        left_layout.addWidget(grp_guides)
        self._add_separator(left_layout)

        # --- Grupo: Elementos ---
        grp_boxes = QFrame()
        ly_boxes = QVBoxLayout(grp_boxes)
        ly_boxes.setContentsMargins(0, 0, 0, 10)
        ly_boxes.addWidget(QLabel("<b>ELEMENTOS</b>"))
        
        self.btn_add_sig = QPushButton("✍️ Assinatura")
        self.btn_add_sig.setMinimumHeight(35)
        self.btn_add_sig.clicked.connect(self._on_click_add_signature)
        ly_boxes.addWidget(self.btn_add_sig)

        self.btn_add = QPushButton("📝 Caixa de Texto")
        self.btn_add.setMinimumHeight(35)
        self.btn_add.clicked.connect(self.add_new_box)
        ly_boxes.addWidget(self.btn_add)

        self.btn_add_img = QPushButton("📸 Imagem")
        self.btn_add_img.setMinimumHeight(35)
        self.btn_add_img.clicked.connect(self._on_click_add_image)
        ly_boxes.addWidget(self.btn_add_img)

        self.btn_add_bg = QPushButton("🖼️ Fundo")
        self.btn_add_bg.setMinimumHeight(35)
        self.btn_add_bg.clicked.connect(self._on_click_load_bg)
        ly_boxes.addWidget(self.btn_add_bg)
        left_layout.addWidget(grp_boxes)
        self._add_separator(left_layout)

        lbl_layers = QLabel("<b>CAMADAS</b>")
        left_layout.addWidget(lbl_layers)

        self.layer_list = QListWidget()
        self.layer_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.layer_list.itemClicked.connect(self._on_layer_list_clicked)
        self.layer_list.itemChanged.connect(self._on_layer_item_changed)
        self.layer_list.model().rowsMoved.connect(self._on_layer_reordered)
        left_layout.addWidget(self.layer_list)
        
        main_layout.addWidget(left_container)

        self.scene = QGraphicsScene(0, 0, 1000, 1000)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setBackgroundBrush(QBrush(QColor("#e0e0e0")))
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Otimização de UX: Zoom segue o ponteiro do mouse
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Filtra a view e o viewport para impedir o vazamento do Scroll
        self.view.installEventFilter(self)
        self.view.viewport().installEventFilter(self)
        
        self.bg_item = None
        self.background_path = None
        
        self.fallback_bg = self.scene.addRect(0, 0, 1000, 1000, QPen(Qt.PenStyle.NoPen), QBrush(Qt.GlobalColor.white))
        self.fallback_bg.setZValue(-100)
        
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        center_layout.addWidget(self.view, 1)
        
        main_layout.addWidget(center_container, 1)

        right_container = QWidget()
        right_container.setFixedWidth(400)
        right_layout = QVBoxLayout(right_container)

        # --- Grupo: Dimensões do Documento ---
        grp_doc = QFrame()
        ly_doc = QVBoxLayout(grp_doc)
        ly_doc.setContentsMargins(0, 0, 0, 10)
        lbl_physical = QLabel("<b>DIMENSÕES DO DOCUMENTO</b>")
        ly_doc.addWidget(lbl_physical)
        
        row_phys = QHBoxLayout()
        self.spin_phys_w = QDoubleSpinBox()
        self.spin_phys_w.setRange(10, 2000)
        self.spin_phys_w.setSuffix(" mm")
        self.spin_phys_w.setPrefix("Larg: ")
        self.spin_phys_w.setDecimals(1)
        self.spin_phys_w.setValue(100.0) 
        
        self.spin_phys_h = QDoubleSpinBox()
        self.spin_phys_h.setRange(10, 2000)
        self.spin_phys_h.setSuffix(" mm")
        self.spin_phys_h.setPrefix("Alt: ")
        self.spin_phys_h.setDecimals(1)
        self.spin_phys_h.setValue(150.0) 
        
        row_phys.addWidget(self.spin_phys_w)
        row_phys.addWidget(self.spin_phys_h)
        ly_doc.addLayout(row_phys)
        right_layout.addWidget(grp_doc)
        self._add_separator(right_layout)

        # --- Grupo: Propriedades do Item (Posição X, Y) ---
        grp_pos = QFrame()
        ly_pos = QVBoxLayout(grp_pos)
        ly_pos.setContentsMargins(0, 0, 0, 10)
        lbl_pos = QLabel("<b>PROPRIEDADES DO ITEM</b>")
        ly_pos.addWidget(lbl_pos)
        
        row_pos = QHBoxLayout()
        self.spin_pos_x = QDoubleSpinBox()
        self.spin_pos_x.setRange(-5000, 20000)
        self.spin_pos_x.setDecimals(1)
        self.spin_pos_x.setPrefix("X: ")
        self.spin_pos_x.setSuffix(" px")
        self.spin_pos_x.setEnabled(False)
        self.spin_pos_x.valueChanged.connect(self.apply_position_x)
        
        self.spin_pos_y = QDoubleSpinBox()
        self.spin_pos_y.setRange(-5000, 20000)
        self.spin_pos_y.setDecimals(1)
        self.spin_pos_y.setPrefix("Y: ")
        self.spin_pos_y.setSuffix(" px")
        self.spin_pos_y.setEnabled(False)
        self.spin_pos_y.valueChanged.connect(self.apply_position_y)
        
        row_pos.addWidget(self.spin_pos_x)
        row_pos.addWidget(self.spin_pos_y)
        ly_pos.addLayout(row_pos)
        right_layout.addWidget(grp_pos)
        self._add_separator(right_layout)

        container_misto = QWidget()
        layout_misto = QHBoxLayout(container_misto)
        layout_misto.setContentsMargins(0, 0, 0, 0)
        layout_misto.setSpacing(10)

        self.caixa_texto_panel = CaixaDeTextoPanel()
        self.caixa_texto_panel.setEnabled(False)
        self.caixa_texto_panel.widthChanged.connect(self.update_width)
        self.caixa_texto_panel.heightChanged.connect(self.update_height)
        self.caixa_texto_panel.rotationChanged.connect(self.update_rotation)
        layout_misto.addWidget(self.caixa_texto_panel, 1)

        v_sep = QFrame()
        v_sep.setFrameShape(QFrame.Shape.VLine)
        v_sep.setFrameShadow(QFrame.Shadow.Sunken)
        v_sep.setStyleSheet("color: #ccc;") 
        layout_misto.addWidget(v_sep)

        grp_cols_compact = QWidget()
        ly_cols_compact = QVBoxLayout(grp_cols_compact)
        ly_cols_compact.setContentsMargins(0, 0, 0, 0)
        ly_cols_compact.setSpacing(2)
        
        lbl_cols = QLabel("<b>ORDEM NA TABELA</b>")
        ly_cols_compact.addWidget(lbl_cols)

        self.lst_placeholders = QListWidget()
        self.lst_placeholders.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lst_placeholders.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lst_placeholders.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lst_placeholders.setFixedHeight(75) 
        ly_cols_compact.addWidget(self.lst_placeholders)
        
        layout_misto.addWidget(grp_cols_compact, 1)

        right_layout.addWidget(container_misto)
        self._add_separator(right_layout)

        self.editor_texto_panel = EditorDeTextoPanel()
        self.editor_texto_panel.setEnabled(False)

        self.editor_texto_panel.htmlChanged.connect(self.update_text_html)
        self.editor_texto_panel.htmlChanged.connect(self._on_content_updated)
        self.editor_texto_panel.fontFamilyChanged.connect(self.update_font_family)
        self.editor_texto_panel.fontSizeChanged.connect(self.update_font_size)
        self.editor_texto_panel.fontColorChanged.connect(self.update_font_color)
        self.editor_texto_panel.alignChanged.connect(self.update_align)
        self.editor_texto_panel.verticalAlignChanged.connect(self.update_vertical_align)
        self.editor_texto_panel.indentChanged.connect(self.update_indent)
        self.editor_texto_panel.lineHeightChanged.connect(self.update_line_height)
        right_layout.addWidget(self.editor_texto_panel)

        self._add_separator(right_layout)

        right_layout.addStretch()
        self.btn_save = QPushButton("Salvar Modelo (JSON)")
        self.btn_save.setMinimumHeight(50)
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; font-size: 14px;")
        self.btn_save.clicked.connect(self.export_to_json)
        right_layout.addWidget(self.btn_save)

        main_layout.addWidget(right_container)

        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.scene.changed.connect(self.update_position_ui)

        self.shortcut_dup = QShortcut(QKeySequence("Ctrl+J"), self)
        self.shortcut_dup.activated.connect(self.duplicate_selected)

        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.export_to_json)

        self.shortcut_bold = QShortcut(QKeySequence("Ctrl+B"), self)
        self.shortcut_bold.activated.connect(lambda: self.editor_texto_panel.btn_bold.click() if self.editor_texto_panel.isEnabled() else None)

        self.shortcut_italic = QShortcut(QKeySequence("Ctrl+I"), self)
        self.shortcut_italic.activated.connect(lambda: self.editor_texto_panel.btn_italic.click() if self.editor_texto_panel.isEnabled() else None)

        self.shortcut_underline = QShortcut(QKeySequence("Ctrl+U"), self)
        self.shortcut_underline.activated.connect(lambda: self.editor_texto_panel.btn_underline.click() if self.editor_texto_panel.isEnabled() else None)

    def showEvent(self, event):
        super().showEvent(event)
        self._zoom_to_fit()

    def _zoom_to_fit(self):
        if not self.scene.sceneRect().isEmpty():
            margin = 50
            view_rect = self.scene.sceneRect().adjusted(-margin, -margin, margin, margin)
            self.view.fitInView(view_rect, Qt.AspectRatioMode.KeepAspectRatio)
    
    def sync_placeholders_list(self):
        current_vars = set(self.get_all_model_placeholders())
        existing_items_map = {} 
        for i in range(self.lst_placeholders.count()):
            existing_items_map[self.lst_placeholders.item(i).text()] = i

        for i in range(self.lst_placeholders.count() - 1, -1, -1):
            txt = self.lst_placeholders.item(i).text()
            if txt not in current_vars:
                self.lst_placeholders.takeItem(i)

        for var in sorted(list(current_vars)):
            if var not in existing_items_map:
                self.lst_placeholders.addItem(var)
    
    def _import_asset(self, source_path: str, model_dir: Path) -> str | None:
        if not source_path: 
            return None
        
        src = Path(source_path)
        if not src.exists():
            return None
            
        if "assets" in src.parts and model_dir in src.parents:
            return f"assets/{src.name}"

        assets_dir = model_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        dest = assets_dir / src.name
        
        try:
            shutil.copy2(src, dest)
            return f"assets/{src.name}"
        except Exception as e:
            print(f"Erro ao copiar asset: {e}")
            return source_path 
    
    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

    def eventFilter(self, source, event):
        # Escuta tanto a view principal quanto o viewport das barras de rolagem
        if source in (self.view, self.view.viewport()):
            # --- 1. Zoom com Ctrl + Scroll ---
            if event.type() == QEvent.Type.Wheel and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
                self.view.scale(zoom_factor, zoom_factor)
                event.accept() # Mata o evento nativo de rolagem
                return True

            # --- Eventos de Teclado (Pressionar) ---
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                
                # 2. Ativar Pan (Mãozinha) ao segurar Espaço
                if key == Qt.Key.Key_Space and not event.isAutoRepeat():
                    self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                    return True
                
                if key == Qt.Key.Key_Delete:
                    selected = self.scene.selectedItems()
                    for item in selected: 
                        self.scene.removeItem(item)
                    self.on_selection_changed()
                    self.sync_placeholders_list()
                    self.refresh_layer_list() # Atualiza a lista para expurgar itens deletados
                    return True
                
                elif key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                    step = 10 if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1
                    dx = -step if key == Qt.Key.Key_Left else (step if key == Qt.Key.Key_Right else 0)
                    dy = -step if key == Qt.Key.Key_Up else (step if key == Qt.Key.Key_Down else 0)
                    sel_items = self.scene.selectedItems()
                    if sel_items:
                        for item in sel_items:
                            item.moveBy(dx, dy)
                        self.on_selection_changed() # Sincroniza a barra superior
                        return True

            # --- Eventos de Teclado (Soltar) ---
            elif event.type() == QEvent.Type.KeyRelease:
                # 3. Desativar Pan (Voltar para seleção) ao soltar Espaço
                if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
                    self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                    return True
        
        return super().eventFilter(source, event)

    def add_guide(self, vertical):
        rect = self.scene.sceneRect()
        if vertical:
            pos = rect.width() / 2
        else:
            pos = rect.height() / 2
        self.scene.addItem(Guideline(pos, is_vertical=vertical))

    def apply_position_x(self, val):
        sel = self.scene.selectedItems()
        if sel:
            item = sel[0]
            item.setPos(val, item.pos().y())

    def apply_position_y(self, val):
        sel = self.scene.selectedItems()
        if sel:
            item = sel[0]
            item.setPos(item.pos().x(), val)

    def add_new_box(self):
        box = DesignerBox(350, 450, 300, 60, "{campo}")
        self.scene.addItem(box)
        self.scene.clearSelection()
        box.setSelected(True)
        self.refresh_layer_list()

    def update_position_ui(self):
        """Atualiza os campos X e Y no topo em tempo real."""
        try:
            sel = self.scene.selectedItems()
        except RuntimeError:
            return # Aborta silenciosamente se a cena já foi destruída (ao fechar o app)
            
        if not sel:
            self.spin_pos_x.setEnabled(False)
            self.spin_pos_y.setEnabled(False)
            return

        item = sel[0]
        self.spin_pos_x.blockSignals(True)
        self.spin_pos_y.blockSignals(True)
        
        self.spin_pos_x.setEnabled(True)
        self.spin_pos_y.setEnabled(True)

        if isinstance(item, Guideline):
            if item.is_vertical:
                self.spin_pos_x.setValue(item.pos().x())
                self.spin_pos_y.setEnabled(False)
            else:
                self.spin_pos_y.setValue(item.pos().y())
                self.spin_pos_x.setEnabled(False)
        else:
            self.spin_pos_x.setValue(item.pos().x())
            self.spin_pos_y.setValue(item.pos().y())

        # Sincroniza Largura e Altura no painel
        if isinstance(item, DesignerBox):
            self.caixa_texto_panel.blockSignals(True)
            self.caixa_texto_panel.spin_w.setValue(int(item.rect().width()))
            self.caixa_texto_panel.spin_h.setValue(int(item.rect().height()))
            self.caixa_texto_panel.blockSignals(False)
        elif isinstance(item, (ImageItem, SignatureItem)):
            self.caixa_texto_panel.blockSignals(True)
            rect = item.pixmap().rect()
            self.caixa_texto_panel.spin_w.setValue(int(rect.width()))
            self.caixa_texto_panel.spin_h.setValue(int(rect.height()))
            self.caixa_texto_panel.blockSignals(False)

        self.spin_pos_x.blockSignals(False)
        self.spin_pos_y.blockSignals(False)

    def on_selection_changed(self):
        """Gerencia a troca de painéis laterais quando a seleção muda."""
        try:
            sel = self.scene.selectedItems()
        except RuntimeError:
            return 
            
        boxes = [i for i in sel if isinstance(i, DesignerBox)]
        images = [i for i in sel if isinstance(i, ImageItem)]
        signatures = [i for i in sel if isinstance(i, SignatureItem)]
        
        self.update_position_ui()

        if boxes:
            target_box = boxes[0]
            self.editor_texto_panel.load_from_item(target_box)
            self.editor_texto_panel.setEnabled(True)
            self.caixa_texto_panel.load_from_item(target_box)
            self.caixa_texto_panel.setEnabled(True)
        elif images or signatures:
            target = images[0] if images else signatures[0]
            self.editor_texto_panel.setEnabled(False)
            self.caixa_texto_panel.load_from_image(target)
            self.caixa_texto_panel.setEnabled(True)
        else:
            self.editor_texto_panel.setEnabled(False)
            self.caixa_texto_panel.setEnabled(False)


    def duplicate_selected(self):
        original = self._get_selected()
        if not original: return

        offset = 20
        new_x = original.x() + offset
        new_y = original.y() + offset
        rect = original.rect()
        
        new_box = DesignerBox(new_x, new_y, rect.width(), rect.height(), "")
        new_box.layer_id = None 
        
        import copy
        new_box.state = copy.deepcopy(original.state)
        new_box.setRotation(original.rotation())
        new_box.apply_state()
        new_box.update_center()

        self.scene.addItem(new_box)
        self.refresh_layer_list()
        
        self.scene.clearSelection()
        new_box.setSelected(True)
        self.sync_placeholders_list()

    def _get_selected(self):
        sel = self.scene.selectedItems()
        valid_items = [i for i in sel if isinstance(i, (DesignerBox, ImageItem, SignatureItem))]
        return valid_items[0] if valid_items else None

    def update_text_html(self, html_content):
        box = self._get_selected()
        if box: 
            box.state.html_content = html_content
            box.apply_state()
    
    def update_font_family(self, font):
        box = self._get_selected()
        if box:
            box.state.font_family = font.family()
            box.apply_state()

    def update_font_size(self, size):
        box = self._get_selected()
        if box:
            box.state.font_size = size
            box.apply_state()

    def update_font_color(self, color_hex):
        box = self._get_selected()
        if box:
            box.state.font_color = color_hex
            box.apply_state()

    def update_width(self, width):
        item = self._get_selected()
        if item:
            if isinstance(item, DesignerBox):
                r = item.rect()
                item.setRect(0, 0, width, r.height())
                item.recalculate_text_position()
                item.update_center() 
            elif isinstance(item, (ImageItem, SignatureItem)):
                h = self.caixa_texto_panel.spin_h.value()
                item.resize_custom(width, h)

    def update_height(self, height):
        item = self._get_selected()
        if item:
            if isinstance(item, DesignerBox):
                r = item.rect()
                item.setRect(0, 0, r.width(), height)
                item.recalculate_text_position()
                item.update_center()
            elif isinstance(item, (ImageItem, SignatureItem)):
                w = self.caixa_texto_panel.spin_w.value()
                item.resize_custom(w, height)

    def update_rotation(self, angle):
        item = self._get_selected()
        if item:
            item.setRotation(angle)
            if isinstance(item, (ImageItem, SignatureItem)):
                rect = item.pixmap().rect()
                item.setTransformOriginPoint(rect.width() / 2, rect.height() / 2)

    def update_align(self, align_str):
        box = self._get_selected()
        if box: box.set_alignment(align_str)

    def update_vertical_align(self, align_str):
        box = self._get_selected()
        if box: box.set_vertical_alignment(align_str)

    def update_indent(self, val):
        box = self._get_selected()
        if box: box.set_block_format(indent=val)

    def update_line_height(self, val):
        box = self._get_selected()
        if box: box.set_block_format(line_height=val)

    def export_to_json(self):
        boxes_data = []
        signatures_data = []
        images_data = []
        
        for item in self.scene.items():
            if isinstance(item, DesignerBox):
                pos = item.pos()
                r = item.rect()

                boxes_data.append({
                    "id": item.text_item.toPlainText().replace("{", "").replace("}", "").strip(),
                    "html": item.state.html_content,
                    "visible": item.isVisible(),
                    "x": int(pos.x()),
                    "y": int(pos.y()),
                    "w": int(r.width()),
                    "h": int(r.height()),
                    "rotation": int(item.rotation()),
                    "font_family": item.state.font_family,
                    "font_size": item.state.font_size,
                    "font_color": getattr(item.state, 'font_color', '#000000'),
                    "align": item.state.align,
                    "vertical_align": item.state.vertical_align,
                    "indent_px": item.state.indent_px,
                    "line_height": item.state.line_height
                })
            
            elif isinstance(item, SignatureItem):
                pos = item.pos()
                pix = item.pixmap()
                signatures_data.append({
                    "path": getattr(item, "_original_path", ""), 
                    "visible": item.isVisible(),
                    "x": int(pos.x()),
                    "y": int(pos.y()),
                    "width": int(pix.width()),
                    "height": int(pix.height()),
                    "longest_side": max(pix.width(), pix.height())
                })

            elif isinstance(item, ImageItem):
                pos = item.pos()
                pix = item.pixmap()
                images_data.append({
                    "path": getattr(item, "_original_path", ""), 
                    "visible": item.isVisible(),
                    "x": int(pos.x()),
                    "y": int(pos.y()),
                    "width": int(pix.width()),
                    "height": int(pix.height()),
                    "longest_side": max(pix.width(), pix.height()),
                    "rotation": int(item.rotation())
                })

        ordered_placeholders = []
        for i in range(self.lst_placeholders.count()):
            ordered_placeholders.append(self.lst_placeholders.item(i).text())

        data = {
            "name": "modelo_v3_projeto",
            "canvas_size": {"w": int(self.scene.width()), "h": int(self.scene.height())},
            "target_w_mm": self.spin_phys_w.value(),
            "target_h_mm": self.spin_phys_h.value(),
            "background_path": self.background_path,
            "placeholders": ordered_placeholders,
            "signatures": signatures_data,
            "images": images_data,
            "boxes": boxes_data
        }
                
        model_name = self.windowTitle().replace("Editor Visual de Modelo - ", "")
        if not model_name or "Gerador de Cartões em Lote - GCL" in model_name:
            model_name, ok = QInputDialog.getText(self, "Salvar Modelo", "Nome do Modelo:")
            if not ok or not model_name: return
            self.setWindowTitle(f"Editor Visual de Modelo - {model_name}")

        slug = slugify_model_name(model_name)
        model_dir = get_models_dir() / slug
        model_dir.mkdir(parents=True, exist_ok=True)
        
        if self.background_path:
            rel_bg = self._import_asset(self.background_path, model_dir)
            data["background_path"] = rel_bg

        for sig in data["signatures"]:
            rel_sig = self._import_asset(sig["path"], model_dir)
            if rel_sig:
                sig["path"] = rel_sig

        for img in data.get("images", []):
            rel_img = self._import_asset(img["path"], model_dir)
            if rel_img:
                img["path"] = rel_img

        file_path = model_dir / "template_v3.json"
        
        data["name"] = model_name
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        self.modelSaved.emit(model_name, data["placeholders"])
        
        QMessageBox.information(self, "Sucesso", f"Modelo '{model_name}' salvo com sucesso em:\n{file_path}")

    
    def load_background_image(self, path):
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
        
        if self.bg_item:
            self.scene.removeItem(self.bg_item)
            
        self.background_path = path
        self.bg_item = self.scene.addPixmap(pixmap)
        self.bg_item.setZValue(-100) 
        
        rect = pixmap.rect()
        self.scene.setSceneRect(rect)
        self.view.setSceneRect(rect)
        
        self.fallback_bg.hide()
        self._zoom_to_fit()

    def _on_click_load_bg(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Fundo", "", "Imagens (*.png *.jpg *.jpeg)")
        if path:
            self.load_background_image(path)


    def _on_click_add_signature(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Assinatura", "", "Imagens (*.png)")
        if path:
            sig = SignatureItem(path)
            center = self.view.mapToScene(self.view.viewport().rect().center())
            sig.setPos(center)
            self.scene.addItem(sig)

    def _on_click_add_image(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg)")
        if path:
            img = ImageItem(path)
            center = self.view.mapToScene(self.view.viewport().rect().center())
            img.setPos(center)
            
            # Trava automática no Z-Value topo da faixa de Imagens
            base_z = 1
            for item in self.scene.items():
                if isinstance(item, ImageItem) and item.zValue() >= base_z:
                    base_z = int(item.zValue()) + 1
            img.setZValue(min(base_z, 100))
            
            self.scene.addItem(img)
            self.refresh_layer_list()

    def get_all_model_placeholders(self):
        placeholders = set()
        for item in self.scene.items():
            if isinstance(item, DesignerBox):
                placeholders.update(item.get_placeholders())
        return sorted(list(placeholders))
    
    def _on_content_updated(self, html):
        self.update_text_html(html)
        self.sync_placeholders_list()
        self.refresh_layer_list()

    def load_from_json(self, file_path):
        import json
        path = Path(file_path)
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.scene.clear()
        self.background_path = None
        self.bg_item = None
        
        canvas_w = data.get("canvas_size", {}).get("w", 1000)
        canvas_h = data.get("canvas_size", {}).get("h", 1000)
        self.scene.setSceneRect(0, 0, canvas_w, canvas_h)

        if hasattr(self, 'spin_phys_w'):
            self.spin_phys_w.setValue(data.get("target_w_mm", 100.0))
            self.spin_phys_h.setValue(data.get("target_h_mm", 150.0))
        
        self.fallback_bg = self.scene.addRect(0, 0, canvas_w, canvas_h, QPen(Qt.PenStyle.NoPen), QBrush(Qt.GlobalColor.white))
        self.fallback_bg.setZValue(-100)

        if data.get("background_path"):
            bg_path_raw = data["background_path"]
            bg_path = path.parent / bg_path_raw if not Path(bg_path_raw).is_absolute() else Path(bg_path_raw)
            
            if bg_path.exists():
                self.load_background_image(str(bg_path))

        from .canvas_items import SignatureItem, ImageItem
        for sig_data in data.get("signatures", []):
            raw_path = sig_data["path"]
            sig_path = path.parent / raw_path if not Path(raw_path).is_absolute() else Path(raw_path)

            if sig_path.exists():
                sig = SignatureItem(str(sig_path))
                sig.setPos(sig_data["x"], sig_data["y"])
                sig.resize_by_longest_side(sig_data["longest_side"])
                self.scene.addItem(sig)
                sig.setVisible(sig_data.get("visible", True))

        for img_data in data.get("images", []):
            raw_path = img_data["path"]
            img_path = path.parent / raw_path if not Path(raw_path).is_absolute() else Path(raw_path)

            if img_path.exists():
                img = ImageItem(str(img_path))
                img.setPos(img_data["x"], img_data["y"])
                
                if "width" in img_data and "height" in img_data:
                    img.resize_custom(img_data["width"], img_data["height"])
                else:
                    img.resize_by_longest_side(img_data.get("longest_side", 100))
                    
                img.setRotation(img_data.get("rotation", 0))
                self.scene.addItem(img)
                img.setVisible(img_data.get("visible", True))

        for b in data.get("boxes", []):
            box = DesignerBox(
                x=b.get("x", 0), 
                y=b.get("y", 0), 
                w=b.get("w", 300), 
                h=b.get("h", 60), 
                text=b.get("id", "Placeholder") 
            )
            
            if "html" in b:
                box.state.html_content = b["html"]
                
            box.state.font_family = b.get("font_family", "Arial")
            box.state.font_size = b.get("font_size", 16)
            box.state.font_color = b.get("font_color", "#000000")
            box.state.vertical_align = b.get("vertical_align", "top")
            box.state.align = b.get("align", "left")
            box.state.indent_px = b.get("indent_px", 0)
            box.state.line_height = b.get("line_height", 1.15)

            box.setRotation(b.get("rotation", 0))
            box.apply_state()
            box.update_center() 

            self.scene.addItem(box)
            box.setVisible(b.get("visible", True))

            saved_placeholders = data.get("placeholders", [])
            self.lst_placeholders.clear()
            for p in saved_placeholders:
                self.lst_placeholders.addItem(p)
            self.sync_placeholders_list()
        self._zoom_to_fit()

        self.setWindowTitle(f"Editor Visual de Modelo - {data['name']}")
        self.refresh_layer_list()

    def _get_next_layer_id(self):
        used = set()
        for item in self.scene.items():
            if hasattr(item, 'layer_id') and item.layer_id is not None:
                used.add(item.layer_id)
        for i in range(100):
            if i not in used: return i
        return 99

    def _generate_layer_name(self, layer_id, item):
        prefix = f"{layer_id:02d}"
        if isinstance(item, DesignerBox):
            raw = item.text_item.toPlainText().strip().replace("\n", " ")
            if len(raw) > 15: raw = raw[:12] + "..."
            if not raw: raw = "{vazio}"
            return f"{prefix}_{raw}"
        elif isinstance(item, SignatureItem):
            return f"{prefix}_Assinatura"
        elif isinstance(item, ImageItem):
            return f"{prefix}_Imagem"
        if item == self.bg_item:
            return f"{prefix}_Fundo"
        return f"{prefix}_Objeto"

    def refresh_layer_list(self):
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        
        assinaturas = []
        textos = []
        imagens = []
        fundo = None
        
        for item in self.scene.items():
            if item == self.bg_item: fundo = item
            elif isinstance(item, SignatureItem): assinaturas.append(item)
            elif isinstance(item, DesignerBox): textos.append(item)
            elif isinstance(item, ImageItem): imagens.append(item)
            
            if not hasattr(item, 'layer_id') or item.layer_id is None:
                item.layer_id = self._get_next_layer_id()

        assinaturas.sort(key=lambda x: x.zValue(), reverse=True)
        textos.sort(key=lambda x: x.zValue(), reverse=True)
        imagens.sort(key=lambda x: x.zValue(), reverse=True)

        def add_header(title):
            header = QListWidgetItem(f"--- {title} ---")
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            from PySide6.QtGui import QBrush, QColor
            header.setBackground(QBrush(QColor("#e0e0e0")))
            header.setForeground(QBrush(QColor("#555555")))
            self.layer_list.addItem(header)

        def add_items(item_list):
            for item in item_list:
                name = self._generate_layer_name(item.layer_id, item)
                list_item = QListWidgetItem(name)
                list_item.setData(Qt.ItemDataRole.UserRole, item)
                flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsUserCheckable
                list_item.setFlags(flags)
                list_item.setCheckState(Qt.CheckState.Checked if item.isVisible() else Qt.CheckState.Unchecked)
                self.layer_list.addItem(list_item)

        if assinaturas:
            add_header("ASSINATURAS")
            add_items(assinaturas)
            
        if textos:
            add_header("TEXTOS")
            add_items(textos)
        
        if imagens:
            add_header("IMAGENS")
            add_items(imagens)
            
        if fundo:
            add_header("FUNDO")
            add_items([fundo])

        self.layer_list.blockSignals(False)

    def _on_layer_list_clicked(self, list_item):
        target_item = list_item.data(Qt.ItemDataRole.UserRole)
        if target_item:
            self.scene.clearSelection()
            target_item.setSelected(True)
            self.view.ensureVisible(target_item)
            self.view.setFocus()

    def _on_layer_item_changed(self, list_item):
        target_item = list_item.data(Qt.ItemDataRole.UserRole)
        if target_item:
            is_visible = (list_item.checkState() == Qt.CheckState.Checked)
            target_item.setVisible(is_visible)

    def _on_layer_reordered(self, parent, start, end, destination, row):
        count = self.layer_list.count()
        items_in_order = []
        
        for i in range(count):
            list_item = self.layer_list.item(i)
            target = list_item.data(Qt.ItemDataRole.UserRole)
            if target:
                items_in_order.append(target)
                
        assinaturas = [i for i in items_in_order if isinstance(i, SignatureItem)]
        textos = [i for i in items_in_order if isinstance(i, DesignerBox)]
        imagens = [i for i in items_in_order if isinstance(i, ImageItem)]
        
        # Blinda o Z-Value matematicamente, não importa pra onde o usuário tentou arrastar
        for i, item in enumerate(assinaturas): item.setZValue(250 - i)
        for i, item in enumerate(textos): item.setZValue(200 - i)
        for i, item in enumerate(imagens): item.setZValue(100 - i)
        
        # Redesenha forçadamente para que o item "pule" de volta para a sua seção correta caso tenha sido arrastado pra fora dela
        self.refresh_layer_list()