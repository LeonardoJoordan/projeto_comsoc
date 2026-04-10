from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
                               QFormLayout, QTextEdit, QFontComboBox, QPushButton, 
                               QComboBox, QDoubleSpinBox, QColorDialog, QCheckBox)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QFont, QTextCursor, QTextBlockFormat, QTextCharFormat
import re

from .canvas_items import DesignerBox, SignatureItem, ImageItem, px_to_mm


class CleanTextEdit(QTextEdit):
    """Campo de texto customizado que intercepta o Ctrl+V e purifica o HTML."""
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
    widthChanged = Signal(int)
    heightChanged = Signal(int)
    rotationChanged = Signal(int)
    proportionToggled = Signal(bool) # Novo sinal para a Checkbox
    restoreRequested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("<b>DIMENSÕES E ROTAÇÃO</b>")
        layout.addWidget(lbl)
        self._aspect_ratio = 1.0
        
        form = QFormLayout()
        form.setSpacing(4)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.spin_w = QDoubleSpinBox()
        self.spin_w.setRange(1.0, 5000.0)
        self.spin_w.setDecimals(1)
        self.spin_w.setSuffix(" mm")
        self.spin_w.setKeyboardTracking(False)
        self.spin_w.valueChanged.connect(self.widthChanged.emit)
        form.addRow("Larg:", self.spin_w)

        self.spin_h = QDoubleSpinBox()
        self.spin_h.setRange(1.0, 5000.0)
        self.spin_h.setDecimals(1)
        self.spin_h.setSuffix(" mm")
        self.spin_h.setKeyboardTracking(False)
        self.spin_h.valueChanged.connect(self.heightChanged.emit)
        form.addRow("Alt:", self.spin_h)

        self.spin_rot = QSpinBox()
        self.chk_proporcao = QCheckBox("Manter proporção")
        self.chk_proporcao.setChecked(True)
        self.chk_proporcao.toggled.connect(self.proportionToggled.emit)
        form.addRow("", self.chk_proporcao)

        # Intercepta os sinais para calcular a proporção antes de emitir para a cena
        self.spin_w.valueChanged.disconnect(self.widthChanged.emit)
        self.spin_h.valueChanged.disconnect(self.heightChanged.emit)
        self.spin_w.valueChanged.connect(self._on_w_changed)
        self.spin_h.valueChanged.connect(self._on_h_changed)
        self.spin_rot.setRange(-360, 360)
        self.spin_rot.setSuffix(" °")
        self.spin_rot.setWrapping(True) 
        self.spin_rot.valueChanged.connect(self.rotationChanged.emit)
        form.addRow("Rot:", self.spin_rot)

        self.btn_restore = QPushButton("🔄 Restaurar Original")
        self.btn_restore.setToolTip("Restaura as dimensões originais e zera a rotação")
        self.btn_restore.clicked.connect(self.restoreRequested.emit)
        form.addRow("", self.btn_restore)

        layout.addLayout(form)
        layout.addStretch()

    def load_from_item(self, box: DesignerBox):
        self.blockSignals(True) 
        rect = box.rect()
        self.spin_w.setValue(px_to_mm(rect.width()))
        self.spin_h.setValue(px_to_mm(rect.height()))
        self.spin_rot.setValue(int(box.rotation()))
        if rect.height() > 0: self._aspect_ratio = rect.width() / rect.height()
        
        self.chk_proporcao.blockSignals(True)
        self.chk_proporcao.setChecked(getattr(box, 'keep_proportion', True))
        self.chk_proporcao.blockSignals(False)
        self.blockSignals(False)

    def load_from_image(self, img):
        self.blockSignals(True)
        rect = img.pixmap().rect()
        self.spin_w.setValue(px_to_mm(rect.width()))
        self.spin_h.setValue(px_to_mm(rect.height()))
        self.spin_rot.setValue(int(img.rotation()))
        if rect.height() > 0: self._aspect_ratio = rect.width() / rect.height()
        
        self.chk_proporcao.blockSignals(True)
        self.chk_proporcao.setChecked(getattr(img, 'keep_proportion', True))
        self.chk_proporcao.blockSignals(False)
        self.blockSignals(False)

    def _on_w_changed(self, val):
        if self.chk_proporcao.isChecked() and self._aspect_ratio > 0:
            self.spin_h.blockSignals(True)
            self.spin_h.setValue(val / self._aspect_ratio)
            self.spin_h.blockSignals(False)
        self.widthChanged.emit(val)

    def _on_h_changed(self, val):
        if self.chk_proporcao.isChecked() and self._aspect_ratio > 0:
            self.spin_w.blockSignals(True)
            self.spin_w.setValue(val * self._aspect_ratio)
            self.spin_w.blockSignals(False)
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

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl = QLabel("EDITOR DE TEXTO")
        lbl.setStyleSheet("font-weight: bold; font-size: 12px; border-bottom: 1px solid #ccc;")
        layout.addWidget(lbl)
        
        layout.addWidget(QLabel("Texto:"))
        
        self.txt_content = CleanTextEdit()
        self.txt_content.setMinimumHeight(160)
        self.txt_content.setStyleSheet("background-color: #FFFFFF; color: #000000; border: 1px solid #aaa; font-family: sans-serif; font-size: 11pt;")
        self.txt_content.textChanged.connect(self._emit_clean_html)
        
        # INSERE A CAIXA NO LAYOUT PARA ELA APARECER
        layout.addWidget(self.txt_content)
        
        row_font = QHBoxLayout()
        self.cbo_font = QFontComboBox()
        self.cbo_font.currentFontChanged.connect(self.set_font_family)
        self.spin_size = QSpinBox()
        self.spin_size.setRange(6, 300)
        self.spin_size.valueChanged.connect(self.set_font_size)
        row_font.addWidget(self.cbo_font, 2)
        row_font.addWidget(self.spin_size, 1)
        layout.addLayout(row_font)

        row_style = QHBoxLayout()
        
        self.btn_bold = QPushButton("B")
        self.btn_bold.setFixedWidth(30)
        self.btn_bold.setStyleSheet("font-weight: bold")
        self.btn_bold.setCheckable(True)
        self.btn_bold.clicked.connect(lambda: self.set_format_attribute("bold"))

        self.btn_italic = QPushButton("I")
        self.btn_italic.setFixedWidth(30)
        self.btn_italic.setStyleSheet("font-style: italic")
        self.btn_italic.setCheckable(True)
        self.btn_italic.clicked.connect(lambda: self.set_format_attribute("italic"))

        self.btn_underline = QPushButton("U")
        self.btn_underline.setFixedWidth(30)
        self.btn_underline.setStyleSheet("text-decoration: underline")
        self.btn_underline.setCheckable(True)
        self.btn_underline.clicked.connect(lambda: self.set_format_attribute("underline"))

        self.btn_color = QPushButton("")
        self.btn_color.setFixedWidth(30)
        self.btn_color.setToolTip("Cor do Texto")
        self.btn_color.setStyleSheet("background-color: #000000; border: 1px solid #aaa; border-radius: 3px;")
        self.btn_color.clicked.connect(self._choose_color)

        row_style.addWidget(self.btn_bold)
        row_style.addWidget(self.btn_italic)
        row_style.addWidget(self.btn_underline)
        row_style.addWidget(self.btn_color)
        
        self.cbo_align = QComboBox()
        self.cbo_align.addItems(["Esq", "Cen", "Dir", "Just"])
        self.cbo_align.setToolTip("Alinhamento Horizontal")
        self._align_map = ["left", "center", "right", "justify"]
        self.cbo_align.currentIndexChanged.connect(lambda idx: self.alignChanged.emit(self._align_map[idx]))

        self.cbo_valign = QComboBox()
        self.cbo_valign.addItems(["Topo", "Meio", "Base"])
        self.cbo_valign.setToolTip("Alinhamento Vertical")
        self._valign_map = ["top", "center", "bottom"]
        self.cbo_valign.currentIndexChanged.connect(lambda idx: self.verticalAlignChanged.emit(self._valign_map[idx]))

        row_style.addWidget(self.cbo_align)
        row_style.addWidget(self.cbo_valign)
        layout.addLayout(row_style)

        form_space = QFormLayout()
        self.spin_indent = QDoubleSpinBox()
        self.spin_indent.setRange(0, 500)
        self.spin_indent.setSuffix(" px")
        self.spin_indent.valueChanged.connect(self._on_indent_changed)
        form_space.addRow("Recuo 1ª:", self.spin_indent)
        
        self.spin_lh = QDoubleSpinBox()
        self.spin_lh.setRange(0.5, 5.0)
        self.spin_lh.setSingleStep(0.1)
        self.spin_lh.setValue(1.15)
        self.spin_lh.valueChanged.connect(lambda val: self.lineHeightChanged.emit(val))
        form_space.addRow("Entrelinha:", self.spin_lh)
        
        layout.addLayout(form_space)
        layout.addStretch()
        self.txt_content.cursorPositionChanged.connect(self.update_buttons_state)

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
        self.txt_content.setFocus()

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
        self.spin_size.setToolTip("Define o tamanho do maior lado (largura ou altura)")
        self.spin_size.valueChanged.connect(self.sideChanged.emit)
        
        form.addRow("Lado Maior:", self.spin_size)
        layout.addLayout(form)
        layout.addStretch()

    def load_from_item(self, item: SignatureItem):
        self.blockSignals(True)
        rect = item.pixmap().rect()
        self.spin_size.setValue(max(rect.width(), rect.height()))
        self.blockSignals(False)