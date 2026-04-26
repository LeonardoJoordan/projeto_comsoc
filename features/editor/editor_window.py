import json
import copy
import shutil
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QGraphicsView, QGraphicsScene, QWidget,
                               QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton,
                               QMessageBox, QInputDialog, QListWidget, QAbstractItemView,
                               QListWidgetItem, QDoubleSpinBox, QComboBox, QGraphicsItem,
                               QFileDialog, QGraphicsOpacityEffect, QFormLayout)
from PySide6.QtGui import (QPainter, QBrush, QPen, QColor, QShortcut,
                           QKeySequence, QTextCursor, QTextCharFormat, QImageReader, QPixmap)
from PySide6.QtCore import Qt, Signal, QEvent, QRectF

from .canvas_items import DesignerBox, Guideline, px_to_mm, mm_to_px, SignatureItem, ImageItem, BackgroundItem
from .properties import CaixaDeTextoPanel, EditorDeTextoPanel
from core.template_manager import slugify_model_name
from core.history_manager import HistoryManager
from core.paths import get_models_dir
from core.custom_widgets import MathDoubleSpinBox




class EditorWindow(QMainWindow):
    modelSaved = Signal(str, list)

    def _apply_tooltip(self, widget, text):
        """Aplica tooltip e garante que labels estáticos capturem o evento no motor customizado."""
        if isinstance(widget, QLabel):
            widget.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        widget.setToolTip(text)

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
        # --- Cabecalho das Linhas Guia com Botões de Controle ---
        row_title_guides = QHBoxLayout()
        row_title_guides.setContentsMargins(0, 10, 0, 0)
        
        lbl_guides = QLabel("LINHAS GUIA")
        lbl_guides.setStyleSheet("font-weight: bold; font-size: 12px;")
        self._apply_tooltip(lbl_guides, 
            "<b>LINHAS GUIA</b><br><br>"
            "Ferramentas de apoio visual projetadas para auxiliar no posicionamento e simetria dos elementos na prancheta.<br><br>"
            "• <b>Apenas Referência:</b> São guias exclusivas do editor e <b>não aparecem na arte final</b> impressa.<br>"
            "• <b>Atração (Snap):</b> Possuem magnetismo automático para o centro e para as bordas do canvas.<br>"
            "• <b>Controle Total:</b> Podem ser ocultadas (👁️) ou bloqueadas (🔒) para não atrapalhar a edição de outros itens.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Selecione uma linha guia e digite o valor exato no painel 'POSIÇÃO (mm)' para obter um alinhamento milimétrico perfeito.</small>"
        )
        
        # Estilo minimalista para os botões do título (sem borda, fundo transparente)
        btn_icon_style = """
            QPushButton { background-color: transparent; border: none; font-size: 14px; }
            QPushButton:hover { background-color: #444444; border-radius: 4px; }
            QPushButton:pressed { background-color: #222222; }
        """
        
        self.btn_toggle_guides = QPushButton("👁️")
        self.btn_toggle_guides.setFixedSize(26, 26)
        self.btn_toggle_guides.setStyleSheet(btn_icon_style)
        self.btn_toggle_guides.setCheckable(True)
        self.btn_toggle_guides.setChecked(True)
        self._apply_tooltip(self.btn_toggle_guides, 
            "<b>MOSTRAR/OCULTAR GUIAS</b><br><br>"
            "Alterna temporariamente a visibilidade de todas as linhas guia.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Desligue as guias rapidamente para ter uma visão limpa da arte e conferir o design sem poluição visual.</small>"
        )
        self.btn_toggle_guides.toggled.connect(self.toggle_guides_visibility)
        # Efeito de opacidade para o olho
        self.op_eye = QGraphicsOpacityEffect(self.btn_toggle_guides)
        self.btn_toggle_guides.setGraphicsEffect(self.op_eye)
        self.op_eye.setOpacity(1.0 if self.btn_toggle_guides.isChecked() else 0.2)
        
        self.btn_clear_guides = QPushButton("🗑️")
        self.btn_clear_guides.setFixedSize(26, 26)
        self.btn_clear_guides.setStyleSheet(btn_icon_style)
        self._apply_tooltip(self.btn_clear_guides, 
            "<b>LIMPAR TODAS AS GUIAS</b><br><br>"
            "Remove permanentemente todas as linhas guia do modelo atual.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Excelente para fazer uma limpeza rápida quando você decide mudar o design completamente.</small>"
        )
        self.btn_clear_guides.clicked.connect(self.clear_all_guides)

        self.btn_lock_guides = QPushButton("🔓")
        self.btn_lock_guides.setFixedSize(26, 26)
        self.btn_lock_guides.setStyleSheet(btn_icon_style)
        self.btn_lock_guides.setCheckable(True)
        self._apply_tooltip(self.btn_lock_guides, 
            "<b>BLOQUEAR/DESBLOQUEAR GUIAS</b><br><br>"
            "Impede que as linhas guia sejam movidas ou selecionadas acidentalmente.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Ative o cadeado após posicionar suas linhas para evitar esbarrões enquanto edita os textos e imagens.</small>"
        )
        self.btn_lock_guides.toggled.connect(self.toggle_guides_lock)
        # Efeito de opacidade para o cadeado
        self.op_lock = QGraphicsOpacityEffect(self.btn_lock_guides)
        self.btn_lock_guides.setGraphicsEffect(self.op_lock)
        self.op_lock.setOpacity(1.0 if self.btn_lock_guides.isChecked() else 0.2)

        row_title_guides.addWidget(lbl_guides)
        row_title_guides.addStretch()
        row_title_guides.addWidget(self.btn_toggle_guides)
        row_title_guides.addWidget(self.btn_lock_guides)
        row_title_guides.addWidget(self.btn_clear_guides)
        
        ly_guides.addLayout(row_title_guides)

        # --- Botões de Criação ---
        lbl_add_info = QLabel("Adicionar linhas")
        lbl_add_info.setStyleSheet("font-size: 10px; color: #888888; margin-top: 5px;")
        lbl_add_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ly_guides.addWidget(lbl_add_info)

        row_guides = QHBoxLayout()
        row_guides.setSpacing(10)
        
        btn_guide_v = QPushButton("Vertical")
        btn_guide_v.setMinimumHeight(30)
        self._apply_tooltip(btn_guide_v, "<b>ADICIONAR GUIA VERTICAL</b><br><br>Insere uma linha de alinhamento vertical no centro da prancheta.")
        btn_guide_v.clicked.connect(lambda: self.add_guide(vertical=True))

        btn_guide_h = QPushButton("Horizontal")
        btn_guide_h.setMinimumHeight(30)
        self._apply_tooltip(btn_guide_h, "<b>ADICIONAR GUIA HORIZONTAL</b><br><br>Insere uma linha de alinhamento horizontal no centro da prancheta.")
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
        lbl_elements = QLabel("<b>ELEMENTOS</b>")
        self._apply_tooltip(lbl_elements, 
            "<b>CONSTRUTOR DE LAYOUT</b><br><br>"
            "Conjunto de ferramentas essenciais para estruturar o design do seu modelo.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Todo elemento adicionado surge inicialmente centralizado na prancheta. Arraste-os para compor sua arte.</small>")
        ly_boxes.addWidget(lbl_elements)
        
        self.btn_add_sig = QPushButton("✍️ Assinatura")
        self.btn_add_sig.setMinimumHeight(35)
        self.btn_add_sig.clicked.connect(self._on_click_add_signature)
        self.btn_add_sig.setToolTip(
            "<b>ASSINATURA DIGITAL</b><br><br>"
            "Adiciona uma assinatura para documentos ou cartões destinados ao envio por mídias digitais:<br><br>"
            "• <b>Recomendação:</b> Utilize arquivos .PNG com fundo transparente para garantir que a assinatura flutue naturalmente sobre o design do cartão.<br>"
            "• <b>Tabela Inteligente:</b> Modelos com este elemento ganham uma coluna especial ('✍️ Ass.') na tabela de dados.<br>"
            "• <b>Controle Seletivo:</b> Permite indicar, linha por linha, se o documento final receberá ou não a assinatura carimbada.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Utilize para carimbar mensagens manuscritas digitalizadas (com fundo transparente) em destinatários específicos. Isso permite que o Comandante/Chefe/Diretor inclua notas pessoais e exclusivas em meio a um lote padrão de cartões, sem precisar alterar o modelo original.</small>")
        ly_boxes.addWidget(self.btn_add_sig)

        self.btn_add = QPushButton("📝 Caixa de Texto")
        self.btn_add.setMinimumHeight(35)
        self.btn_add.clicked.connect(self.add_new_box)
        self.btn_add.setToolTip(
            "<b>TEXTO DINÂMICO</b><br><br>"
            "Cria áreas que serão preenchidas automaticamente com os dados da sua tabela (ex: {Nome}):<br><br>"
            "• <b>Delimitação:</b> A largura da caixa trava o alinhamento, mas o conteúdo pode expandir verticalmente caso o texto seja muito longo.<br>"
            "• <b>Formatação:</b> Suporta estilos individuais de fontes, cores e recuos por caixa.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Configure o alinhamento vertical como 'Meio' para que nomes curtos ou longos fiquem sempre bem centralizados na moldura.</small>")
        ly_boxes.addWidget(self.btn_add)

        self.btn_add_img = QPushButton("📸 Imagem")
        self.btn_add_img.setMinimumHeight(35)
        self.btn_add_img.clicked.connect(self._on_click_add_image)
        self.btn_add_img.setToolTip(
            "<b>ELEMENTOS VISUAIS</b><br><br>"
            "Insere ícones, fotos, selos ou mapas para personalização e identidade visual:<br><br>"
            "• <b>Interatividade:</b> É possível ativar links clicáveis para criar cartões interativos no formato PDF.<br>"
            "• <b>Versatilidade:</b> Ideal para incluir botões de ação, logotipos ou QR Codes estáticos.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Transforme logos de redes sociais em links diretos para criar cartões de visita digitais interativos.</small>")
        ly_boxes.addWidget(self.btn_add_img)

        self.btn_add_bg = QPushButton("🖼️ Fundo")
        self.btn_add_bg.setMinimumHeight(35)
        self.btn_add_bg.clicked.connect(self._on_click_load_bg)
        self.btn_add_bg.setToolTip(
            "<b>IMAGEM DE FUNDO</b><br><br>"
            "Define a base gráfica e as dimensões estruturais (alma) do seu documento:<br><br>"
            "• <b>Criação Externa:</b> Recomenda-se criar a base em programas especializados (Photoshop, Corel, Gimp ou Inkscape).<br>"
            "• <b>Auto-ajuste:</b> As dimensões da imagem importada definem automaticamente o tamanho do documento (cartão, diploma, prisma ou etiquetas).<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Exporte seu fundo em 300 DPI para garantir que a impressão saia com nitidez máxima e cores fiéis ao design original.</small>")
        ly_boxes.addWidget(self.btn_add_bg)
        left_layout.addWidget(grp_boxes)
        self._add_separator(left_layout)

        lbl_layers = QLabel("<b>CAMADAS</b>")
        self._apply_tooltip(lbl_layers, 
            "<b>PAINEL DE CAMADAS</b><br><br>"
            "Gerencia a sobreposição e o estado de todos os objetos do modelo:<br><br>"
            "• <b>Hierarquia:</b> Itens no topo da lista cobrem visualmente os que estão abaixo.<br>"
            "• <b>Categorias:</b> Assinaturas sempre sobrepõem Textos, que sobrepõem Imagens.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Você pode arrastar os itens na lista para reordená-los dentro da sua própria categoria.</small>")
        left_layout.addWidget(lbl_layers)

        # Barra de Ferramentas Auxiliar de Camadas (Undo, Redo, Dup, Del)
        self.layer_toolbar = self._setup_layer_toolbar()
        left_layout.addWidget(self.layer_toolbar)

        self.layer_list = QListWidget()
        self.layer_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.layer_list.itemClicked.connect(self._on_layer_list_clicked)
        self.layer_list.itemChanged.connect(self._on_layer_item_changed)
        self.layer_list.itemDoubleClicked.connect(self.rename_layer)
        self.layer_list.model().rowsMoved.connect(self._on_layer_reordered)
        left_layout.addWidget(self.layer_list)
        
        main_layout.addWidget(left_container)

        self.scene = QGraphicsScene(0, 0, 1000, 1000)
        self.view = QGraphicsView(self.scene)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate) # <-- EXTIRPA OS FANTASMAS
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
        self.fallback_bg.setZValue(-200) # Afundado para -200 para ficar atrás do BackgroundItem (-100)
        
        # Inicializa o fundo vazio para garantir a existência da camada desde o início
        self.bg_item = BackgroundItem(None)
        self.scene.addItem(self.bg_item)

        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        center_layout.addWidget(self.view, 1)
        
        main_layout.addWidget(center_container, 1)

        right_container = QWidget()
        right_container.setFixedWidth(400)
        right_layout = QVBoxLayout(right_container)

        # --- Container Superior Misto (Dimensões e Posição) ---
        container_sup = QWidget()
        layout_sup = QHBoxLayout(container_sup)
        layout_sup.setContentsMargins(0, 0, 0, 0)
        layout_sup.setSpacing(10)

        # Coluna 1: Posição do Item (Agora na esquerda)
        col_pos = QWidget()
        ly_pos = QVBoxLayout(col_pos)
        ly_pos.setContentsMargins(0, 0, 0, 0)
        ly_pos.setSpacing(5)
        lbl_pos = QLabel("<b>POSIÇÃO (mm)</b>")
        self._apply_tooltip(lbl_pos, 
            "<b>COORDENADAS DO OBJETO</b><br><br>"
            "Mostra e ajusta a posição exata do elemento selecionado no papel:<br><br>"
            "• <b>Eixo X:</b> Distância horizontal a partir da borda esquerda.<br>"
            "• <b>Eixo Y:</b> Distância vertical a partir do topo.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Utilize estes campos numéricos para fazer alinhamentos com precisão cirúrgica em vez de arrastar com o mouse.</small>")
        ly_pos.addWidget(lbl_pos)
        
        form_pos = QFormLayout()
        form_pos.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.spin_pos_x = MathDoubleSpinBox()
        self.spin_pos_x.setRange(-5000, 20000)
        self.spin_pos_x.setDecimals(1)
        self.spin_pos_x.setKeyboardTracking(False)
        self.spin_pos_x.setEnabled(False)
        
        self.spin_pos_y = MathDoubleSpinBox()
        self.spin_pos_y.setRange(-5000, 20000)
        self.spin_pos_y.setDecimals(1)
        self.spin_pos_y.setKeyboardTracking(False)
        self.spin_pos_y.setEnabled(False)
        
        form_pos.addRow("X:", self.spin_pos_x)
        form_pos.addRow("Y:", self.spin_pos_y)
        ly_pos.addLayout(form_pos)
        layout_sup.addWidget(col_pos, 1)

        # Separador Vertical (VLine)
        v_sep_sup = QFrame()
        v_sep_sup.setFrameShape(QFrame.Shape.VLine)
        v_sep_sup.setFrameShadow(QFrame.Shadow.Sunken)
        v_sep_sup.setStyleSheet("color: #ccc;") 
        layout_sup.addWidget(v_sep_sup)

        # Coluna 2: Dimensões do Documento (Agora na direita)
        col_dim = QWidget()
        ly_dim = QVBoxLayout(col_dim)
        ly_dim.setContentsMargins(0, 0, 0, 0)
        ly_dim.setSpacing(5)
        lbl_dim = QLabel("<b>DOCUMENTO (mm)</b>")
        self._apply_tooltip(lbl_dim, 
            "<b>DIMENSÕES DO DOCUMENTO</b><br><br>"
            "Define o tamanho físico real da arte final impressa ou exportada:<br><br>"
            "• <b>Fidelidade:</b> O sistema gera os cartões mantendo 300 DPI exatos nesta medida.<br>"
            "• <b>Prancheta:</b> Ajusta automaticamente a área branca de trabalho no editor.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Ao carregar uma imagem de fundo (Background), o documento se ajustará sozinho às proporções dela.</small>")
        ly_dim.addWidget(lbl_dim)
        
        form_dim = QFormLayout()
        form_dim.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.spin_phys_w = MathDoubleSpinBox()
        self.spin_phys_w.setRange(10, 2000)
        self.spin_phys_w.setDecimals(1)
        self.spin_phys_w.setKeyboardTracking(False)
        self.spin_phys_w.setValue(100.0) 
        
        self.spin_phys_h = MathDoubleSpinBox()
        self.spin_phys_h.setRange(10, 2000)
        self.spin_phys_h.setDecimals(1)
        self.spin_phys_h.setKeyboardTracking(False)
        self.spin_phys_h.setValue(150.0) 
        
        form_dim.addRow("Larg:", self.spin_phys_w)
        form_dim.addRow("Alt:", self.spin_phys_h)
        ly_dim.addLayout(form_dim)
        layout_sup.addWidget(col_dim, 1)

        right_layout.addWidget(container_sup)

        # Conexões de Sinais
        self.spin_phys_w.valueChanged.connect(self._on_physical_size_changed)
        self.spin_phys_h.valueChanged.connect(self._on_physical_size_changed)
        self.spin_pos_x.valueChanged.connect(self.apply_position_x)
        self.spin_pos_y.valueChanged.connect(self.apply_position_y)
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
        self.caixa_texto_panel.proportionToggled.connect(self.update_proportion_lock)
        self.caixa_texto_panel.linkToggled.connect(self.update_link_state)
        self.caixa_texto_panel.restoreRequested.connect(self.restore_item_state)
        self.caixa_texto_panel.opacityChanged.connect(self.update_opacity)
        self.caixa_texto_panel.snapshotRequested.connect(self.save_snapshot)
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
        self._apply_tooltip(lbl_cols, 
            "<b>ESTRUTURA DA PLANILHA</b><br><br>"
            "Define a sequência visual das colunas na tela principal de geração:<br><br>"
            "• <b>Mapeamento:</b> Lê as variáveis criadas nas caixas de texto e gera a lista.<br>"
            "• <b>Reordenação:</b> Arraste os itens aqui para mudar a ordem de digitação depois.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Coloque as informações mais importantes (como Nome e Cargo) no topo da lista para acelerar o preenchimento.</small>")
        ly_cols_compact.addWidget(lbl_cols)

        self.lst_placeholders = QListWidget()
        self.lst_placeholders.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lst_placeholders.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lst_placeholders.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lst_placeholders.setFixedHeight(150) 
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
        self.editor_texto_panel.snapshotRequested.connect(self.save_snapshot)
        right_layout.addWidget(self.editor_texto_panel)

        self._add_separator(right_layout)

        right_layout.addStretch()
        self.btn_save = QPushButton("Salvar Modelo")
        self.btn_save.setMinimumHeight(50)
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; font-size: 14px;")
        self.btn_save.clicked.connect(self.export_to_json)
        right_layout.addWidget(self.btn_save)

        main_layout.addWidget(right_container)

        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.scene.changed.connect(self.update_position_ui)

        
        # O histórico não deve registrar a inicialização em branco, deixaremos para 
        # registrar o Estado #0 logo após carregar o JSON ou criar novos itens.

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
        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.shortcut_delete.activated.connect(self.delete_selected_items)

        # --- SISTEMA DE UNDO/REDO ---
        self.history = HistoryManager(max_steps=30)
        
        # Conecta o estado da pilha aos novos botões da UI
        self.history.canUndoChanged.connect(self.btn_undo.setEnabled)
        self.history.canRedoChanged.connect(self.btn_redo.setEnabled)
        
        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.undo)

        # Atalho para renomear camada
        self.shortcut_rename = QShortcut(QKeySequence("F2"), self)
        # Só executa se houver um item atual na lista
        self.shortcut_rename.activated.connect(
            lambda: self.rename_layer() if self.layer_list.currentItem() else None
        )
        
        self.shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.shortcut_redo.activated.connect(self.redo)
        self.shortcut_redo_alt = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self.shortcut_redo_alt.activated.connect(self.redo)

        # Ativa/Desativa o botão de renomear conforme a seleção na lista
        self.layer_list.itemSelectionChanged.connect(
            lambda: self.btn_ren_layer.setEnabled(self.layer_list.currentItem() is not None)
        )        

        # --- FORÇA A SINCRONIA INICIAL ---
        # Faz o quadrado branco (1000x1000) se transformar no retângulo exato ditado pelas caixas (100x150mm) a 300 DPI
        self._on_physical_size_changed()

    def showEvent(self, event):
        super().showEvent(event)
        self._zoom_to_fit()

    def eventFilter(self, source, event):
        # Escuta tanto a view principal quanto o viewport das barras de rolagem
        if source in (self.view, self.view.viewport()):
            # --- 1. Zoom com Ctrl + Scroll ou Mouse (Wayland/X11) ---
            if event.type() == QEvent.Type.Wheel and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                delta = event.angleDelta().y()
                if delta == 0:
                    delta = event.pixelDelta().y()
                
                if delta != 0:
                    zoom_factor = 1.15 if delta > 0 else 1 / 1.15
                    self.view.scale(zoom_factor, zoom_factor)
                event.accept() # Mata o evento nativo de rolagem
                return True

            # --- 1.5. Zoom com Gesto de Pinça (Touchpad) ---
            if event.type() == QEvent.Type.NativeGesture and event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                zoom_factor = 1.0 + event.value()
                if zoom_factor > 0:
                    self.view.scale(zoom_factor, zoom_factor)
                event.accept()
                return True

            # --- Eventos de Teclado (Pressionar) ---
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                
                # 2. Ativar Pan (Mãozinha) ao segurar Espaço
                if key == Qt.Key.Key_Space and not event.isAutoRepeat():
                    self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                    return True
                
                if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                    step = 10 if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1
                    dx = -step if key == Qt.Key.Key_Left else (step if key == Qt.Key.Key_Right else 0)
                    dy = -step if key == Qt.Key.Key_Up else (step if key == Qt.Key.Key_Down else 0)
                    sel_items = self.scene.selectedItems()
                    if sel_items:
                        for item in sel_items:
                            if item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
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
    
    def load_from_json(self, file_path):
        path = Path(file_path)
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.setWindowTitle(f"Editor Visual de Modelo - {data['name']}")
        
        # O apply_scene_state faz todo o trabalho duro de desenhar
        self.apply_scene_state(data, is_undo_redo=False)
        self._zoom_to_fit()
        
        # Limpa o histórico e salva o Estado #0
        self.history.clear()
        self.save_snapshot()

    def export_to_json(self):
        data = self.get_current_scene_state()
        model_name = data["name"]
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
    
    def load_background_image(self, path, update_ui=True, props=None):
        original_size = None
        if path:
            reader = QImageReader(path)
            reader.setAutoTransform(True)
            original_size = reader.size()
            
            if not reader.canRead() and QPixmap(path).isNull():
                QMessageBox.warning(self, "Erro de Leitura", "A imagem está corrompida ou em um formato não suportado (ex: CMYK sem plugin).")
                return
                
            if original_size.isEmpty():
                original_size = QPixmap(path).size()
        
        if self.bg_item:
            self.scene.removeItem(self.bg_item)
            
        self.background_path = path
        
        # Instancia o fundo livre em vez de um Pixmap cimentado
        self.bg_item = BackgroundItem(path)
        self.scene.addItem(self.bg_item)
        self.refresh_layer_list()
        
        if props:
            # Se for carregado via JSON, recupera posições e bloqueios
            self.bg_item.setPos(props.get("x", 0), props.get("y", 0))
            if "w" in props and "h" in props:
                self.bg_item.resize_custom(props["w"], props["h"])
            self.bg_item.setVisible(props.get("visible", True))
            self.bg_item.setOpacity(props.get("opacity", 1.0))
            if props.get("locked", False):
                self.bg_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                self.bg_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                self.bg_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        elif not update_ui:
            # Fallback para JSONs antigos: estica para o tamanho da tela para não quebrar layout
            w_px = mm_to_px(self.spin_phys_w.value())
            h_px = mm_to_px(self.spin_phys_h.value())
            self.bg_item.resize_custom(w_px, h_px)

        if update_ui and original_size:
                # Lê o tamanho original da imagem ao importar manualmente e molda a "Prancheta"
                w_mm = px_to_mm(original_size.width())
                h_mm = px_to_mm(original_size.height())
                
                self.spin_phys_w.blockSignals(True)
                self.spin_phys_h.blockSignals(True)
                self.spin_phys_w.setValue(w_mm)
                self.spin_phys_h.setValue(h_mm)
                self.spin_phys_w.blockSignals(False)
                self.spin_phys_h.blockSignals(False)
                
                self._on_physical_size_changed()
                self._zoom_to_fit()
            
                if update_ui:
                    self.save_snapshot()

    def get_all_model_placeholders(self):
        placeholders = set()
        for item in self.scene.items():
            if isinstance(item, DesignerBox):
                placeholders.update(item.get_placeholders())
                if getattr(item.state, 'has_link', False):
                    name = self._generate_layer_name(getattr(item, 'layer_id', 99), item)
                    placeholders.add(f"Link - {name}")
            elif isinstance(item, ImageItem) and not isinstance(item, BackgroundItem):
                if getattr(item, 'has_link', False):
                    name = self._generate_layer_name(getattr(item, 'layer_id', 99), item)
                    placeholders.add(f"Link - {name}")
        return sorted(list(placeholders))
    
    def add_new_box(self):
        box = DesignerBox(350, 450, 300, 60, "{campo}")
        self.scene.addItem(box)
        self.scene.clearSelection()
        box.setSelected(True)
        self.sync_placeholders_list()
        self.refresh_layer_list()
        self.save_snapshot()

    def add_guide(self, vertical):
        rect = self.scene.sceneRect()
        if vertical:
            pos = rect.width() / 2
        else:
            pos = rect.height() / 2
        guide = Guideline(pos, is_vertical=vertical)
        # Respeita o estado de visibilidade e bloqueio ao criar
        is_locked = self.btn_lock_guides.isChecked()
        guide.setVisible(self.btn_toggle_guides.isChecked())
        guide.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not is_locked)
        guide.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not is_locked)
        guide.setOpacity(0.4 if is_locked else 1.0)
        
        self.scene.addItem(guide)
        self.save_snapshot()

    def toggle_guides_visibility(self, checked):
        self.op_eye.setOpacity(1.0 if checked else 0.2)
        for item in self.scene.items():
            if isinstance(item, Guideline):
                item.setVisible(checked)
        self.save_snapshot()

    def toggle_guides_lock(self, locked):
        self.btn_lock_guides.setText("🔒" if locked else "🔓")
        self.op_lock.setOpacity(1.0 if locked else 0.2)
        self.btn_clear_guides.setEnabled(not locked)
        for item in self.scene.items():
            if isinstance(item, Guideline):
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not locked)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not locked)
                # Feedback visual: reduz a opacidade quando bloqueado
                item.setOpacity(0.4 if locked else 1.0)
        self.save_snapshot()

    def clear_all_guides(self):
        # Proteção contra exclusão acidental: ignora se o cadeado estiver fechado
        if self.btn_lock_guides.isChecked():
            return

        removed = False
        for item in self.scene.items():
            if isinstance(item, Guideline):
                self.scene.removeItem(item)
                removed = True
        if removed:
            self.save_snapshot()

    def duplicate_selected(self):
        original = self._get_selected()
        if not original: return

        offset = 20
        new_x = original.x() + offset
        new_y = original.y() + offset
        rect = original.rect()
        
        new_box = DesignerBox(new_x, new_y, rect.width(), rect.height(), "")
        new_box.layer_id = None 
        
        new_box.state = copy.deepcopy(original.state)
        new_box.setRotation(original.rotation())
        new_box.apply_state()
        new_box.update_center()

        self.scene.addItem(new_box)
        self.refresh_layer_list()
        
        self.scene.clearSelection()
        new_box.setSelected(True)
        self.sync_placeholders_list()
        self.save_snapshot()

    def delete_selected_items(self):
        selected = self.scene.selectedItems()
        if not selected: return
        
        for item in selected: 
            self.scene.removeItem(item)
            
        self.on_selection_changed()
        self.sync_placeholders_list()
        self.refresh_layer_list()
        self.save_snapshot()

    def apply_position_x(self, val):
        sel = self.scene.selectedItems()
        if sel:
            item = sel[0]
            item.setPos(mm_to_px(val), item.pos().y())

    def apply_position_y(self, val):
        sel = self.scene.selectedItems()
        if sel:
            item = sel[0]
            item.setPos(item.pos().x(), mm_to_px(val))

    def update_width(self, width_mm):
        item = self._get_selected()
        width_px = mm_to_px(width_mm)
        if item:
            if isinstance(item, DesignerBox):
                r = item.rect()
                item.setRect(0, 0, width_px, r.height())
                item.recalculate_text_position()
                item.update_center() 
            elif isinstance(item, (ImageItem, SignatureItem)):
                h_px = mm_to_px(self.caixa_texto_panel.spin_h.value())
                item.resize_custom(width_px, h_px)

    def update_height(self, height_mm):
        item = self._get_selected()
        height_px = mm_to_px(height_mm)
        if item:
            if isinstance(item, DesignerBox):
                r = item.rect()
                item.setRect(0, 0, r.width(), height_px)
                item.recalculate_text_position()
                item.update_center()
            elif isinstance(item, (ImageItem, SignatureItem)):
                w_px = mm_to_px(self.caixa_texto_panel.spin_w.value())
                item.resize_custom(w_px, height_px)

    def update_rotation(self, angle):
        item = self._get_selected()
        if item:
            item.setRotation(angle)
            if isinstance(item, (ImageItem, SignatureItem)):
                rect = item.pixmap().rect()
                item.setTransformOriginPoint(rect.width() / 2, rect.height() / 2)

    def update_proportion_lock(self, locked):
        item = self._get_selected()
        if item:
            item.keep_proportion = locked

    def update_link_state(self, has_link):
        item = self._get_selected()
        if item:
            if isinstance(item, DesignerBox):
                item.state.has_link = has_link
            elif isinstance(item, ImageItem):
                item.has_link = has_link
            self.sync_placeholders_list()
            self.refresh_layer_list()

    def update_opacity(self, value):
        item = self._get_selected()
        if item:
            item.setOpacity(value)

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

    def restore_item_state(self):
        item = self._get_selected()
        if not item: return
        
        item.setRotation(0)
        
        if isinstance(item, (ImageItem, SignatureItem)):
            if hasattr(item, '_original_pixmap') and not item._original_pixmap.isNull():
                w_px = item._original_pixmap.width()
                h_px = item._original_pixmap.height()
                item.resize_custom(w_px, h_px)
                item.setTransformOriginPoint(w_px / 2, h_px / 2) # Corrige o pivô de giro
            self.caixa_texto_panel.load_from_image(item) # Recarrega a UI com os dados puros
            
        elif isinstance(item, DesignerBox):
            item.update_center()
            self.caixa_texto_panel.load_from_item(item)
        self.save_snapshot()

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

        # Sincroniza a seleção na lista de camadas (UI)
        if sel:
            target_item = sel[0]
            self.layer_list.blockSignals(True)
            for i in range(self.layer_list.count()):
                list_item = self.layer_list.item(i)
                if list_item.data(Qt.ItemDataRole.UserRole) == target_item:
                    self.layer_list.setCurrentItem(list_item)
                    break
            self.layer_list.blockSignals(False)
        else:
            self.layer_list.clearSelection()

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

    def _on_physical_size_changed(self, _=None):
        """Redimensiona APENAS a prancheta (papel branco). A imagem de fundo agora é livre."""
        if not hasattr(self, 'scene'): return
        
        w_px = mm_to_px(self.spin_phys_w.value())
        h_px = mm_to_px(self.spin_phys_h.value())
        
        rect = QRectF(0, 0, w_px, h_px)
        
        self.scene.setSceneRect(rect)
        self.view.setSceneRect(rect)
        
        if self.fallback_bg:
            self.fallback_bg.setRect(rect)
            self.fallback_bg.show() # Garante que o papel branco esteja visível como base

    def _on_click_load_bg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Fundo", "", "Imagens (*.png *.jpg *.jpeg)")
        if path:
            self.load_background_image(path)


    def _on_click_add_signature(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Assinatura", "", "Imagens (*.png)")
        if path:
            sig = SignatureItem(path)
            center = self.view.mapToScene(self.view.viewport().rect().center())
            sig.setPos(center)
            self.scene.addItem(sig)
            self.refresh_layer_list()
            self.save_snapshot()

    def _on_click_add_image(self):
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
            self.save_snapshot()

    def _on_content_updated(self, html):
        self.update_text_html(html)
        self.sync_placeholders_list()
        self.refresh_layer_list()

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
            self.save_snapshot()

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
        imagens = [i for i in items_in_order if isinstance(i, ImageItem) and not isinstance(i, BackgroundItem)]
        fundos = [i for i in items_in_order if isinstance(i, BackgroundItem)]
        
        # Blinda o Z-Value matematicamente, não importa pra onde o usuário tentou arrastar
        for i, item in enumerate(assinaturas): item.setZValue(250 - i)
        for i, item in enumerate(textos): item.setZValue(200 - i)
        for i, item in enumerate(imagens): item.setZValue(100 - i)
        for i, item in enumerate(fundos): item.setZValue(-100 - i)
        
        # Redesenha forçadamente para que o item "pule" de volta para a sua seção correta caso tenha sido arrastado pra fora dela
        self.refresh_layer_list()
        self.save_snapshot()

    def rename_layer(self, list_item=None):
        """Abre a janela de renomeação e preserva a seleção após o refresh."""
        if list_item is None or isinstance(list_item, bool):
            list_item = self.layer_list.currentItem()
            
        if not list_item:
            return

        item = list_item.data(Qt.ItemDataRole.UserRole)
        if not item:
            return

        # 1. Guardar o ID da camada selecionada para recuperar depois
        selected_id = getattr(item, 'layer_id', None)

        current_name = self._generate_layer_name(selected_id, item)
        new_name, ok = QInputDialog.getText(
            self, "Renomear Camada", 
            "Novo nome para a camada:", 
            text=current_name
        )
        
        if ok and new_name.strip():
            item.custom_name = new_name.strip()
            
            # 2. Atualizar a lista (isso limpa a seleção)
            self.refresh_layer_list()
            
            # 3. Recuperar a seleção automaticamente
            if selected_id is not None:
                for i in range(self.layer_list.count()):
                    li = self.layer_list.item(i)
                    obj = li.data(Qt.ItemDataRole.UserRole)
                    if obj and getattr(obj, 'layer_id', None) == selected_id:
                        self.layer_list.setCurrentItem(li)
                        break
            
            self.sync_placeholders_list()
            self.save_snapshot()

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
                self.spin_pos_x.setValue(px_to_mm(item.pos().x()))
                self.spin_pos_y.setEnabled(False)
            else:
                self.spin_pos_y.setValue(px_to_mm(item.pos().y()))
                self.spin_pos_x.setEnabled(False)
        else:
            self.spin_pos_x.setValue(px_to_mm(item.pos().x()))
            self.spin_pos_y.setValue(px_to_mm(item.pos().y()))

        # Sincroniza Largura e Altura no painel
        if isinstance(item, DesignerBox):
            self.caixa_texto_panel.blockSignals(True)
            self.caixa_texto_panel.spin_w.setValue(px_to_mm(item.rect().width()))
            self.caixa_texto_panel.spin_h.setValue(px_to_mm(item.rect().height()))
            self.caixa_texto_panel.blockSignals(False)
        elif isinstance(item, (ImageItem, SignatureItem)):
            self.caixa_texto_panel.blockSignals(True)
            rect = item.pixmap().rect()
            self.caixa_texto_panel.spin_w.setValue(px_to_mm(rect.width()))
            self.caixa_texto_panel.spin_h.setValue(px_to_mm(rect.height()))
            self.caixa_texto_panel.blockSignals(False)

        self.spin_pos_x.blockSignals(False)
        self.spin_pos_y.blockSignals(False)

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

    def refresh_layer_list(self):
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        
        assinaturas = []
        textos = []
        imagens = []
        fundo = None
        
        for item in self.scene.items():
            if isinstance(item, BackgroundItem): fundo = item
            elif isinstance(item, SignatureItem): assinaturas.append(item)
            elif isinstance(item, DesignerBox): textos.append(item)
            elif isinstance(item, ImageItem): imagens.append(item)
            
            if not hasattr(item, 'layer_id') or item.layer_id is None:
                item.layer_id = self._get_next_layer_id()

        assinaturas.sort(key=lambda x: x.zValue(), reverse=True)
        textos.sort(key=lambda x: x.zValue(), reverse=True)
        imagens.sort(key=lambda x: x.zValue(), reverse=True)

        def toggle_item_visibility(item, effect):
            new_vis = not item.isVisible()
            item.setVisible(new_vis)
            # Aplica opacidade 1.0 (visível) ou 0.15 (oculto)
            effect.setOpacity(1.0 if new_vis else 0.15)
            self.save_snapshot()

        def toggle_item_lock(item, effect, label):
            is_locked = not bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            new_locked = not is_locked
            
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not new_locked)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not new_locked)
            
            if new_locked:
                item.setSelected(False) # Força a perda de seleção imediata
                item.setAcceptedMouseButtons(Qt.MouseButton.NoButton) # Fica invisível aos cliques
                if hasattr(item, 'handle_br'):
                    item.handle_br.hide()
            else:
                item.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton) # Restaura a detecção de cliques
                
            # Aplica opacidade 1.0 (trancado) ou 0.15 (destrancado)
            effect.setOpacity(1.0 if new_locked else 0.15)
            label.setStyleSheet("color: #888888; font-style: italic;" if new_locked else "")
            self.save_snapshot()

        def add_header(title):
            header = QListWidgetItem(f"--- {title} ---")
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setBackground(QBrush(QColor("#e0e0e0")))
            header.setForeground(QBrush(QColor("#555555")))
            self.layer_list.addItem(header)

        def add_items(item_list):
            for item in item_list:
                name = self._generate_layer_name(item.layer_id, item)
                list_item = QListWidgetItem()
                list_item.setData(Qt.ItemDataRole.UserRole, item)
                
                # Removemos Qt.ItemFlag.ItemIsUserCheckable para sumir com a checkbox nativa
                flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDragEnabled
                list_item.setFlags(flags)
                
                w = QWidget()
                ly = QHBoxLayout(w)
                ly.setContentsMargins(5, 0, 5, 0)
                ly.setSpacing(2) # Espaçamento curto entre os elementos
                
                # --- Botão Visibilidade (Olho - ESQUERDA) ---
                btn_vis = QPushButton("👁️")
                btn_vis.setFixedSize(24, 24)
                btn_vis.setStyleSheet("border: none; background: transparent; font-size: 14px;")
                btn_vis.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_vis.setToolTip(
                    "<b>VISIBILIDADE DA CAMADA</b><br><br>"
                    "Alterna a exibição do objeto atual no editor e na impressão:<br><br>"
                    "• <b>Oculto:</b> O elemento fica transparente e NÃO sai no arquivo final.<br><br>"
                    "<small style='color: #A0A0A0;'>Dica: Útil para esconder temporariamente elementos muito grandes enquanto você ajusta pequenos detalhes embaixo deles.</small>")
                
                effect_vis = QGraphicsOpacityEffect()
                is_visible = item.isVisible()
                effect_vis.setOpacity(1.0 if is_visible else 0.15)
                btn_vis.setGraphicsEffect(effect_vis)
                
                btn_vis.clicked.connect(lambda checked=False, itm=item, eff=effect_vis: toggle_item_visibility(itm, eff))
                ly.addWidget(btn_vis)
                
                # --- Nome da Camada (CENTRO) ---
                lbl = QLabel(name)
                is_locked = not bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                if is_locked:
                    lbl.setStyleSheet("color: #888888; font-style: italic;")
                ly.addWidget(lbl, 1) # Toma todo o espaço restante
                
                # --- Botão Bloqueio (Cadeado - DIREITA) ---
                btn_lock = QPushButton("🔒")
                btn_lock.setFixedSize(24, 24)
                btn_lock.setStyleSheet("border: none; background: transparent; font-size: 14px;")
                btn_lock.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_lock.setToolTip(
                    "<b>BLOQUEIO DE CAMADA</b><br><br>"
                    "Protege o elemento selecionado contra edições acidentais:<br><br>"
                    "• <b>Travado:</b> O item não pode ser clicado, movido ou apagado na tela.<br><br>"
                    "<small style='color: #A0A0A0;'>Dica: Tranque o Fundo e as Imagens decorativas assim que posicioná-los. Isso facilita muito a seleção dos textos.</small>")
                
                effect_lock = QGraphicsOpacityEffect()
                effect_lock.setOpacity(1.0 if is_locked else 0.15) # Sincroniza com sua personalização
                btn_lock.setGraphicsEffect(effect_lock)
                
                btn_lock.clicked.connect(lambda checked=False, itm=item, eff=effect_lock, l=lbl: toggle_item_lock(itm, eff, l))
                ly.addWidget(btn_lock)
                                
                # --- Finalização ---
                list_item.setSizeHint(w.sizeHint())
                self.layer_list.addItem(list_item)
                self.layer_list.setItemWidget(list_item, w)

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

    def get_current_scene_state(self) -> dict:
        """Captura uma 'foto' de tudo o que está na cena agora e retorna como um dicionário."""
        boxes_data = []
        signatures_data = []
        images_data = []
        guidelines_data = []
        
        for item in self.scene.items():
            if isinstance(item, Guideline):
                guidelines_data.append({
                    "pos": round(float(item.pos().x() if item.is_vertical else item.pos().y()), 2),
                    "vertical": item.is_vertical,
                    "visible": item.isVisible()
                })
            
            elif isinstance(item, DesignerBox):
                pos = item.pos()
                r = item.rect()
                boxes_data.append({
                    "custom_name": getattr(item, "custom_name", ""),
                    "id": item.text_item.toPlainText().replace("{", "").replace("}", "").strip(),
                    "html": item.state.html_content,
                    "visible": item.isVisible(),
                    "opacity": round(float(item.opacity()), 2),
                    "locked": not bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable),
                    "x": round(float(pos.x()), 2),
                    "y": round(float(pos.y()), 2),
                    "w": round(float(r.width()), 2),
                    "h": round(float(r.height()), 2),
                    "rotation": round(float(item.rotation()), 2),
                    "font_family": item.state.font_family,
                    "font_size": item.state.font_size,
                    "font_color": getattr(item.state, 'font_color', '#000000'),
                    "has_link": getattr(item.state, 'has_link', False),
                    "link_key": f"Link - {self._generate_layer_name(getattr(item, 'layer_id', 99), item)}",
                    "align": item.state.align,
                    "vertical_align": item.state.vertical_align,
                    "indent_px": item.state.indent_px,
                    "line_height": item.state.line_height,
                    "layer_id": getattr(item, 'layer_id', None),
                    "z_value": round(float(item.zValue()), 2)
                })
            
            elif isinstance(item, SignatureItem):
                pos = item.pos()
                pix = item.pixmap()
                signatures_data.append({
                    "custom_name": getattr(item, "custom_name", ""),
                    "path": getattr(item, "_original_path", ""), 
                    "visible": item.isVisible(),
                    "opacity": round(float(item.opacity()), 2),
                    "locked": not bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable),
                    "x": round(float(pos.x()), 2),
                    "y": round(float(pos.y()), 2),
                    "width": round(float(pix.width()), 2),
                    "height": round(float(pix.height()), 2),
                    "longest_side": round(float(max(pix.width(), pix.height())), 2),
                    "layer_id": getattr(item, 'layer_id', None),
                    "z_value": round(float(item.zValue()), 2)
                })

            elif isinstance(item, ImageItem) and not isinstance(item, BackgroundItem):
                pos = item.pos()
                pix = item.pixmap()
                images_data.append({
                    "custom_name": getattr(item, "custom_name", ""),
                    "path": getattr(item, "_original_path", ""), 
                    "visible": item.isVisible(),
                    "opacity": round(float(item.opacity()), 2),
                    "locked": not bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable),
                    "x": round(float(pos.x()), 2),
                    "y": round(float(pos.y()), 2),
                    "width": round(float(pix.width()), 2),
                    "height": round(float(pix.height()), 2),
                    "longest_side": round(float(max(pix.width(), pix.height())), 2),
                    "rotation": round(float(item.rotation()), 2),
                    "has_link": getattr(item, "has_link", False),
                    "link_key": f"Link - {self._generate_layer_name(getattr(item, 'layer_id', 99), item)}",
                    "layer_id": getattr(item, 'layer_id', None),
                    "z_value": round(float(item.zValue()), 2)
                })

        ordered_placeholders = [self.lst_placeholders.item(i).text() for i in range(self.lst_placeholders.count())]

        data = {
            "name": self.windowTitle().replace("Editor Visual de Modelo - ", "").replace(" (Gerador de Cartões em Lote - GCL)", ""),
            "canvas_size": {"w": int(self.scene.width()), "h": int(self.scene.height())},
            "target_w_mm": self.spin_phys_w.value(),
            "target_h_mm": self.spin_phys_h.value(),
            "background_path": self.background_path,
            "placeholders": ordered_placeholders,
            "signatures": signatures_data,
            "images": images_data,
            "boxes": boxes_data,
            "guidelines": guidelines_data,
            "guidelines_locked": self.btn_lock_guides.isChecked()
        }
        
        if self.bg_item and isinstance(self.bg_item, BackgroundItem):
            data["bg_props"] = {
                "x": round(float(self.bg_item.pos().x()), 2),
                "y": round(float(self.bg_item.pos().y()), 2),
                "w": round(float(self.bg_item.pixmap().width()), 2),
                "h": round(float(self.bg_item.pixmap().height()), 2),
                "visible": self.bg_item.isVisible(),
                "opacity": round(float(self.bg_item.opacity()), 2),
                "locked": not bool(self.bg_item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable),
                "layer_id": getattr(self.bg_item, 'layer_id', None),
                "z_value": round(float(self.bg_item.zValue()), 2)
            }
            
        return data

    def apply_scene_state(self, data: dict, is_undo_redo: bool = False):
        """Limpa a cena e recria tudo com base no dicionário fornecido."""
        # Salva qual layer estava selecionada antes de limpar
        selected_layer_id = None
        sel = self.scene.selectedItems()
        if sel and hasattr(sel[0], 'layer_id'):
            selected_layer_id = sel[0].layer_id

        self.scene.clear()
        self.bg_item = None
        
        canvas_w = data.get("canvas_size", {}).get("w", 1000)
        canvas_h = data.get("canvas_size", {}).get("h", 1000)
        self.scene.setSceneRect(0, 0, canvas_w, canvas_h)

        # Se não for uma ação de undo/redo (ex: abrindo modelo novo), ajusta as pranchetas
        if not is_undo_redo:
            self.spin_phys_w.blockSignals(True)
            self.spin_phys_h.blockSignals(True)
            self.spin_phys_w.setValue(data.get("target_w_mm", 100.0))
            self.spin_phys_h.setValue(data.get("target_h_mm", 150.0))
            self.spin_phys_w.blockSignals(False)
            self.spin_phys_h.blockSignals(False)
        
        self.fallback_bg = self.scene.addRect(0, 0, canvas_w, canvas_h, QPen(Qt.PenStyle.NoPen), QBrush(Qt.GlobalColor.white))
        self.fallback_bg.setZValue(-200)
        
        if not is_undo_redo:
            self._on_physical_size_changed()

        # Fundo
        bg_path_raw = data.get("background_path")
        if bg_path_raw:
            bg_path = Path(bg_path_raw)
            # Tenta resolver o caminho se não for absoluto (procura no próprio modelo)
            if not bg_path.is_absolute():
                slug = slugify_model_name(data.get("name", ""))
                bg_path = get_models_dir() / slug / bg_path_raw
            
            if bg_path.exists():
                self.load_background_image(str(bg_path), update_ui=not is_undo_redo, props=data.get("bg_props"))
                if self.bg_item and "bg_props" in data:
                    self.bg_item.setZValue(data["bg_props"].get("z_value", -100))
            else:
                self.load_background_image(None, update_ui=not is_undo_redo, props=data.get("bg_props"))
        else:
            self.load_background_image(None, update_ui=not is_undo_redo, props=data.get("bg_props"))

        if self.bg_item and "bg_props" in data:
            self.bg_item.layer_id = data["bg_props"].get("layer_id")
            self.bg_item.setZValue(data["bg_props"].get("z_value", -100))

        # Assinaturas
        for sig_data in data.get("signatures", []):
            raw_path = sig_data["path"]
            sig_path = Path(raw_path)
            if not sig_path.is_absolute():
                slug = slugify_model_name(data.get("name", ""))
                sig_path = get_models_dir() / slug / raw_path

            if sig_path.exists():
                sig = SignatureItem(str(sig_path))
                sig.custom_name = sig_data.get("custom_name", "")
                sig.layer_id = sig_data.get("layer_id")
                sig.setPos(sig_data["x"], sig_data["y"])
                sig.resize_by_longest_side(sig_data["longest_side"])
                self.scene.addItem(sig)
                sig.setZValue(sig_data.get("z_value", 201))
                sig.setVisible(sig_data.get("visible", True))
                sig.setOpacity(sig_data.get("opacity", 1.0))
                if sig_data.get("locked", False):
                    sig.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                    sig.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                    sig.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        # Imagens
        for img_data in data.get("images", []):
            raw_path = img_data["path"]
            img_path = Path(raw_path)
            if not img_path.is_absolute():
                slug = slugify_model_name(data.get("name", ""))
                img_path = get_models_dir() / slug / raw_path

            if img_path.exists():
                img = ImageItem(str(img_path))
                img.custom_name = img_data.get("custom_name", "")
                img.layer_id = img_data.get("layer_id")
                img.setPos(img_data["x"], img_data["y"])
                
                if "width" in img_data and "height" in img_data:
                    img.resize_custom(img_data["width"], img_data["height"])
                else:
                    img.resize_by_longest_side(img_data.get("longest_side", 100))
                    
                img.setRotation(img_data.get("rotation", 0))
                self.scene.addItem(img)
                img.setZValue(img_data.get("z_value", 1))
                img.has_link = img_data.get("has_link", False)
                img.setVisible(img_data.get("visible", True))
                img.setOpacity(img_data.get("opacity", 1.0))
                if img_data.get("locked", False):
                    img.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                    img.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                    img.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        # Caixas de Texto
        for b in data.get("boxes", []):
            box = DesignerBox(
                x=b.get("x", 0), 
                y=b.get("y", 0), 
                w=b.get("w", 300), 
                h=b.get("h", 60), 
                text=b.get("id", "Placeholder") 
            )
            box.custom_name = b.get("custom_name", "")
            box.layer_id = b.get("layer_id")
            
            if "html" in b:
                box.state.html_content = b["html"]
                
            box.state.font_family = b.get("font_family", "Arial")
            box.state.font_size = b.get("font_size", 16)
            box.state.font_color = b.get("font_color", "#000000")
            box.state.vertical_align = b.get("vertical_align", "top")
            box.state.align = b.get("align", "left")
            box.state.indent_px = b.get("indent_px", 0)
            box.state.line_height = b.get("line_height", 1.15)
            box.state.has_link = b.get("has_link", False)

            box.setRotation(b.get("rotation", 0))
            box.apply_state()
            box.update_center() 

            self.scene.addItem(box)
            box.setZValue(b.get("z_value", 101))
            box.setVisible(b.get("visible", True))
            box.setOpacity(b.get("opacity", 1.0))
        # Linhas Guia
        guides_data = data.get("guidelines", [])
        for g in guides_data:
            guide = Guideline(g["pos"], is_vertical=g.get("vertical", True))
            guide.setVisible(g.get("visible", True))
            self.scene.addItem(guide)
            
        if guides_data:
            # Sincroniza o botão visual com o estado da primeira guia carregada
            is_visible = guides_data[0].get("visible", True)
            self.btn_toggle_guides.blockSignals(True)
            self.btn_toggle_guides.setChecked(is_visible)
            self.op_eye.setOpacity(1.0 if is_visible else 0.2)
            self.btn_toggle_guides.blockSignals(False)

        # Restaura o estado do cadeado das guias
        is_locked = data.get("guidelines_locked", False)
        self.btn_lock_guides.blockSignals(True)
        self.btn_lock_guides.setChecked(is_locked)
        self.btn_lock_guides.setText("🔒" if is_locked else "🔓")
        self.op_lock.setOpacity(1.0 if is_locked else 0.2)
        self.btn_lock_guides.blockSignals(False)
        
        # Reaplica o bloqueio nos itens recém-criados
        for item in self.scene.items():
            if isinstance(item, Guideline):
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not is_locked)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not is_locked)
                item.setOpacity(0.4 if is_locked else 1.0)

        # Atualiza Placeholders e Lista de Camadas
        saved_placeholders = data.get("placeholders", [])
        self.lst_placeholders.clear()
        for p in saved_placeholders:
            self.lst_placeholders.addItem(p)
        self.sync_placeholders_list()
        self.refresh_layer_list()

        # Restaura a seleção do item que estava ativo
        if selected_layer_id is not None:
            for item in self.scene.items():
                if getattr(item, 'layer_id', None) == selected_layer_id:
                    item.setSelected(True)
                    break

    def save_snapshot(self):
        """Dispara um salvamento na memória (chamado ao soltar o mouse ou terminar uma edição)."""
        state = self.get_current_scene_state()
        self.history.push(state)

    def undo(self):
        state = self.history.undo()
        if state:
            self.apply_scene_state(state, is_undo_redo=True)

    def redo(self):
        state = self.history.redo()
        if state:
            self.apply_scene_state(state, is_undo_redo=True)

    def _setup_layer_toolbar(self) -> QWidget:
        """Cria a barra de ferramentas compacta acima da lista de camadas."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 2, 0, 5)
        layout.setSpacing(4)

        # Estilo comum para os botões da toolbar
        btn_style = """
            QPushButton { 
                background-color: #333333; 
                border: 1px solid #555555; 
                border-radius: 4px; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #444444; border-color: #777777; }
            QPushButton:pressed { background-color: #222222; }
            QPushButton:disabled { background-color: #222222; color: #555555; border-color: #333333; }
        """

        self.btn_undo = QPushButton("↩️")
        self._apply_tooltip(self.btn_undo, 
            "<b>DESFAZER</b><br>"
            "<small style='color: #A0A0A0;'>Atalho: Ctrl + Z</small>"
            "<br><br>"
            "Reverte a última alteração realizada no seu modelo.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: O sistema armazena as últimas 30 ações, permitindo que você explore ideias sem medo de errar.</small>")
        self.btn_undo.setFixedSize(32, 30)
        self.btn_undo.setStyleSheet(btn_style)
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo)

        self.btn_redo = QPushButton("↪️")
        self._apply_tooltip(self.btn_redo, 
            "<b>REFAZER</b><br>"
            "<small style='color: #A0A0A0;'>Atalho: Ctrl + Y</small>"
            "<br><br>"
            "Reaplica a última ação que foi desfeita anteriormente.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Útil para comparar rapidamente o 'antes e depois' de um ajuste fino no layout.</small>")
        self.btn_redo.setFixedSize(32, 30)
        self.btn_redo.setStyleSheet(btn_style)
        self.btn_redo.setEnabled(False)
        self.btn_redo.clicked.connect(self.redo)

        self.btn_ren_layer = QPushButton("✏️")
        self._apply_tooltip(self.btn_ren_layer, 
            "<b>RENOMEAR CAMADA</b><br>"
            "<small style='color: #A0A0A0;'>Atalho: F2</small>"
            "<br><br>"
            "Altera o nome de identificação do objeto selecionado na lista de camadas.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Use nomes descritivos (ex: 'Logo Fundo') para organizar melhor projetos que possuem muitos elementos sobrepostos.</small>")
        self.btn_ren_layer.setFixedSize(32, 30)
        self.btn_ren_layer.setStyleSheet(btn_style)
        self.btn_ren_layer.setEnabled(False) # <--- Começa desativado
        self.btn_ren_layer.clicked.connect(lambda: self.rename_layer())

        self.btn_dup_layer = QPushButton("📑")
        self._apply_tooltip(self.btn_dup_layer, 
            "<b>DUPLICAR CAMADA</b><br>"
            "<small style='color: #A0A0A0;'>Atalho: Ctrl + J</small>"
            "<br><br>"
            "Cria uma cópia exata do elemento selecionado, preservando todas as cores, fontes e tamanhos.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: A cópia é criada com um pequeno deslocamento. Ótimo para criar padrões repetitivos ou variações de uma mesma base.</small>")
        self.btn_dup_layer.setFixedSize(32, 30)
        self.btn_dup_layer.setStyleSheet(btn_style)
        self.btn_dup_layer.clicked.connect(self.duplicate_selected)

        self.btn_del_layer = QPushButton("🗑️")
        self._apply_tooltip(self.btn_del_layer, 
            "<b>EXCLUIR CAMADA</b><br>"
            "<small style='color: #A0A0A0;'>Atalho: Delete</small>"
            "<br><br>"
            "Remove permanentemente o objeto selecionado do seu modelo.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Se apagar algo por engano, utilize o botão DESFAZER ou Ctrl+Z imediatamente para recuperar o item.</small>")
        self.btn_del_layer.setFixedSize(32, 30)
        self.btn_del_layer.setStyleSheet(btn_style)
        self.btn_del_layer.clicked.connect(self.delete_selected_items)

        layout.addWidget(self.btn_undo)
        layout.addWidget(self.btn_redo)
        layout.addStretch() # Empurra os próximos botões para a direita
        layout.addWidget(self.btn_ren_layer) # <- NOVO BOTÃO AQUI
        layout.addWidget(self.btn_dup_layer)
        layout.addWidget(self.btn_del_layer)

        return container

    def _get_selected(self):
        sel = self.scene.selectedItems()
        valid_items = [i for i in sel if isinstance(i, (DesignerBox, ImageItem, SignatureItem))]
        return valid_items[0] if valid_items else None

    def _zoom_to_fit(self):
        if not self.scene.sceneRect().isEmpty():
            margin = 50
            view_rect = self.scene.sceneRect().adjusted(-margin, -margin, margin, margin)
            self.view.fitInView(view_rect, Qt.AspectRatioMode.KeepAspectRatio)

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
    
    def _get_next_layer_id(self):
        used = set()
        for item in self.scene.items():
            if hasattr(item, 'layer_id') and item.layer_id is not None:
                used.add(item.layer_id)
        for i in range(100):
            if i not in used: return i
        return 99

    def _generate_layer_name(self, layer_id, item):
        if hasattr(item, 'custom_name') and item.custom_name:
            return item.custom_name
            
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
        if isinstance(item, BackgroundItem):
            return f"{prefix}_Fundo"
        return f"{prefix}_Objeto"
    
    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

    
    
    

    

    

    

    


    

    
    
    

    

    

    

    
    

    
    
    

    

    
    
    

    

    

    

    