import re
from pathlib import Path
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsRectItem, QGraphicsTextItem,
                               QGraphicsItem, QInputDialog, QLineEdit, QGraphicsPixmapItem)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (QPen, QBrush, QColor, QFont, QTextCursor,
                           QTextBlockFormat, QPixmap, QPainterPathStroker, QTextCharFormat,
                           QImageReader, QPainterPath, QFontMetrics)
from core.text_state import TextState

DPI = 300

def mm_to_px(mm):
    return (mm * DPI) / 25.4

def px_to_mm(px):
    return (px * 25.4) / DPI


class ResizeHandle(QGraphicsRectItem):
    def __init__(self, parent):
        super().__init__(-6, -6, 12, 12, parent)
        self.setBrush(QBrush(QColor("#27ae60")))
        self.setPen(QPen(Qt.GlobalColor.white, 2))
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self._is_resizing = False
        self.initial_ratio = 1.0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = True
            parent = self.parentItem()
            if hasattr(parent, 'rect'):
                r = parent.rect()
            else:
                r = parent.pixmap().rect()
            self.initial_ratio = r.width() / r.height() if r.height() > 0 else 1.0
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_resizing:
            parent = self.parentItem()
            if parent:
                parent_pos = self.mapToParent(event.pos())
                new_w = max(40, parent_pos.x())
                new_h = max(30, parent_pos.y())
                
                # A mágica da proporção travada acontece aqui:
                if getattr(parent, 'keep_proportion', True):
                    new_h = new_w / self.initial_ratio
                
                if hasattr(parent, 'resize_from_handle'):
                    parent.resize_from_handle(new_w, new_h)
                
                if parent.scene():
                    parent.scene().update() 
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        super().mouseReleaseEvent(event)


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


