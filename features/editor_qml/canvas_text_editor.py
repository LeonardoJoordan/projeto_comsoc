"""Edição nativa sobre o canvas, com o mesmo QTextDocument do renderer."""
from copy import deepcopy
import re

from PySide6.QtCore import Property, Signal, Slot, Qt, QRectF, QPointF
from PySide6.QtGui import (QAbstractTextDocumentLayout, QColor, QFont, QGuiApplication,
                          QKeySequence, QPainter, QPicture, QTextBlockFormat,
                          QTextCharFormat, QTextCursor, QTextDocument)
from PySide6.QtQuick import QQuickPaintedItem, QQuickItem
from PySide6.QtWidgets import QInputDialog
from core.text_layout import build_document, text_geometry, ALIGNMENTS
from core.object_style import outline_margin


class CanvasTextEditor(QQuickPaintedItem):
    contentsEdited = Signal(str)
    formatChanged = Signal()
    geometryChanged = Signal()
    finishRequested = Signal()
    feedback = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setKeepMouseGrab(True)
        self.setFlag(QQuickItem.ItemAcceptsInputMethod, True)
        self.setAntialiasing(True)
        self._doc = QTextDocument(self)
        self._cursor = QTextCursor(self._doc)
        self._box = {}
        self._offset = 0
        self._top = 0
        self._height = 100
        self._dragging = False
        self._preedit = ""
        self._updating = False
        self._picture = QPicture()
        self._connect_document()
        self.activeFocusChanged.connect(self._refresh)

    def _connect_document(self):
        self._doc.contentsChanged.connect(self._content_changed)

    @Slot("QVariantMap")
    def beginEditing(self, box):
        self._box = deepcopy(box)
        previous = self._doc
        self._doc = build_document(box, box.get("html", "<p></p>"))
        self._doc.setParent(self)
        self._doc.setUndoRedoEnabled(True)
        self._doc.clearUndoRedoStacks()
        self._cursor = QTextCursor(self._doc)
        self._cursor.movePosition(QTextCursor.End)
        self._connect_document()
        previous.deleteLater()
        self._preedit = ""
        self._refresh()
        self.forceActiveFocus()

    @Property(float, notify=geometryChanged)
    def contentLeft(self):
        return -outline_margin(self._box)

    @Property(float, notify=geometryChanged)
    def contentTop(self):
        return self._top

    @Property(float, notify=geometryChanged)
    def paintHeight(self):
        return self._height

    @Property(str, notify=formatChanged)
    def text(self):
        return self._doc.toHtml()

    @Property("QVariantMap", notify=formatChanged)
    def formatState(self):
        fmt, block = self._cursor.charFormat(), self._cursor.blockFormat()
        alignment = block.alignment() if block.hasProperty(QTextBlockFormat.BlockAlignment) else self._doc.defaultTextOption().alignment()
        return {"bold": fmt.fontWeight() >= QFont.Bold, "italic": fmt.fontItalic(),
                "underline": fmt.fontUnderline(), "font_family": fmt.font().family() or self._doc.defaultFont().family(),
                "font_size": fmt.fontPointSize() or self._doc.defaultFont().pointSizeF(),
                "font_color": fmt.foreground().color().name() if fmt.hasProperty(QTextCharFormat.ForegroundBrush) else self._box.get("font_color", "#000000"),
                "align": next((key for key, flag in ALIGNMENTS.items() if alignment & flag), "left"),
                "vertical_align": self._box.get("vertical_align", "top"),
                "indent_px": block.textIndent(),
                "line_height": block.lineHeight()/100 if block.lineHeightType() == QTextBlockFormat.ProportionalHeight else self._box.get("line_height", 1.15),
                "hasSelection": self._cursor.hasSelection(), "selectionStart": self._cursor.selectionStart(),
                "selectionEnd": self._cursor.selectionEnd(), "canUndo": self._doc.isUndoAvailable(),
                "canRedo": self._doc.isRedoAvailable()}

    def _content_changed(self):
        if self._updating:
            return
        self._refresh()
        self.contentsEdited.emit(self._doc.toHtml())

    def _refresh(self):
        self._offset, _, _ = text_geometry(self._doc, self._box)
        margin = outline_margin(self._box)
        self._top = min(0, self._offset) - margin
        self._height = max(self._box.get("h", 100), self._offset + self._doc.size().height()) - self._top + margin + 2
        self.geometryChanged.emit()
        self.formatChanged.emit()
        self._record_paint()
        self.update()
        if QGuiApplication.inputMethod():
            QGuiApplication.inputMethod().update(Qt.ImQueryAll)

    def caretRect(self):
        block = self._cursor.block()
        layout = block.layout()
        line = layout.lineForTextPosition(self._cursor.positionInBlock())
        if not line.isValid():
            return QRectF(0, self._offset-self._top, 1, 20)
        x = line.cursorToX(self._cursor.positionInBlock())
        if isinstance(x, tuple): x = x[0]
        bounds = self._doc.documentLayout().blockBoundingRect(block)
        return QRectF(bounds.x()+x-self.contentLeft, bounds.y()+line.y()+self._offset-self._top, 1, line.height())

    def paint(self, painter):
        # Qt Quick pode chamar paint na QSGRenderThread. O documento e o cursor
        # pertencem à GUI; reproduza somente comandos de pintura já preparados.
        painter.drawPicture(0, 0, self._picture)

    def _record_paint(self):
        picture = QPicture()
        painter = QPainter(picture)
        try:
            self._paint_document(painter)
        finally:
            painter.end()
        self._picture = picture

    def _paint_document(self, painter):
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.save()
        painter.translate(-self.contentLeft, self._offset-self._top)
        context = QAbstractTextDocumentLayout.PaintContext()
        if self._cursor.hasSelection():
            selection = QAbstractTextDocumentLayout.Selection()
            selection.cursor = self._cursor
            selection.format.setBackground(QColor("#7C73F2"))
            selection.format.setForeground(QColor("white"))
            context.selections = [selection]
        self._doc.documentLayout().draw(painter, context)
        painter.restore()
        if self.hasActiveFocus():
            caret = self.caretRect()
            painter.fillRect(caret, QColor(self.formatState["font_color"]))
            if self._preedit:
                painter.setFont(self._cursor.charFormat().font())
                painter.setPen(QColor(self.formatState["font_color"]))
                painter.drawText(caret.bottomLeft(), self._preedit)

    def _hit(self, pos):
        pos = QPointF(pos.x()+self.contentLeft, pos.y()-self._offset+self._top)
        return max(0, min(self._doc.characterCount()-1, self._doc.documentLayout().hitTest(pos, Qt.FuzzyHit)))

    def mousePressEvent(self, event):
        self.forceActiveFocus()
        if event.button() == Qt.RightButton:
            event.ignore()
            return
        mode = QTextCursor.KeepAnchor if event.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
        self._cursor.setPosition(self._hit(event.position()), mode)
        self._dragging = True
        self._refresh()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._cursor.setPosition(self._hit(event.position()), QTextCursor.KeepAnchor)
            self._refresh()
        event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        self._cursor.setPosition(self._hit(event.position()))
        self._cursor.select(QTextCursor.WordUnderCursor)
        self._refresh()
        event.accept()

    @Slot(int, int)
    def selectRange(self, start, end):
        maximum = self._doc.characterCount()-1
        self._cursor.setPosition(max(0, min(maximum, start)))
        self._cursor.setPosition(max(0, min(maximum, end)), QTextCursor.KeepAnchor)
        self._refresh()

    @Slot(str, "QVariant")
    def applyFormat(self, key, value):
        fmt = QTextCharFormat()
        current = self._cursor.charFormat()
        if key == "Negrito": fmt.setFontWeight(QFont.Normal if current.fontWeight() >= QFont.Bold else QFont.Bold)
        elif key == "Itálico": fmt.setFontItalic(not current.fontItalic())
        elif key == "Sublinhado": fmt.setFontUnderline(not current.fontUnderline())
        elif key == "font_family": fmt.setFontFamilies([str(value)])
        elif key == "font_size": fmt.setFontPointSize(float(str(value).replace(",", ".")))
        elif key == "font_color": fmt.setForeground(QColor(str(value)))
        elif key in ("align", "indent_px", "line_height"):
            block = QTextBlockFormat()
            if key == "align": block.setAlignment(ALIGNMENTS.get(value, Qt.AlignLeft))
            elif key == "indent_px": block.setTextIndent(float(str(value).replace(",", ".")))
            else: block.setLineHeight(float(str(value).replace(",", "."))*100, QTextBlockFormat.ProportionalHeight)
            self._cursor.mergeBlockFormat(block)
            self._refresh()
            return
        elif key == "vertical_align":
            self._box[key] = value
            self._refresh()
            return
        else: return
        self._cursor.mergeCharFormat(fmt)
        self._refresh()

    @Slot(str)
    def insertText(self, value):
        self._cursor.insertText(value)
        self._refresh()

    @Slot(str, result=bool)
    def insertVariable(self, name):
        name = name.strip().strip("{}")
        if not re.fullmatch(r"[a-zA-Z0-9_]+", name):
            self.feedback.emit("Use letras sem acento, números e sublinhado no nome da variável.")
            return False
        self._cursor.insertText("{"+name+"}")
        self._refresh()
        return True

    @Slot()
    def promptVariable(self):
        name, accepted = QInputDialog.getText(None, "Inserir variável", "Nome da variável:", text=self._cursor.selectedText().strip("{}"))
        if accepted: self.insertVariable(name)
        self.forceActiveFocus()

    @Slot(result=bool)
    def wrapOptional(self):
        if not self._cursor.hasSelection():
            self.feedback.emit("Selecione o trecho que deseja tornar opcional.")
            return False
        start, end = self._cursor.selectionStart(), self._cursor.selectionEnd()
        self._cursor.beginEditBlock()
        self._cursor.setPosition(end)
        self._cursor.insertText("|")
        self._cursor.setPosition(start)
        self._cursor.insertText("|")
        self._cursor.endEditBlock()
        self.selectRange(start, end+2)
        return True

    @Slot(str)
    def command(self, action):
        clipboard = QGuiApplication.clipboard()
        if action == "copy":
            from PySide6.QtCore import QMimeData
            from PySide6.QtGui import QTextDocumentFragment
            mime = QMimeData()
            fragment = QTextDocumentFragment(self._cursor)
            mime.setText(fragment.toPlainText())
            mime.setHtml(fragment.toHtml())
            mime.setData("application/x-comsoc-rich-text", fragment.toHtml().encode("utf-8"))
            clipboard.setMimeData(mime)
        elif action == "cut":
            if self._cursor.hasSelection():
                self.command("copy")
                self._cursor.removeSelectedText()
        elif action == "paste":
            mime = clipboard.mimeData()
            if mime and mime.hasHtml():
                # Use the legacy cleanup for external formatting, retaining B/I/U.
                from PySide6.QtGui import QTextDocumentFragment
                own = mime.hasFormat("application/x-comsoc-rich-text")
                clean = build_document({**self._box, "rich_text_version": int(own)}, mime.html())
                self._cursor.insertFragment(QTextDocumentFragment(clean))
            else: self._cursor.insertText(clipboard.text())
        elif action == "selectAll": self._cursor.select(QTextCursor.Document)
        elif action == "undo": self._doc.undo(self._cursor)
        elif action == "redo": self._doc.redo(self._cursor)
        self._refresh()

    def keyPressEvent(self, event):
        for sequence, command in ((QKeySequence.Copy,"copy"), (QKeySequence.Cut,"cut"),
                                  (QKeySequence.Paste,"paste"), (QKeySequence.SelectAll,"selectAll"),
                                  (QKeySequence.Undo,"undo"), (QKeySequence.Redo,"redo")):
            if event.matches(sequence):
                self.command(command)
                event.accept()
                return
        key, mods = event.key(), event.modifiers()
        if mods & Qt.ControlModifier and key in (Qt.Key_B, Qt.Key_I, Qt.Key_U):
            self.applyFormat({Qt.Key_B:"Negrito", Qt.Key_I:"Itálico", Qt.Key_U:"Sublinhado"}[key], True)
        elif mods & Qt.ControlModifier and key == Qt.Key_1: self.promptVariable()
        elif mods & Qt.ControlModifier and key == Qt.Key_2: self.wrapOptional()
        elif key == Qt.Key_Escape or (key in (Qt.Key_Return,Qt.Key_Enter) and mods & Qt.ControlModifier): self.finishRequested.emit()
        elif key in (Qt.Key_Return,Qt.Key_Enter): self._cursor.insertBlock()
        elif key == Qt.Key_Backspace: self._cursor.deletePreviousChar()
        elif key == Qt.Key_Delete: self._cursor.deleteChar()
        elif key in (Qt.Key_Left,Qt.Key_Right,Qt.Key_Up,Qt.Key_Down,Qt.Key_Home,Qt.Key_End):
            moves = {Qt.Key_Left: QTextCursor.PreviousCharacter, Qt.Key_Right: QTextCursor.NextCharacter,
                     Qt.Key_Up: QTextCursor.Up, Qt.Key_Down: QTextCursor.Down,
                     Qt.Key_Home: QTextCursor.StartOfLine, Qt.Key_End: QTextCursor.EndOfLine}
            if mods & Qt.ControlModifier:
                moves.update({Qt.Key_Left: QTextCursor.PreviousWord, Qt.Key_Right: QTextCursor.NextWord,
                              Qt.Key_Home: QTextCursor.Start, Qt.Key_End: QTextCursor.End})
            self._cursor.movePosition(moves[key], QTextCursor.KeepAnchor if mods & Qt.ShiftModifier else QTextCursor.MoveAnchor)
        elif event.text() and not (mods & (Qt.ControlModifier | Qt.AltModifier)): self._cursor.insertText(event.text())
        else:
            event.ignore()
            return
        self._refresh()
        event.accept()

    def inputMethodEvent(self, event):
        if event.commitString() or event.replacementLength():
            if event.replacementLength():
                position = self._cursor.position()+event.replacementStart()
                self.selectRange(position, position+event.replacementLength())
            self._cursor.insertText(event.commitString())
        self._preedit = event.preeditString()
        self._refresh()
        event.accept()

    def inputMethodQuery(self, query):
        values = {Qt.ImEnabled: True, Qt.ImCursorRectangle: self.caretRect(),
                  Qt.ImSurroundingText: self._doc.toPlainText(), Qt.ImCurrentSelection: self._cursor.selectedText(),
                  Qt.ImCursorPosition: self._cursor.position(), Qt.ImAnchorPosition: self._cursor.anchor(),
                  Qt.ImFont: self._cursor.charFormat().font()}
        return values.get(query, super().inputMethodQuery(query))
