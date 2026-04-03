import json
from PySide6.QtWidgets import (QMainWindow, QGraphicsView, QGraphicsScene, QWidget, 
                               QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, 
                               QMessageBox, QInputDialog, QListWidget, QAbstractItemView,
                               QListWidgetItem, QDoubleSpinBox)
from PySide6.QtGui import (QPainter, QBrush, QPen, QColor, QShortcut, 
                           QKeySequence, QTextCursor, QTextCharFormat)
from PySide6.QtCore import Qt, Signal, QEvent
from pathlib import Path
import shutil

from .canvas_items import DesignerBox, Guideline, px_to_mm, SignatureItem
from .properties import CaixaDeTextoPanel, EditorDeTextoPanel, AssinaturaPanel
from core.template_manager import slugify_model_name

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
        self.view.installEventFilter(self)
        
        self.bg_item = None  
        self.background_path = None
        
        self.fallback_bg = self.scene.addRect(0, 0, 1000, 1000, QPen(Qt.PenStyle.NoPen), QBrush(Qt.GlobalColor.white))
        self.fallback_bg.setZValue(-100)
        
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        self.top_bar = QWidget()
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(10, 5, 10, 5)
        top_layout.addWidget(QLabel("<b>POSIÇÃO DO ITEM (X, Y):</b>"))
        
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
        
        top_layout.addWidget(self.spin_pos_x)
        top_layout.addWidget(self.spin_pos_y)
        top_layout.addStretch()
        
        center_layout.addWidget(self.top_bar)
        center_layout.addWidget(self.view, 1)
        
        main_layout.addWidget(center_container, 1)

        right_container = QWidget()
        right_container.setFixedWidth(400)
        right_layout = QVBoxLayout(right_container)
        
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

        right_layout.addWidget(grp_guides)
        self._add_separator(right_layout)

        grp_boxes = QFrame()
        ly_boxes = QVBoxLayout(grp_boxes)
        ly_boxes.setContentsMargins(0, 0, 0, 10)
        ly_boxes.addWidget(QLabel("<b>ELEMENTOS</b>"))
        
        self.btn_add = QPushButton("+ Adicionar Caixa Texto")
        self.btn_add.setMinimumHeight(40)
        self.btn_add.clicked.connect(self.add_new_box)
        ly_boxes.addWidget(self.btn_add)

        row_assets = QHBoxLayout()
        row_assets.setSpacing(10)

        self.btn_add_bg = QPushButton("🖼️ Fundo")
        self.btn_add_bg.setToolTip("Definir imagem de fundo")
        self.btn_add_bg.setMinimumHeight(40)
        self.btn_add_bg.clicked.connect(self._on_click_load_bg)
        
        self.btn_add_sig = QPushButton("✍️ Assinatura")
        self.btn_add_sig.setToolTip("Adicionar imagem de assinatura")
        self.btn_add_sig.setMinimumHeight(40)
        self.btn_add_sig.clicked.connect(self._on_click_add_signature)
        
        row_assets.addWidget(self.btn_add_bg)
        row_assets.addWidget(self.btn_add_sig)
        ly_boxes.addLayout(row_assets)

        right_layout.addWidget(grp_boxes)
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
        self.editor_texto_panel.alignChanged.connect(self.update_align)
        self.editor_texto_panel.verticalAlignChanged.connect(self.update_vertical_align)
        self.editor_texto_panel.indentChanged.connect(self.update_indent)
        self.editor_texto_panel.lineHeightChanged.connect(self.update_line_height)
        right_layout.addWidget(self.editor_texto_panel)

        self.assinatura_panel = AssinaturaPanel()
        self.assinatura_panel.setVisible(False)
        self.assinatura_panel.sideChanged.connect(self.update_signature_size)
        right_layout.addWidget(self.assinatura_panel)

        self._add_separator(right_layout)
        
        grp_doc = QFrame()
        ly_doc = QVBoxLayout(grp_doc)
        ly_doc.setContentsMargins(0, 0, 0, 0)
        lbl_doc = QLabel("<b>DIMENSÕES DO DOCUMENTO</b> <small style='color:gray'>(Ajuste Proporcional)</small>")
        ly_doc.addWidget(lbl_doc)
        
        row_doc = QHBoxLayout()
        from PySide6.QtWidgets import QSpinBox
        self.spin_doc_w = QSpinBox()
        self.spin_doc_w.setRange(10, 20000)
        self.spin_doc_w.setSuffix(" px")
        self.spin_doc_w.setPrefix("Largura: ")
        self.spin_doc_w.setEnabled(False)
        
        self.spin_doc_h = QSpinBox()
        self.spin_doc_h.setRange(10, 20000)
        self.spin_doc_h.setSuffix(" px")
        self.spin_doc_h.setPrefix("Altura: ")
        self.spin_doc_h.setReadOnly(True) # A altura é calculada automaticamente
        
        self.btn_apply_doc_size = QPushButton("Aplicar Novo Tamanho")
        self.btn_apply_doc_size.setEnabled(False)
        self.btn_apply_doc_size.clicked.connect(self.apply_document_resize)
        
        row_doc.addWidget(self.spin_doc_w)
        row_doc.addWidget(self.spin_doc_h)
        ly_doc.addLayout(row_doc)
        ly_doc.addWidget(self.btn_apply_doc_size)
        
        right_layout.addWidget(grp_doc)
        self.spin_doc_w.valueChanged.connect(self._on_doc_w_changed)

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
        if source == self.view:
            # --- 1. Zoom com Ctrl + Scroll ---
            if event.type() == QEvent.Type.Wheel and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
                self.view.scale(zoom_factor, zoom_factor)
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

        # Sincroniza Largura e Altura no painel se for uma Caixa de Texto sendo arrastada pela alça
        if isinstance(item, DesignerBox):
            self.caixa_texto_panel.blockSignals(True)
            self.caixa_texto_panel.spin_w.setValue(int(item.rect().width()))
            self.caixa_texto_panel.spin_h.setValue(int(item.rect().height()))
            self.caixa_texto_panel.blockSignals(False)

        self.spin_pos_x.blockSignals(False)
        self.spin_pos_y.blockSignals(False)

    def on_selection_changed(self):
        """Gerencia a troca de painéis laterais quando a seleção muda."""
        try:
            sel = self.scene.selectedItems()
        except RuntimeError:
            return # Aborta silenciosamente se a cena já foi destruída (ao fechar o app)
            
        boxes = [i for i in sel if isinstance(i, DesignerBox)]
        signatures = [i for i in sel if isinstance(i, SignatureItem)]
        
        # Atualiza a posição X/Y imediatamente ao selecionar
        self.update_position_ui()

        if boxes:
            target_box = boxes[0]
            self.editor_texto_panel.load_from_item(target_box)
            self.editor_texto_panel.setEnabled(True)
            self.caixa_texto_panel.load_from_item(target_box)
            self.caixa_texto_panel.setEnabled(True)
        else:
            self.editor_texto_panel.setEnabled(False)
            self.caixa_texto_panel.setEnabled(False)

        if signatures:
            self.assinatura_panel.load_from_item(signatures[0])
            self.assinatura_panel.setVisible(True)
        else:
            self.assinatura_panel.setVisible(False)

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

    def _get_selected(self) -> DesignerBox | None:
        sel = self.scene.selectedItems()
        boxes = [i for i in sel if isinstance(i, DesignerBox)]
        return boxes[0] if boxes else None

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

    def update_width(self, width):
        box = self._get_selected()
        if box:
            r = box.rect()
            box.setRect(0, 0, width, r.height())
            box.recalculate_text_position()
            box.update_center() 

    def update_height(self, height):
        box = self._get_selected()
        if box:
            r = box.rect()
            box.setRect(0, 0, r.width(), height)
            box.recalculate_text_position()
            box.update_center() 

    def update_rotation(self, angle):
        box = self._get_selected()
        if box:
            box.setRotation(angle)

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
        
        for item in self.scene.items():
            if isinstance(item, DesignerBox):
                pos = item.pos()
                r = item.rect()

                boxes_data.append({
                    "id": item.text_item.toPlainText().replace("{", "").replace("}", "").strip(),
                    "html": item.state.html_content,
                    "x": int(pos.x()),
                    "y": int(pos.y()),
                    "w": int(r.width()),
                    "h": int(r.height()),
                    "rotation": int(item.rotation()),
                    "font_family": item.state.font_family,
                    "font_size": item.state.font_size,
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
                    "x": int(pos.x()),
                    "y": int(pos.y()),
                    "width": int(pix.width()),
                    "height": int(pix.height()),
                    "longest_side": max(pix.width(), pix.height())
                })

        ordered_placeholders = []
        for i in range(self.lst_placeholders.count()):
            ordered_placeholders.append(self.lst_placeholders.item(i).text())

        data = {
            "name": "modelo_v3_projeto",
            "canvas_size": {"w": int(self.scene.width()), "h": int(self.scene.height())},
            "background_path": self.background_path,
            "placeholders": ordered_placeholders,
            "signatures": signatures_data,
            "boxes": boxes_data
        }
                
        model_name = self.windowTitle().replace("Editor Visual de Modelo - ", "")
        if not model_name or "Gerador de Cartões em Lote - GCL" in model_name:
            model_name, ok = QInputDialog.getText(self, "Salvar Modelo", "Nome do Modelo:")
            if not ok or not model_name: return
            self.setWindowTitle(f"Editor Visual de Modelo - {model_name}")

        slug = slugify_model_name(model_name)
        model_dir = Path("models") / slug
        model_dir.mkdir(parents=True, exist_ok=True)
        
        if self.background_path:
            rel_bg = self._import_asset(self.background_path, model_dir)
            data["background_path"] = rel_bg

        for sig in data["signatures"]:
            rel_sig = self._import_asset(sig["path"], model_dir)
            if rel_sig:
                sig["path"] = rel_sig

        file_path = model_dir / "template_v3.json"
        
        data["name"] = model_name
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        self.modelSaved.emit(model_name, data["placeholders"])
        
        QMessageBox.information(self, "Sucesso", f"Modelo '{model_name}' salvo com sucesso em:\n{file_path}")

    def update_signature_size(self, size):
        sel = self.scene.selectedItems()
        if sel and isinstance(sel[0], SignatureItem):
            sel[0].resize_by_longest_side(size)
    
    def load_background_image(self, path):
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
        
        if self.bg_item:
            self.scene.removeItem(self.bg_item)
            
        self.background_path = path
        self.bg_item = self.scene.addPixmap(pixmap)
        self.bg_item.setZValue(-95) 
        
        rect = pixmap.rect()
        self.scene.setSceneRect(rect)
        self.view.setSceneRect(rect)
        
        self.fallback_bg.hide()
        self._zoom_to_fit()
        
        # --- Ativar e popular controles de dimensão do documento ---
        if hasattr(self, 'spin_doc_w'):
            self.spin_doc_w.blockSignals(True)
            self.spin_doc_w.setValue(rect.width())
            self.spin_doc_h.setValue(rect.height())
            self._doc_aspect_ratio = rect.width() / rect.height() if rect.height() > 0 else 1
            self.spin_doc_w.setEnabled(True)
            self.btn_apply_doc_size.setEnabled(True)
            self.spin_doc_w.blockSignals(False)

    def _on_click_load_bg(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Fundo", "", "Imagens (*.png *.jpg *.jpeg)")
        if path:
            self.load_background_image(path)

    def _on_doc_w_changed(self, new_w):
        if hasattr(self, '_doc_aspect_ratio'):
            new_h = int(new_w / self._doc_aspect_ratio)
            self.spin_doc_h.setValue(new_h)

    def apply_document_resize(self):
        if not self.bg_item or not self.background_path:
            return
            
        from PySide6.QtGui import QPixmap
        new_w = self.spin_doc_w.value()
        new_h = self.spin_doc_h.value()
        
        # Recarrega a imagem original e aplica o redimensionamento suave
        pixmap = QPixmap(self.background_path)
        scaled_pixmap = pixmap.scaled(new_w, new_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.bg_item.setPixmap(scaled_pixmap)
        
        # Ajusta os limites do palco (canvas) para o novo tamanho
        rect = scaled_pixmap.rect()
        self.scene.setSceneRect(rect)
        self.view.setSceneRect(rect)
        self._zoom_to_fit()

    def _on_click_add_signature(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Assinatura", "", "Imagens (*.png)")
        if path:
            sig = SignatureItem(path)
            center = self.view.mapToScene(self.view.viewport().rect().center())
            sig.setPos(center)
            self.scene.addItem(sig)

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
        
        self.fallback_bg = self.scene.addRect(0, 0, canvas_w, canvas_h, QPen(Qt.PenStyle.NoPen), QBrush(Qt.GlobalColor.white))
        self.fallback_bg.setZValue(-100)

        if data.get("background_path"):
            bg_path_raw = data["background_path"]
            bg_path = path.parent / bg_path_raw if not Path(bg_path_raw).is_absolute() else Path(bg_path_raw)
            
            if bg_path.exists():
                self.load_background_image(str(bg_path))

        from .canvas_items import SignatureItem
        for sig_data in data.get("signatures", []):
            raw_path = sig_data["path"]
            sig_path = path.parent / raw_path if not Path(raw_path).is_absolute() else Path(raw_path)

            if sig_path.exists():
                sig = SignatureItem(str(sig_path))
                sig.setPos(sig_data["x"], sig_data["y"])
                sig.resize_by_longest_side(sig_data["longest_side"])
                self.scene.addItem(sig)

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
            box.state.vertical_align = b.get("vertical_align", "top")
            box.state.align = b.get("align", "left")
            box.state.indent_px = b.get("indent_px", 0)
            box.state.line_height = b.get("line_height", 1.15)

            box.setRotation(b.get("rotation", 0))
            box.apply_state()
            box.update_center() 

            self.scene.addItem(box)

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
        if item == self.bg_item:
            return f"{prefix}_Fundo"
        return f"{prefix}_Objeto"

    def refresh_layer_list(self):
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        items = self.scene.items()
        
        valid_items = []
        for item in items:
            if isinstance(item, (DesignerBox, SignatureItem)) or item == self.bg_item:
                valid_items.append(item)
                if not hasattr(item, 'layer_id') or item.layer_id is None:
                    item.layer_id = self._get_next_layer_id()

        # Ordenar do maior Z-Value (topo visual) para o menor
        valid_items.sort(key=lambda x: x.zValue(), reverse=True)

        for item in valid_items:
            name = self._generate_layer_name(item.layer_id, item)
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            # Adiciona Checkbox (Nativo) e mantém permissão de Drag
            flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsUserCheckable
            list_item.setFlags(flags)
            list_item.setCheckState(Qt.CheckState.Checked if item.isVisible() else Qt.CheckState.Unchecked)
            
            self.layer_list.addItem(list_item)
            
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
                
        # Extrai os Z-Values existentes e ordena do maior para o menor
        available_zs = sorted([item.zValue() for item in items_in_order], reverse=True)
        
        # Redistribui as profundidades na nova ordem garantindo coerência
        for i, target in enumerate(items_in_order):
            target.setZValue(available_zs[i])