from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
                               QFormLayout, QTextEdit, QFontComboBox, QPushButton, 
                               QComboBox, QDoubleSpinBox, QColorDialog, QCheckBox)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QFont, QTextCursor, QTextBlockFormat, QTextCharFormat
import re

from .canvas_items import DesignerBox, SignatureItem, ImageItem, px_to_mm
from core.custom_widgets import MathDoubleSpinBox


class CleanTextEdit(QTextEdit):
    """Campo de texto customizado que intercepta o Ctrl+V e purifica o HTML."""
    editingFinished = Signal()
    
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.editingFinished.emit()

    def insertFromMimeData(self, source: QMimeData):
        if source.hasHtml():
            raw = source.html()
            # Exterminador no momento exato da colagem
            clean = re.sub(r"font-family\s*:[^;\"]+;?", "", raw)
            clean = re.sub(r"font-size\s*:[^;\"]+;?", "", clean)
            clean = re.sub(r"color\s*:[^;\"]+;?", "", clean)
            clean = re.sub(r"background-color\s*:[^;\"]+;?", "", clean)
            clean = re.sub(r"text-decoration\s*:[^;\"]+;?", "", clean)
            clean = re.sub(r"line-height\s*:[^;\"]+;?", "", clean)
            clean = re.sub(r"(?i)<a\b[^>]*>", "", clean)
            clean = re.sub(r"(?i)</a>", "", clean)
            clean = re.sub(r"(?i)<h[1-6]([^>]*)>", r"<p\1>", clean)
            clean = re.sub(r"(?i)</h[1-6]>", "</p>", clean)
            
            new_mime = QMimeData()
            new_mime.setHtml(clean)
            new_mime.setText(source.text())
            super().insertFromMimeData(new_mime)
        else:
            super().insertFromMimeData(source)

