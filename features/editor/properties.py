from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
                               QFormLayout, QTextEdit, QFontComboBox, QPushButton, 
                               QComboBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor, QTextBlockFormat, QTextCharFormat
import re

from .canvas_items import DesignerBox, SignatureItem

class CaixaDeTextoPanel(QWidget):
    widthChanged = Signal(int)
    heightChanged = Signal(int)
    rotationChanged = Signal(int)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("<b>DIMENSÕES DA CAIXA</b>")
        layout.addWidget(lbl)
        
        form = QFormLayout()
        form.setSpacing(4)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.spin_w = QSpinBox()
        self.spin_w.setRange(10, 5000)
        self.spin_w.setSuffix(" px")
        self.spin_w.valueChanged.connect(self.widthChanged.emit)
        form.addRow("Larg:", self.spin_w)

        self.spin_h = QSpinBox()
        self.spin_h.setRange(10, 5000)
        self.spin_h.setSuffix(" px")
        self.spin_h.valueChanged.connect(self.heightChanged.emit)
        form.addRow("Alt:", self.spin_h)

        self.spin_rot = QSpinBox()
        self.spin_rot.setRange(-360, 360)
        self.spin_rot.setSuffix(" °")
        self.spin_rot.setWrapping(True) 
        self.spin_rot.valueChanged.connect(self.rotationChanged.emit)
        form.addRow("Rot:", self.spin_rot)

        layout.addLayout(form)
        layout.addStretch()

    def load_from_item(self, box: DesignerBox):
        self.blockSignals(True) 
        rect = box.rect()
        self.spin_w.setValue(int(rect.width()))
        self.spin_h.setValue(int(rect.height()))
        self.spin_rot.setValue(int(box.rotation()))
        self.blockSignals(False)

class EditorDeTextoPanel(QWidget):
    htmlChanged = Signal(str)
    fontFamilyChanged = Signal(QFont)
    fontSizeChanged = Signal(int)
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
        self.txt_content = QTextEdit()
        self.txt_content.setStyleSheet("background-color: #FFFFFF; color: #000000;")
        self.txt_content.setMinimumHeight(160)
        self.txt_content.textChanged.connect(self._emit_clean_html)
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

        row_style.addWidget(self.btn_bold)
        row_style.addWidget(self.btn_italic)
        row_style.addWidget(self.btn_underline)
        
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

    def load_from_item(self, box: DesignerBox):
        self.blockSignals(True)
        self.txt_content.blockSignals(True)

        state = box.state

        # 1. Carrega apenas o conteúdo limpo no editor e força fonte padrão UI
        self.txt_content.setHtml(state.html_content)
        self.txt_content.setFont(QFont("Segoe UI", 11))

        cursor = self.txt_content.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.txt_content.setTextCursor(cursor)

        # 2. Preenche os controles com os metadados puros da Fonte da Verdade
        self.cbo_font.setCurrentFont(QFont(state.font_family))
        self.spin_size.setValue(state.font_size)
        
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
        # Regex corrigida: ignora aspas simples geradas pelo Qt no nome da fonte
        clean_html = re.sub(r"font-family\s*:[^;\"]+;?", "", raw_html)
        clean_html = re.sub(r"font-size\s*:[^;\"]+;?", "", clean_html)
        self.htmlChanged.emit(clean_html)

class AssinaturaPanel(QWidget):
    sideChanged = Signal(int)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        lbl = QLabel("PROPRIEDADES DA ASSINATURA")
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