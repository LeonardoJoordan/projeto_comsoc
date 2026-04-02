from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsRectItem, QGraphicsTextItem, 
                               QGraphicsItem, QInputDialog, QLineEdit, QGraphicsPixmapItem)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (QPen, QBrush, QColor, QFont, QTextCursor, 
                           QTextBlockFormat, QPixmap, QPainterPathStroker)
import re
from core.text_state import TextState

DPI = 96

def mm_to_px(mm):
    return (mm * DPI) / 25.4

def px_to_mm(px):
    return (px * 25.4) / DPI

class Guideline(QGraphicsLineItem):
    def __init__(self, position_px, is_vertical=True):
        super().__init__()
        self.is_vertical = is_vertical
        
        if is_vertical:
            self.setLine(0, -10000, 0, 10000)
            self.setPos(position_px, 0)
        else:
            self.setLine(-10000, 0, 10000, 0)
            self.setPos(0, position_px)

        pen = QPen(QColor("#00bcd4"), 1, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        self.setPen(pen)

        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setZValue(10)

    def shape(self):
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(10) 
        return stroker.createStroke(path)
    
    def mouseDoubleClickEvent(self, event):
        rect = self.scene().sceneRect()
        
        if self.is_vertical:
            axis_name = "Horizontal (X)"
            total_px = rect.width()
            current_px = self.pos().x()
        else:
            axis_name = "Vertical (Y)"
            total_px = rect.height()
            current_px = self.pos().y()

        total_mm = px_to_mm(total_px)
        current_mm = px_to_mm(current_px)

        label = (f"Posição (mm). Total disponível: {total_mm:.2f} mm\n"
                 f"Pode usar contas: '100/2', '{total_mm:.0f}-10', etc.")
        
        expression, ok = QInputDialog.getText(
            None, 
            f"Editar Guia {axis_name}", 
            label, 
            QLineEdit.EchoMode.Normal,
            f"{current_mm:.2f}"
        )

        if ok and expression:
            try:
                sanitized = expression.replace(",", ".")
                allowed_chars = set("0123456789.+-*/() ")
                if not set(sanitized).issubset(allowed_chars):
                    raise ValueError("Caracteres inválidos")
                
                final_val_mm = float(eval(sanitized))
                new_px = mm_to_px(final_val_mm)
                
                if self.is_vertical:
                    self.setPos(new_px, 0)
                else:
                    self.setPos(0, new_px)
                
                self.scene().update()
            except Exception as e:
                print(f"Erro na conta: {e}")

        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            rect = self.scene().sceneRect()
            snap_dist = 15 
            
            if self.is_vertical:
                x = new_pos.x()
                candidates = [0, rect.width() / 2, rect.width()]
                for c in candidates:
                    if abs(x - c) < snap_dist:
                        x = c
                        break 
                return QPointF(x, 0)
            else:
                y = new_pos.y()
                candidates = [0, rect.height() / 2, rect.height()]
                for c in candidates:
                    if abs(y - c) < snap_dist:
                        y = c
                        break
                return QPointF(0, y)
                
        return super().itemChange(change, value)

class DesignerBox(QGraphicsRectItem):
    SNAP_DISTANCE = 15

    def __init__(self, x=0, y=0, w=300, h=60, text="Placeholder"):
        super().__init__(0, 0, w, h)
        self.setPos(x, y)
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        self.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(255, 255, 255, 50)))
        self.setZValue(100)

        self.state = TextState(html_content=text)
        
        self.text_item = QGraphicsTextItem("", self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.black)
        
        self.text_item.document().contentsChanged.connect(self.recalculate_text_position)

        self.text_item.setTextWidth(w) 
        self.text_item.setPos(0, 0)
        
        self.apply_state()
        self.update_center()

    def update_center(self):
        rect = self.rect()
        self.setTransformOriginPoint(rect.center())

    def apply_state(self):
        """Reconstrói todo o documento visual com base na Fonte da Verdade."""
        self.text_item.blockSignals(True)
        
        # 1. Limpar sujeiras herdadas e Injetar Conteúdo
        html = re.sub(r"font-family\s*:[^;\"]+;?", "", self.state.html_content)
        html = re.sub(r"font-size\s*:[^;\"]+;?", "", html)
        self.text_item.setHtml(html)
        
        # 2. Aplicar Fonte Global (SEMPRE após o setHtml, pois ele reseta o documento)
        font = QFont(self.state.font_family, self.state.font_size)
        self.text_item.setFont(font)
        self.text_item.document().setDefaultFont(font)
        
        # 3. Aplicar Alinhamento Horizontal
        opt = self.text_item.document().defaultTextOption()
        if self.state.align == "center": opt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif self.state.align == "right": opt.setAlignment(Qt.AlignmentFlag.AlignRight)
        elif self.state.align == "justify": opt.setAlignment(Qt.AlignmentFlag.AlignJustify)
        else: opt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.text_item.document().setDefaultTextOption(opt)
        
        # 4. Aplicar Margens e Entrelinhas
        cursor = QTextCursor(self.text_item.document())
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextBlockFormat()
        fmt.setTextIndent(self.state.indent_px)
        fmt.setLineHeight(self.state.line_height * 100.0, 1)
        cursor.mergeBlockFormat(fmt)
        
        self.text_item.blockSignals(False)
        self.recalculate_text_position()

    def set_vertical_alignment(self, align_str):
        self.state.vertical_align = align_str
        self.apply_state()

    def recalculate_text_position(self):
        self.text_item.setTextWidth(self.rect().width())
        doc_h = self.text_item.document().size().height()
        box_h = self.rect().height()
        
        y = 0
        if self.state.vertical_align == "center":
            y = (box_h - doc_h) / 2
        elif self.state.vertical_align == "bottom":
            y = box_h - doc_h
            
        self.text_item.setPos(0, y)

    def get_placeholders(self):
        text = self.text_item.toPlainText()
        return re.findall(r"\{([a-zA-Z0-9_]+)\}", text)

    def set_alignment(self, align_str):
        self.state.align = align_str
        self.apply_state()

    def set_block_format(self, indent=None, line_height=None):
        if indent is not None: self.state.indent_px = indent
        if line_height is not None: self.state.line_height = line_height
        self.apply_state()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            rect = self.rect()
            w, h = rect.width(), rect.height()
            
            x_candidates = [(new_pos.x(), 0), (new_pos.x() + w/2, w/2), (new_pos.x() + w, w)]
            y_candidates = [(new_pos.y(), 0), (new_pos.y() + h/2, h/2), (new_pos.y() + h, h)]
            
            best_x, best_y = new_pos.x(), new_pos.y()
            min_dist_x, min_dist_y = self.SNAP_DISTANCE, self.SNAP_DISTANCE

            for item in self.scene().items():
                if isinstance(item, Guideline):
                    if item.is_vertical:
                        for (cx, offset) in x_candidates:
                            if abs(cx - item.x()) < min_dist_x:
                                min_dist_x = abs(cx - item.x())
                                best_x = item.x() - offset
                    else:
                        for (cy, offset) in y_candidates:
                            if abs(cy - item.y()) < min_dist_y:
                                min_dist_y = abs(cy - item.y())
                                best_y = item.y() - offset
            return QPointF(best_x, best_y)
        return super().itemChange(change, value)

    def paint(self, painter, option, widget=None):
        if self.isSelected():
            self.setPen(QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine))
            self.setBrush(QBrush(QColor(0, 100, 255, 30)))
        else:
            self.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DotLine))
            self.setBrush(QBrush(QColor(255, 255, 255, 10)))
        super().paint(painter, option, widget)

class SignatureItem(QGraphicsPixmapItem):
    def __init__(self, pixmap_path, parent=None):
        pixmap = QPixmap(pixmap_path)
        super().__init__(pixmap)
        self._original_path = pixmap_path
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._original_pixmap = pixmap
        self.setZValue(50)

    def resize_by_longest_side(self, size_px):
        w = self._original_pixmap.width()
        h = self._original_pixmap.height()
        
        if w > h:
            new_w = size_px
            new_h = (h * size_px) / w
        else:
            new_h = size_px
            new_w = (w * size_px) / h
            
        scaled = self._original_pixmap.scaled(
            new_w, new_h, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)