class CaixaDeTextoPanel(QWidget):
    widthChanged = Signal(float)
    heightChanged = Signal(float)
    rotationChanged = Signal(float)
    proportionToggled = Signal(bool) # Novo sinal para a Checkbox
    linkToggled = Signal(bool)
    restoreRequested = Signal()
    opacityChanged = Signal(float)
    snapshotRequested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_title = QLabel("<b>PROPRIEDADES DO OBJETO</b>")
        self.lbl_title.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        tooltip_propriedades = (
            "<b>PROPRIEDADES DO OBJETO</b><br><br>"
            "Gestão técnica de dimensões, orientação e comportamento do elemento selecionado.<br><br>"
            "• <b>Largura e Altura:</b> Define as dimensões físicas horizontais e verticais em milímetros (mm).<br>"
            "• <b>Manter proporção:</b> Trava a relação entre os eixos para evitar distorções no redimensionamento.<br>"
            "• <b>Rotação:</b> Gira o objeto selecionado em graus (°) ao redor do seu ponto central.<br>"
            "• <b>Opacidade:</b> Controla o nível de transparência do elemento (0% a 100%).<br>"
            "• <b>Restaurar original:</b> Reseta a escala e rotação para os valores nativos do arquivo.<br>"
            "• <b>Habilitar link:</b> Cria uma área de interação para redirecionamento em arquivos PDF.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Utilize a função 'Restaurar original' para recuperar instantaneamente a proporção e nitidez nativa de imagens que foram deformadas.</small>"
        )
        self.lbl_title.setToolTip(tooltip_propriedades)
        layout.addWidget(self.lbl_title)
        self._aspect_ratio = 1.0
        self._group_mode = False
        
        form = QFormLayout()
        form.setSpacing(4)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.spin_w = MathDoubleSpinBox()
        self.spin_w.setRange(1.0, 5000.0)
        self.spin_w.setDecimals(2)
        self.spin_w.setKeyboardTracking(False)
        self.spin_w.valueChanged.connect(self.widthChanged.emit)
        
        lbl_w = QLabel("Larg (mm):")
        lbl_w.setToolTip(
            "<b>LARGURA</b><br><br>"
            "Define a dimensão física horizontal exata do objeto.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Valores inseridos aqui refletem o tamanho real (em milímetros) na impressão final.</small>"
        )
        form.addRow(lbl_w, self.spin_w)

        self.spin_h = MathDoubleSpinBox()
        self.spin_h.setRange(1.0, 5000.0)
        self.spin_h.setDecimals(2)
        self.spin_h.setKeyboardTracking(False)
        self.spin_h.valueChanged.connect(self.heightChanged.emit)
        
        lbl_h = QLabel("Alt (mm):")
        lbl_h.setToolTip(
            "<b>ALTURA</b><br><br>"
            "Define a dimensão física vertical exata do objeto.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Se a opção 'Manter proporção' estiver ativa, a largura será ajustada automaticamente.</small>"
        )
        form.addRow(lbl_h, self.spin_h)

        self.spin_rot = QSpinBox()
        self.chk_proporcao = QCheckBox("Manter proporção")
        self.chk_proporcao.setToolTip("Mantém a relação entre largura e altura ao redimensionar o objeto manualmente.")
        self.chk_proporcao.setChecked(True)
        self.chk_proporcao.toggled.connect(self.proportionToggled.emit)
        form.addRow("", self.chk_proporcao)
        self.chk_proporcao.setToolTip(
            "<b>MANTER PROPORÇÃO</b><br><br>"
            "Preserva a relação entre largura e altura durante o redimensionamento:<br>"
            "• <b>Vínculo:</b> Ao alterar um valor, o outro é ajustado automaticamente.<br>"
            "• <b>Integridade:</b> Evita que imagens e textos fiquem esticados ou deformados.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Desative apenas se precisar forçar uma dimensão específica ignorando o aspeto original.</small>")

        # Intercepta os sinais para calcular a proporção antes de emitir para a cena
        self.spin_w.valueChanged.disconnect(self.widthChanged.emit)
        self.spin_h.valueChanged.disconnect(self.heightChanged.emit)
        self.spin_w.valueChanged.connect(self._on_w_changed)
        self.spin_h.valueChanged.connect(self._on_h_changed)
        self.spin_rot = MathDoubleSpinBox()
        self.spin_rot.setRange(-360, 360)
        self.spin_rot.setDecimals(1)
        self.spin_rot.setWrapping(True) 
        self.spin_rot.valueChanged.connect(self.rotationChanged.emit)
        
        lbl_rot = QLabel("Rot (°):")
        lbl_rot.setToolTip(
            "<b>ROTAÇÃO</b><br><br>"
            "Gira o objeto selecionado em graus (°) ao redor do seu ponto central.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Use valores positivos para girar no sentido horário ou negativos para o sentido anti-horário.</small>"
        )
        form.addRow(lbl_rot, self.spin_rot)

        self.spin_opacity = MathDoubleSpinBox()
        self.spin_opacity.setRange(0.0, 100.0)
        self.spin_opacity.setDecimals(0)
        self.spin_opacity.setValue(100.0)
        self.spin_opacity.valueChanged.connect(lambda v: self.opacityChanged.emit(v / 100.0))
        
        lbl_opac = QLabel("Opac (%):")
        lbl_opac.setToolTip(
            "<b>OPACIDADE</b><br><br>"
            "Controla o nível de transparência do elemento (0% a 100%).<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Valores baixos são excelentes para criar marcas d'água sutis que não interferem na leitura de outros dados.</small>"
        )
        form.addRow(lbl_opac, self.spin_opacity)

        self.btn_restore = QPushButton("🔄 Restaurar Original")
        self.btn_restore.setToolTip(
            "<b>RESTAURAR ORIGINAL</b><br><br>"
            "Reverte o objeto ao seu estado inicial de importação:<br><br>"
            "• <b>Reset:</b> Redefine o tamanho nativo e remove qualquer rotação aplicada.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: A forma mais rápida de corrigir uma imagem que foi redimensionada incorretamente ou perdeu qualidade.</small>")
        self.btn_restore.clicked.connect(self.restoreRequested.emit)
        form.addRow("", self.btn_restore)

        self.chk_link = QCheckBox("Habilitar Link (PDF)")
        self.chk_link.setToolTip(
            "<b>HABILITAR LINK (URL)</b><br><br>"
            "Cria uma área de interação (clicável) no PDF exportado:<br><br>"
            "• <b>Cartões interativos:</b> O PDF gerado terá um link clicável para redirecionar ao endereço configurado na tabela.<br>"
            "• <b>Somente em PDF:</b> Esta funcionalidade só está disponível no formato PDF.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Use em logótipos ou rodapés para levar o utilizador diretamente ao seu site ou redes sociais.</small>")
        self.chk_link.toggled.connect(self.linkToggled.emit)
        form.addRow("", self.chk_link)

        self.spin_w.editingFinished.connect(self.snapshotRequested.emit)
        self.spin_h.editingFinished.connect(self.snapshotRequested.emit)
        self.spin_rot.editingFinished.connect(self.snapshotRequested.emit)
        self.spin_opacity.editingFinished.connect(self.snapshotRequested.emit)
        self.chk_proporcao.clicked.connect(self.snapshotRequested.emit)
        self.chk_link.clicked.connect(self.snapshotRequested.emit)

        layout.addLayout(form)
        layout.addStretch()

    def set_group_mode(self, enabled: bool):
        self._group_mode = enabled
        title = "PROPRIEDADES DO GRUPO" if enabled else "PROPRIEDADES DO OBJETO"
        self.lbl_title.setText(f"<b>{title}</b>")

        size_controls_enabled = not enabled
        self.spin_w.setEnabled(size_controls_enabled)
        self.spin_h.setEnabled(size_controls_enabled)
        self.chk_proporcao.setEnabled(size_controls_enabled)
        self.btn_restore.setEnabled(size_controls_enabled)

    def load_from_item(self, box: DesignerBox):
        self.blockSignals(True) 
        rect = box.rect()
        self.spin_w.setValue(px_to_mm(rect.width()))
        self.spin_h.setValue(px_to_mm(rect.height()))
        self.spin_rot.setValue(int(box.rotation()))
        if rect.height() > 0: self._aspect_ratio = rect.width() / rect.height()
        self.spin_opacity.setValue(box.opacity() * 100.0)
        
        self.chk_proporcao.blockSignals(True)
        self.chk_proporcao.setChecked(getattr(box, 'keep_proportion', True))
        self.chk_proporcao.blockSignals(False)
        self.chk_link.blockSignals(True)
        self.chk_link.setChecked(getattr(box.state, 'has_link', False))
        self.chk_link.blockSignals(False)
        self.blockSignals(False)

    def load_from_image(self, img):
        self.blockSignals(True)
        rect = img.pixmap().rect()
        self.spin_w.setValue(px_to_mm(rect.width()))
        self.spin_h.setValue(px_to_mm(rect.height()))
        self.spin_rot.setValue(int(img.rotation()))
        if rect.height() > 0: self._aspect_ratio = rect.width() / rect.height()
        self.spin_opacity.setValue(img.opacity() * 100.0)
        
        self.chk_proporcao.blockSignals(True)
        self.chk_proporcao.setChecked(getattr(img, 'keep_proportion', True))
        self.chk_proporcao.blockSignals(False)
        self.chk_link.blockSignals(True)
        self.chk_link.setChecked(getattr(img, 'has_link', False))
        self.chk_link.blockSignals(False)
        self.blockSignals(False)

    def _on_w_changed(self, val):
        if self.chk_proporcao.isChecked() and self._aspect_ratio > 0:
            new_h = val / self._aspect_ratio
            self.spin_h.blockSignals(True)
            self.spin_h.setValue(new_h)
            self.spin_h.blockSignals(False)
            self.widthChanged.emit(val)
            self.heightChanged.emit(new_h)
        else:
            self.widthChanged.emit(val)

    def _on_h_changed(self, val):
        if self.chk_proporcao.isChecked() and self._aspect_ratio > 0:
            new_w = val * self._aspect_ratio
            self.spin_w.blockSignals(True)
            self.spin_w.setValue(new_w)
            self.spin_w.blockSignals(False)
            self.heightChanged.emit(val)
            self.widthChanged.emit(new_w)
        else:
            self.heightChanged.emit(val)

    