class ImageItem(QGraphicsPixmapItem):
    SNAP_DISTANCE = 15

    def __init__(self, pixmap_path, parent=None):
        reader = QImageReader(pixmap_path)
        reader.setAutoTransform(True)
        size = reader.size()        
        img = reader.read()
        pixmap = QPixmap.fromImage(img) if not img.isNull() else QPixmap(pixmap_path)
        
        super().__init__(pixmap)
        self._original_path = pixmap_path
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._original_pixmap = pixmap
        self.setZValue(1) 
        
        self.keep_proportion = True
        self.handle_br = ResizeHandle(self)
        rect = self.pixmap().rect()
        self.handle_br.setPos(rect.width(), rect.height())
        self.handle_br.hide()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if hasattr(self, 'handle_br'):
                if self.isSelected() and (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable):
                    self.handle_br.show()
                else:
                    self.handle_br.hide()

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            rect = self.pixmap().rect()
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
        if hasattr(self, 'handle_br'):
            self.handle_br.setPos(new_w, new_h)

    def resize_custom(self, w, h):
        if w <= 0 or h <= 0: return
        scaled = self._original_pixmap.scaled(
            w, h, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        if hasattr(self, 'handle_br'):
            self.handle_br.setPos(w, h)

    def resize_from_handle(self, w, h):
        self.resize_custom(w, h)

class BackgroundItem(ImageItem):
    """
    Herdando de ImageItem, o fundo atua como um PowerClip (Máscara de Corte).
    Ele ganha alças de redimensionamento e vira uma camada livre (Z-Value -100), 
    mas é renderizado estritamente dentro da área da prancheta.
    """
    def __init__(self, pixmap_path, parent=None):
        super().__init__(pixmap_path, parent)
        self.setZValue(-100)

    def paint(self, painter, option, widget=None):
        """MÁGICA VISUAL: Corta a pintura da imagem nas bordas exatas do documento."""
        if self.scene():
            path = QPainterPath()
            path.addRect(self.scene().sceneRect())
            local_path = self.mapFromScene(path) # Traduz as coordenadas do documento para as da imagem
            
            # Aplica a máscara (PowerClip)
            painter.setClipPath(local_path)
            
        super().paint(painter, option, widget)

    def shape(self):
        """MÁGICA DE UX: Impede que o usuário selecione a parte invisível da imagem clicando no nada."""
        base_shape = super().shape()
        if self.scene():
            path = QPainterPath()
            path.addRect(self.scene().sceneRect())
            local_path = self.mapFromScene(path)
            
            # O formato "clicável" é apenas a interseção entre o tamanho real da imagem e o tamanho do documento
            return base_shape.intersected(local_path)
            
        return base_shape
    
class SignatureItem(QGraphicsPixmapItem):
    SNAP_DISTANCE = 15

    def __init__(self, pixmap_path, parent=None):
        reader = QImageReader(pixmap_path)
        reader.setAutoTransform(True) # Lê metadados EXIF e rotaciona corretamente
        size = reader.size()        
        img = reader.read()
        pixmap = QPixmap.fromImage(img) if not img.isNull() else QPixmap(pixmap_path)
        
        super().__init__(pixmap)
        self._original_path = pixmap_path
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._original_pixmap = pixmap
        self.setZValue(201)
        
        self.keep_proportion = True
        self.handle_br = ResizeHandle(self)
        rect = self.pixmap().rect()
        self.handle_br.setPos(rect.width(), rect.height())
        self.handle_br.hide()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if hasattr(self, 'handle_br'):
                if self.isSelected() and (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable):
                    self.handle_br.show()
                else:
                    self.handle_br.hide()

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            rect = self.pixmap().rect()
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
        if hasattr(self, 'handle_br'):
            self.handle_br.setPos(new_w, new_h)

    def resize_custom(self, w, h):
        if w <= 0 or h <= 0: return
        scaled = self._original_pixmap.scaled(
            w, h, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        if hasattr(self, 'handle_br'):
            self.handle_br.setPos(w, h)

    def resize_from_handle(self, w, h):
        self.resize_custom(w, h)


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
        self.setZValue(101)

        self.state = TextState(html_content=text)
        
        self.text_item = QGraphicsTextItem("", self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.black)
        
        # CORREÇÃO CRÍTICA: Zera a margem fantasma nativa do Editor para equiparar ao Gerador
        self.text_item.document().setDocumentMargin(0)
        
        self.text_item.document().contentsChanged.connect(self.recalculate_text_position)

        self.text_item.setTextWidth(w)
        self.text_item.setPos(0, 0)
        
        self.apply_state()
        self.update_center()
        
        # --- Instanciar Alça de Redimensionamento ---
        self.keep_proportion = True
        self.handle_br = ResizeHandle(self)
        self.handle_br.setPos(w, h)
        self.handle_br.hide()

    def setRect(self, *args):
        super().setRect(*args)
        if hasattr(self, 'handle_br'):
            r = self.rect()
            self.handle_br.setPos(r.width(), r.height())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if hasattr(self, 'handle_br'):
                if self.isSelected() and (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable):
                    self.handle_br.show()
                else:
                    self.handle_br.hide()

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

    
    def resize_from_handle(self, w, h):
        self.setRect(0, 0, w, h)
        self.recalculate_text_position()
        self.update_center()
    
    def set_alignment(self, align_str):
        self.state.align = align_str
        self.apply_state()

    def set_vertical_alignment(self, align_str):
        self.state.vertical_align = align_str
        self.apply_state()

    def set_block_format(self, indent=None, line_height=None):
        if indent is not None: self.state.indent_px = indent
        if line_height is not None: self.state.line_height = line_height
        self.apply_state()

    def get_placeholders(self):
        text = self.text_item.toPlainText()
        return re.findall(r"\{([a-zA-Z0-9_]+)\}", text)
    

    def apply_state(self):
        """Reconstrói todo o documento visual com base na Fonte da Verdade."""
        self.text_item.blockSignals(True)
        
        # 1. Limpeza Retroativa e Injeção de Conteúdo (conserta JSONs antigos já infectados)
        html = re.sub(r"font-family\s*:[^;\"]+;?", "", self.state.html_content)
        html = re.sub(r"font-size\s*:[^;\"]+;?", "", html)
        html = re.sub(r"color\s*:[^;\"]+;?", "", html)
        html = re.sub(r"background-color\s*:[^;\"]+;?", "", html)
        html = re.sub(r"text-decoration\s*:[^;\"]+;?", "", html)
        html = re.sub(r"(?i)<a\b[^>]*>", "", html)
        html = re.sub(r"(?i)</a>", "", html)
        html = re.sub(r"(?i)<h[1-6]([^>]*)>", r"<p\1>", html)
        html = re.sub(r"(?i)</h[1-6]>", "</p>", html)
        
        self.text_item.setHtml(html)
        
        # 2. Aplicar Fonte Global e Cor NATIVA (SEMPRE após o setHtml, pois ele reseta o documento)
        font = QFont(self.state.font_family, self.state.font_size)
        font.setStyleStrategy(QFont.StyleStrategy.ForceOutline)
        self.text_item.setFont(font)
        self.text_item.document().setDefaultFont(font)
        
        color = QColor(getattr(self.state, 'font_color', '#000000'))
        
        cursor_color = QTextCursor(self.text_item.document())
        cursor_color.select(QTextCursor.SelectionType.Document)
        char_fmt = QTextCharFormat()
        char_fmt.setForeground(QBrush(color))
        cursor_color.mergeCharFormat(char_fmt)
        
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

        # 5. Zerar margens para sistema de ancoragem livre
        root_frame = self.text_item.document().rootFrame()
        frame_fmt = root_frame.frameFormat()
        frame_fmt.setMargin(0)
        root_frame.setFrameFormat(frame_fmt)
        
        self.text_item.blockSignals(False)
        self.recalculate_text_position()

    def recalculate_text_position(self):
        self.text_item.setTextWidth(self.rect().width())
        doc = self.text_item.document()
        layout = doc.documentLayout()
        logical_h = layout.documentSize().height()
        box_h = self.rect().height()
        
        # --- CÁLCULO DA TINTA REAL (Ignorando Ascender/Descender invisível) ---
        font = self.text_item.font()
        fm = QFontMetrics(font)
        real_top = 0
        real_bottom = logical_h
        
        first_block = doc.begin()
        if first_block.isValid():
            text_layout = first_block.layout()
            if text_layout.lineCount() > 0:
                first_line = text_layout.lineAt(0)
                text_str = first_block.text()[first_line.textStart() : first_line.textStart() + first_line.textLength()]
                if text_str.strip():
                    tight_rect = fm.tightBoundingRect(text_str)
                    real_top = first_line.y() + first_line.ascent() + tight_rect.top()

        last_block = doc.begin()
        last_valid_block = last_block
        while last_block.isValid():
            if last_block.text().strip(): last_valid_block = last_block
            last_block = last_block.next()
            
        if last_valid_block.isValid():
            text_layout = last_valid_block.layout()
            if text_layout.lineCount() > 0:
                last_line = text_layout.lineAt(text_layout.lineCount() - 1)
                text_str = last_valid_block.text()[last_line.textStart() : last_line.textStart() + last_line.textLength()]
                if text_str.strip():
                    tight_rect = fm.tightBoundingRect(text_str)
                    block_y = layout.blockBoundingRect(last_valid_block).y()
                    real_bottom = block_y + last_line.y() + last_line.ascent() + tight_rect.bottom()
                    
        content_h = real_bottom - real_top
        
        y = 0
        if self.state.vertical_align == "center":
            y = (box_h - content_h) / 2 - real_top
        elif self.state.vertical_align == "bottom":
            y = box_h - content_h - real_top
        else: # Top
            y = -real_top
            
        self.text_item.setPos(0, y)

    def update_center(self):
        rect = self.rect()
        self.setTransformOriginPoint(rect.center())