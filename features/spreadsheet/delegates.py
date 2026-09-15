import re
from PySide6.QtWidgets import (QStyledItemDelegate, QStyle, QStyleOptionViewItem,
                               QApplication, QTextEdit, QToolTip, QAbstractItemDelegate)
from PySide6.QtGui import (QTextDocument, QPalette, QTextCursor, QFont, QPen, QColor)
from PySide6.QtCore import Qt, QEvent

class RichTextEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setFrameShape(QTextEdit.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            if key == Qt.Key.Key_B:
                self._toggle_weight()
                return
            elif key == Qt.Key.Key_I:
                self._toggle_italic()
                return
            elif key == Qt.Key.Key_U:
                self._toggle_underline()
                return
        super().keyPressEvent(event)

    def _toggle_weight(self):
        fmt = self.currentCharFormat()
        new_weight = QFont.Weight.Normal if fmt.fontWeight() > QFont.Weight.Normal else QFont.Weight.Bold
        fmt.setFontWeight(new_weight)
        self.mergeCurrentCharFormat(fmt)

    def _toggle_italic(self):
        fmt = self.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.mergeCurrentCharFormat(fmt)

    def _toggle_underline(self):
        fmt = self.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.mergeCurrentCharFormat(fmt)

class HTMLDelegate(QStyledItemDelegate):
    def eventFilter(self, editor, event):
        if isinstance(editor, RichTextEditor) and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # A tecla chega ao QTextEdit e vira uma quebra de linha.
                    return False
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)
                return True
        return super().eventFilter(editor, event)

    def helpEvent(self, event, view, option, index):
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or '')
        available = max(0, option.rect.width() - 20)
        clipped = '\n' in text or option.fontMetrics.horizontalAdvance(text) > available
        if clipped and text:
            QToolTip.showText(event.globalPos(), text, view, option.rect)
            return True
        QToolTip.hideText()
        return False

    def paint(self, painter, option, index):
        options = option
        self.initStyleOption(options, index)
        style = options.widget.style() if options.widget else QApplication.style()

        # No modo compacto cada célula ocupa uma única linha. O conteúdo real
        # permanece intacto no modelo, na barra fx e no tooltip.
        if not options.widget or not options.widget.wordWrap():
            text = str(index.data(Qt.ItemDataRole.DisplayRole) or '')
            options.text = re.sub(r'\s*[\r\n]+\s*', ' ', text)
            options.features &= ~QStyleOptionViewItem.ViewItemFeature.WrapText
            options.displayAlignment = (
                options.displayAlignment & Qt.AlignmentFlag.AlignHorizontal_Mask
            ) | Qt.AlignmentFlag.AlignVCenter
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, options, painter, options.widget)
            self._paint_current(painter, options, index)
            return
        
        rich_text = index.data(Qt.ItemDataRole.UserRole)
        
        if not rich_text:
            super().paint(painter, options, index)
            self._paint_current(painter, options, index)
            return

        painter.save()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, options, painter, options.widget)

        doc = QTextDocument()
        doc.setDefaultFont(options.font)
        doc.setHtml(rich_text)
        doc.setTextWidth(options.rect.width())
        doc.setDocumentMargin(2)

        if options.state & QStyle.StateFlag.State_Selected:
            text_color = options.palette.color(QPalette.ColorGroup.Normal, QPalette.ColorRole.HighlightedText).name()
        else:
            text_color = options.palette.color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Text).name()
            
        doc.setDefaultStyleSheet(f"body {{ color: {text_color}; }}")

        content_height = doc.size().height()
        y_offset = max(0, (options.rect.height() - content_height) / 2)
        
        painter.translate(options.rect.left(), options.rect.top() + y_offset)
        painter.setClipRect(0, 0, options.rect.width(), options.rect.height())
        doc.drawContents(painter)
        painter.restore()
        self._paint_current(painter, options, index)

    def _paint_current(self, painter, option, index):
        if option.widget and option.widget.currentIndex() == index:
            painter.save()
            painter.setPen(QPen(QColor('#8774df'), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
            painter.restore()

    def createEditor(self, parent, option, index):
        editor = RichTextEditor(parent)
        # Se for a coluna 0 (Cópias), força o alinhamento central no editor
        if index.column() == 0:
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return editor
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def setEditorData(self, editor, index):
        html = index.data(Qt.ItemDataRole.UserRole)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if html:
            editor.setHtml(html)
        else:
            editor.setText(text)
        editor.moveCursor(QTextCursor.MoveOperation.End)

    def setModelData(self, editor, model, index):
        raw_html = editor.toHtml()
        html_content_only = re.sub(r'<(head|style|script)[^>]*>.*?</\1>', '', raw_html, flags=re.IGNORECASE | re.DOTALL)
        plain = editor.toPlainText()
        
        # Como o editor do Qt gera um HTML muito poluído internamente ao editar,
        # limpamos as tags estruturais pesadas e salvamos o fragmento direto
        clean_html = re.sub(r'</?(html|body|meta|p)[^>]*>', '', html_content_only, flags=re.IGNORECASE).strip()
        
        model.setData(index, clean_html, Qt.ItemDataRole.UserRole)
        model.setData(index, plain, Qt.ItemDataRole.DisplayRole)