class EditorDeTextoPanel(QWidget):
    htmlChanged = Signal(str)
    fontFamilyChanged = Signal(QFont)
    fontSizeChanged = Signal(int)
    fontColorChanged = Signal(str)
    boldChanged = Signal(bool) 
    alignChanged = Signal(str)
    verticalAlignChanged = Signal(str)
    indentChanged = Signal(float)
    lineHeightChanged = Signal(float)
    snapshotRequested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl = QLabel("EDITOR DE TEXTO")
        lbl.setStyleSheet("font-weight: bold; font-size: 12px; border-bottom: 1px solid #ccc;")
        lbl.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        
        tooltip_editor = (
            "<b>EDITOR DE TEXTO</b><br><br>"
            "Ferramentas de formatação tipográfica e espaçamento do bloco de texto selecionado.<br><br>"
            "• <b>Texto:</b> Defina a redação e crie as chaves que o sistema substituirá automaticamente pelas informações da sua tabela.<br>"
            "• <b>Fonte e Tamanho:</b> Define a família tipográfica e a escala da fonte.<br>"
            "• <b>Estilos:</b> Aplica negrito (Ctrl+B), itálico (Ctrl+I) ou sublinhado (Ctrl+U).<br>"
            "• <b>Cor:</b> Define a cor do texto para garantir bom contraste com a imagem de fundo.<br>"
            "• <b>Alinhamento horizontal:</b> Posiciona o texto nas laterais (Esq/Dir), Centralizado ou Justificado.<br>"
            "• <b>Alinhamento vertical:</b> Fixa o conteúdo no Topo, no Meio ou na Base da moldura.<br>"
            "• <b>Recuo:</b> Define o recuo horizontal da primeira linha para organizar visualmente o início dos parágrafos.<br>"
            "• <b>Entrelinha:</b> Controla a distância vertical entre as linhas, melhorando a legibilidade ou compactando o bloco.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Para caixas que receberão nomes curtos ou longos, ajuste o alinhamento vertical para 'Meio' para mantê-los sempre perfeitamente centralizados na altura.</small>"
        )
        lbl.setToolTip(tooltip_editor)
        layout.addWidget(lbl)
        
        lbl_texto = QLabel("Texto:")
        lbl_texto.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        tooltip_texto = (
            "<b>CONTEÚDO E VARIÁVEIS (PLACEHOLDERS)</b><br><br>"
            "Área de digitação para textos fixos e criação do motor dinâmico do seu modelo.<br><br>"
            "• <b>Como criar:</b> Envolva qualquer palavra com chaves (ex: <b>{Nome}</b>) para que o sistema crie automaticamente uma coluna na sua tabela de preenchimento.<br>"
            "• <b>Caracteres Proibidos:</b> O sistema reconhece <b>apenas letras, números e subtraços (_)</b>. O uso de espaços, acentos ou símbolos quebra a variável, transformando-a em texto estático.<br>"
            "• <b>Composição:</b> Você pode misturar texto estático e variáveis na mesma caixa (ex: <i>Certificamos que {Aluno} concluiu...</i>).<br>"
            "• <b>Ocultação Automática:</b> Se uma variável estiver vazia na tabela, <b>toda a caixa de texto ficará invisível</b> naquele cartão, evitando lixo visual na impressão final.<br><br>"
            "<small style='color: #A0A0A0;'>Dica Smart: Agrupe rótulos e variáveis na mesma caixa (ex: \"WhatsApp: {Telefone}\"). Assim, se a pessoa não tiver telefone cadastrado, a palavra \"WhatsApp:\" some junto com a variável, mantendo o layout impecável.</small>"
        )
        lbl_texto.setToolTip(tooltip_texto)
        layout.addWidget(lbl_texto)
        
        self.txt_content = CleanTextEdit()
        self.txt_content.setMinimumHeight(160)
        self.txt_content.setStyleSheet("background-color: #FFFFFF; color: #000000; border: 1px solid #aaa; font-family: sans-serif; font-size: 11pt;")
        self.txt_content.textChanged.connect(self._emit_clean_html)
        
        # INSERE A CAIXA NO LAYOUT PARA ELA APARECER
        layout.addWidget(self.txt_content)
        
        row_font = QHBoxLayout()
        
        self.cbo_font = QFontComboBox()
        self.cbo_font.setToolTip(
            "<b>FAMÍLIA TIPOGRÁFICA</b><br><br>"
            "Define a fonte (tipo de letra) do texto ou da seleção atual.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Dê preferência a fontes limpas (como Arial, Roboto ou Montserrat) para garantir máxima legibilidade em impressões menores.</small>"
        )
        self.cbo_font.currentFontChanged.connect(self.set_font_family)
        
        self.spin_size = QSpinBox()
        self.spin_size.setRange(6, 300)
        self.spin_size.setToolTip(
            "<b>TAMANHO DA FONTE</b><br><br>"
            "Ajusta a escala do texto em pontos tipográficos (pt).<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Nomes e títulos principais costumam ter grande destaque, enquanto cargos e prefixos usam tamanhos reduzidos.</small>"
        )
        self.spin_size.valueChanged.connect(self.set_font_size)
        
        row_font.addWidget(self.cbo_font, 2)
        row_font.addWidget(self.spin_size, 1)
        layout.addLayout(row_font)

        row_style = QHBoxLayout()
        
        self.btn_bold = QPushButton("B")
        self.btn_bold.setFixedWidth(30)
        self.btn_bold.setStyleSheet("font-weight: bold")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setToolTip(
            "<b>NEGRITO</b><br>"
            "<small style='color: #A0A0A0;'>Atalho: Ctrl + B</small>"
            "<br><br>"
            "Aumenta a espessura da fonte para dar destaque ao texto selecionado.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Ideal para chamar a atenção para nomes, cargos ou informações cruciais no documento.</small>"
        )
        self.btn_bold.clicked.connect(lambda: self.set_format_attribute("bold"))

        self.btn_italic = QPushButton("I")
        self.btn_italic.setFixedWidth(30)
        self.btn_italic.setStyleSheet("font-style: italic")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setToolTip(
            "<b>ITÁLICO</b><br>"
            "<small style='color: #A0A0A0;'>Atalho: Ctrl + I</small>"
            "<br><br>"
            "Inclina o texto selecionado, alterando seu estilo visual sem mudar o peso.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Utilize para destacar citações, nomes científicos ou palavras de origem estrangeira.</small>"
        )
        self.btn_italic.clicked.connect(lambda: self.set_format_attribute("italic"))

        self.btn_underline = QPushButton("U")
        self.btn_underline.setFixedWidth(30)
        self.btn_underline.setStyleSheet("text-decoration: underline")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setToolTip(
            "<b>SUBLINHADO</b><br>"
            "<small style='color: #A0A0A0;'>Atalho: Ctrl + U</small>"
            "<br><br>"
            "Adiciona uma linha contínua sob o texto para ressaltar informações.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Evite usar em blocos de texto muito grandes para não sobrecarregar o design.</small>"
        )
        self.btn_underline.clicked.connect(lambda: self.set_format_attribute("underline"))

        self.btn_color = QPushButton("")
        self.btn_color.setFixedWidth(30)
        self.btn_color.setToolTip(
            "<b>COR DO TEXTO</b><br><br>"
            "Abre a paleta de cores para personalizar o texto ou a seleção atual.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Procure manter um alto contraste com o fundo para garantir a legibilidade após a impressão.</small>")
        self.btn_color.setStyleSheet("background-color: #000000; border: 1px solid #aaa; border-radius: 3px;")
        self.btn_color.clicked.connect(self._choose_color)

        row_style.addWidget(self.btn_bold)
        row_style.addWidget(self.btn_italic)
        row_style.addWidget(self.btn_underline)
        row_style.addWidget(self.btn_color)
        
        self.cbo_align = QComboBox()
        self.cbo_align.addItems(["Esquerda", "Centro", "Direita", "Justificado"])
        self.cbo_align.setToolTip(
            "<b>ALINHAMENTO HORIZONTAL</b><br><br>"
            "Define a posição do texto em relação às laterais da caixa:<br>"
            "• <b>Justificado:</b> Distribui o texto para preencher toda a largura da moldura.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: O alinhamento justificado cria margens retas e profissionais em blocos de texto mais densos.</small>")
        self._align_map = ["left", "center", "right", "justify"]
        self.cbo_align.currentIndexChanged.connect(lambda idx: self.alignChanged.emit(self._align_map[idx]))

        self.cbo_valign = QComboBox()
        self.cbo_valign.addItems(["Topo", "Meio", "Base"])
        self.cbo_valign.setToolTip(
            "<b>ALINHAMENTO VERTICAL</b><br><br>"
            "Posiciona o conteúdo verticalmente dentro da moldura da caixa:<br>"
            "• <b>Ancoragem:</b> Fixa o texto no Topo, no Meio ou na Base da caixa.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Combine o alinhamento 'Meio' com uma caixa alta para garantir que nomes e cargos fiquem sempre centralizados.</small>")
        self._valign_map = ["top", "center", "bottom"]
        self.cbo_valign.currentIndexChanged.connect(lambda idx: self.verticalAlignChanged.emit(self._valign_map[idx]))

        row_style.addWidget(self.cbo_align)
        row_style.addWidget(self.cbo_valign)
        layout.addLayout(row_style)

        form_space = QFormLayout()
        
        # Recuo com label manual para tooltip
        lbl_indent = QLabel("Recuo 1ª (px):")
        lbl_indent.setToolTip(
            "<b>RECUO DA PRIMEIRA LINHA</b><br><br>"
            "Define o recuo horizontal inicial do bloco de texto.<br><br>"
            "• <b>Estética:</b> Cria o efeito visual de parágrafo organizado.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Um valor entre 20 e 40px é o ideal para documentos formais.</small>")
        
        self.spin_indent = MathDoubleSpinBox()
        self.spin_indent.setRange(0, 500)
        self.spin_indent.valueChanged.connect(self._on_indent_changed)
        form_space.addRow(lbl_indent, self.spin_indent)
        
        # Entrelinha com label manual para tooltip
        lbl_lh = QLabel("Entrelinha:")
        lbl_lh.setToolTip(
            "<b>ENTRELINHA</b><br><br>"
            "Controla a distância vertical entre as linhas do parágrafo.<br><br>"
            "• <b>Legibilidade:</b> Valores maiores tornam a leitura mais fluida.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: 1.15 é o padrão de conforto; use 1.0 para compactar informações.</small>")

        self.spin_lh = MathDoubleSpinBox()
        self.spin_lh.setRange(0.5, 5.0)
        self.spin_lh.setSingleStep(0.1)
        self.spin_lh.setValue(1.15)
        self.spin_lh.valueChanged.connect(lambda val: self.lineHeightChanged.emit(val))
        form_space.addRow(lbl_lh, self.spin_lh)
        
        layout.addLayout(form_space)
        layout.addStretch()
        self.txt_content.cursorPositionChanged.connect(self.update_buttons_state)

        # Gatilhos de Snapshot da UI
        self.txt_content.editingFinished.connect(self.snapshotRequested.emit)
        self.cbo_font.activated.connect(lambda _: self.snapshotRequested.emit())
        self.spin_size.editingFinished.connect(self.snapshotRequested.emit)
        self.btn_bold.clicked.connect(self.snapshotRequested.emit)
        self.btn_italic.clicked.connect(self.snapshotRequested.emit)
        self.btn_underline.clicked.connect(self.snapshotRequested.emit)
        self.cbo_align.activated.connect(lambda _: self.snapshotRequested.emit())
        self.cbo_valign.activated.connect(lambda _: self.snapshotRequested.emit())
        self.spin_indent.editingFinished.connect(self.snapshotRequested.emit)
        self.spin_lh.editingFinished.connect(self.snapshotRequested.emit)

    def load_from_item(self, box: DesignerBox):
        self.blockSignals(True)
        self.txt_content.blockSignals(True)

        state = box.state

        # 1. Limpeza Retroativa UI: Remove links/cores antigas do JSON antes de jogar no painel
        clean_html = re.sub(r"font-family\s*:[^;\"]+;?", "", state.html_content)
        clean_html = re.sub(r"font-size\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"color\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"background-color\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"text-decoration\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"line-height\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"(?i)<a\b[^>]*>", "", clean_html)
        clean_html = re.sub(r"(?i)</a>", "", clean_html)
        clean_html = re.sub(r"(?i)<h[1-6]([^>]*)>", r"<p\1>", clean_html)
        clean_html = re.sub(r"(?i)</h[1-6]>", "</p>", clean_html)

        # Carrega o conteúdo purificado no editor e força fonte padrão UI
        self.txt_content.setHtml(clean_html)

        cursor = self.txt_content.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.txt_content.setTextCursor(cursor)

        # 2. Preenche os controles com os metadados puros da Fonte da Verdade
        self.cbo_font.setCurrentFont(QFont(state.font_family))
        self.spin_size.setValue(state.font_size)
        
        color_hex = getattr(state, 'font_color', '#000000')
        self.btn_color.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #aaa; border-radius: 3px;")
        
        self.update_buttons_state()

        if state.align == "right": self.cbo_align.setCurrentIndex(2)
        elif state.align == "center": self.cbo_align.setCurrentIndex(1)
        elif state.align == "justify": self.cbo_align.setCurrentIndex(3)
        else: self.cbo_align.setCurrentIndex(0)

        if state.vertical_align == "center": self.cbo_valign.setCurrentIndex(1)
        elif state.vertical_align == "bottom": self.cbo_valign.setCurrentIndex(2)
        else: self.cbo_valign.setCurrentIndex(0)

        self.spin_indent.setValue(state.indent_px)
        self.spin_lh.setValue(state.line_height)

        # Refletir o recuo no próprio editor de texto para feedback visual
        cursor_block = QTextCursor(self.txt_content.document())
        cursor_block.select(QTextCursor.SelectionType.Document)
        fmt = QTextBlockFormat()
        fmt.setTextIndent(state.indent_px)
        cursor_block.mergeBlockFormat(fmt)

        self.txt_content.blockSignals(False)
        self.blockSignals(False)
    
    def update_buttons_state(self):
        fmt = self.txt_content.currentCharFormat()
        
        self.btn_bold.blockSignals(True)
        self.btn_italic.blockSignals(True)
        self.btn_underline.blockSignals(True)

        self.btn_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.btn_italic.setChecked(fmt.fontItalic())
        self.btn_underline.setChecked(fmt.fontUnderline())

        self.btn_bold.blockSignals(False)
        self.btn_italic.blockSignals(False)
        self.btn_underline.blockSignals(False)

    def set_font_family(self, font):
        self.fontFamilyChanged.emit(font)
        self.txt_content.setFocus()

    def set_font_size(self, size):
        self.fontSizeChanged.emit(size)

    def set_format_attribute(self, attr_type):
        cursor = self.txt_content.textCursor()

        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        fmt = QTextCharFormat()

        if attr_type == "bold":
            desired_on = self.btn_bold.isChecked()
            fmt.setFontWeight(QFont.Weight.Bold if desired_on else QFont.Weight.Normal)
        elif attr_type == "italic":
            desired_on = self.btn_italic.isChecked()
            fmt.setFontItalic(desired_on)
        elif attr_type == "underline":
            desired_on = self.btn_underline.isChecked()
            fmt.setFontUnderline(desired_on)

        cursor.mergeCharFormat(fmt)
        self.txt_content.mergeCurrentCharFormat(fmt)
        self.txt_content.setFocus()

    def _choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            self.btn_color.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #aaa; border-radius: 3px;")
            self.fontColorChanged.emit(hex_color)
            self.snapshotRequested.emit()
            self.txt_content.setFocus()

    def _on_indent_changed(self, val):
        self.indentChanged.emit(val)
        # Atualiza o feedback visual do espaçamento em tempo real enquanto digita
        cursor = QTextCursor(self.txt_content.document())
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextBlockFormat()
        fmt.setTextIndent(val)
        cursor.mergeBlockFormat(fmt)

    def _emit_clean_html(self):
        raw_html = self.txt_content.toHtml()
        
        # FAXINA GERAL: Remove fontes, tamanhos, cores, fundos e decorações indesejadas do Ctrl+V
        clean_html = re.sub(r"font-family\s*:[^;\"]+;?", "", raw_html)
        clean_html = re.sub(r"font-size\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"color\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"background-color\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"text-decoration\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"line-height\s*:[^;\"]+;?", "", clean_html)
        
        # Extermina Hiperlinks fantasmas (tags <a>) mantendo apenas o texto limpo
        clean_html = re.sub(r"(?i)<a\b[^>]*>", "", clean_html)
        clean_html = re.sub(r"(?i)</a>", "", clean_html)
        
        # Rebaixa tags de título (h1, h2...) para parágrafos comuns (p)
        clean_html = re.sub(r"(?i)<h[1-6]([^>]*)>", r"<p\1>", clean_html)
        clean_html = re.sub(r"(?i)</h[1-6]>", "</p>", clean_html)
        
        self.htmlChanged.emit(clean_html)

class AssinaturaPanel(QWidget):
    sideChanged = Signal(int)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        lbl = QLabel("PROPRIEDADES DA IMAGEM / ASSINATURA")
        lbl.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(lbl)
        
        form = QFormLayout()
        self.spin_size = QSpinBox()
        self.spin_size.setRange(10, 2000)
        self.spin_size.setSuffix(" px")
        self.spin_size.setToolTip(
            "<b>DIMENSIONAMENTO PROPORCIONAL</b><br><br>"
            "Ajusta o tamanho do objeto baseando-se no seu lado mais comprido:<br>"
            "• <b>Automático:</b> A largura e altura são calculadas para evitar distorções na imagem.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Utilize este campo para garantir que todas as assinaturas do projeto mantenham uma escala uniforme.</small>")
        self.spin_size.valueChanged.connect(self.sideChanged.emit)
        
        form.addRow("Lado Maior:", self.spin_size)
        layout.addLayout(form)
        layout.addStretch()

    def load_from_item(self, item: SignatureItem):
        self.blockSignals(True)
        rect = item.pixmap().rect()
        self.spin_size.setValue(max(rect.width(), rect.height()))
        self.blockSignals(False)
