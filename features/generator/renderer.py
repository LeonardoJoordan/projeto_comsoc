from PySide6.QtGui import (QPainter, QImage, QPixmap, QTextDocument, QFont, 
                           QTextCursor, QTextBlockFormat, QTextCharFormat, QColor, QBrush, QFontMetrics)
from PySide6.QtCore import Qt, QPointF
import re
from pathlib import Path

class NativeRenderer:
    def __init__(self, template_data: dict):
        self.tpl = template_data

    def render_to_pixmap(self, row_rich: dict = None) -> QPixmap:
        w = self.tpl["canvas_size"]["w"]
        h = self.tpl["canvas_size"]["h"]
        
        image = QImage(w, h, QImage.Format_ARGB32)
        image.setDotsPerMeterX(3780) # Trava o Gerador em exatos 96 DPI
        image.setDotsPerMeterY(3780)
        image.fill(Qt.GlobalColor.white)

        painter = QPainter(image)
        try:
            if row_rich is None:
                placeholders = self.tpl.get("placeholders", [])
                row_rich = {p: f"{{{p}}}" for p in placeholders}
            self._paint_card(painter, row_rich)
        finally:
            painter.end()
        
        return QPixmap.fromImage(image)

    def render_row(self, row_plain: dict, row_rich: dict, out_path: Path):
        w = self.tpl["canvas_size"]["w"]
        h = self.tpl["canvas_size"]["h"]
        
        image = QImage(w, h, QImage.Format_ARGB32)
        image.setDotsPerMeterX(3780) # Trava o Gerador em exatos 96 DPI
        image.setDotsPerMeterY(3780)
        image.fill(Qt.GlobalColor.white)

        painter = QPainter(image)
        try:
            self._paint_card(painter, row_rich)
        finally:
            painter.end()

        image.save(str(out_path), "PNG")

    def render_to_qimage(self, row_plain: dict, row_rich: dict) -> QImage:
        w = self.tpl["canvas_size"]["w"]
        h = self.tpl["canvas_size"]["h"]
        
        image = QImage(w, h, QImage.Format_ARGB32)
        image.setDotsPerMeterX(3780) # Trava o Gerador em exatos 96 DPI
        image.setDotsPerMeterY(3780)
        image.fill(Qt.GlobalColor.white)

        painter = QPainter(image)
        try:
            self._paint_card(painter, row_rich)
        finally:
            painter.end()
        return image

    def _paint_card(self, painter: QPainter, row_rich: dict):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # Criamos uma fonte base com estratégia de outline para evitar o "hinting" (ajuste de pixel da tela)
        # Isso garante que o glifo seja desenhado exatamente onde as coordenadas flutuantes mandam.
        base_font = QFont()
        base_font.setStyleStrategy(QFont.StyleStrategy.ForceOutline)
        painter.setFont(base_font)

        if self.tpl.get("background_path"):
            bg = QPixmap(self.tpl["background_path"])
            if not bg.isNull():
                painter.drawPixmap(0, 0, bg)

        for img in self.tpl.get("images", []):
            if not img.get("visible", True): continue
            
            raw_path = img.get("path", "")
            img_path = Path(raw_path)
            
            # Fallback de resolução de caminho (resolve assets relativos quando acionado via gerador)
            if not img_path.exists() and self.tpl.get("background_path"):
                bg_path = Path(self.tpl["background_path"])
                if bg_path.is_absolute():
                    alt_path = bg_path.parent.parent / raw_path
                    if alt_path.exists(): img_path = alt_path

            if img_path.exists():
                pix = QPixmap(str(img_path))
                w, h = img.get("width", 0), img.get("height", 0)
                
                # Blindagem contra corrompimento de QImage/QPixmap ou dimensões ausentes
                if not pix.isNull() and w > 0 and h > 0:
                    scaled = pix.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    painter.drawPixmap(QPointF(float(img.get("x", 0)), float(img.get("y", 0))), scaled)

        for box in self.tpl.get("boxes", []):
            if not box.get("visible", True):
                continue
            needed_vars = re.findall(r"\{([a-zA-Z0-9_]+)\}", box["html"])
            should_skip = False
            for var in needed_vars:
                val = row_rich.get(var, "")
                clean_val = re.sub(r"<[^>]+>", "", str(val)).strip()
                if not clean_val:
                    should_skip = True
                    break
            
            if should_skip:
                continue
            try:
                html_resolved = self.resolve_html(box["html"], row_rich)
                self._draw_html_box(painter, box, html_resolved)
            except Exception as e:
                print(f"[WARN] Erro ao desenhar caixa de texto: {e}")
                continue

        for sig in self.tpl.get("signatures", []):
            # A decisão da tabela sobrepõe a do JSON. Se não houver info na tabela, usa o JSON.
            show_sig = row_rich.get("__use_signature__")
            
            if show_sig is None:
                show_sig = sig.get("visible", True)
                
            if not show_sig:
                continue

            if Path(sig["path"]).exists():
                pix = QPixmap(sig["path"])
                scaled = pix.scaled(sig["width"], sig["height"], 
                                   Qt.AspectRatioMode.IgnoreAspectRatio, 
                                   Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(QPointF(float(sig.get("x", 0)), float(sig.get("y", 0))), scaled)

    def resolve_html(self, html: str, row_rich: dict) -> str:
        def repl(match):
            key = match.group(1)
            return str(row_rich.get(key, ""))
        return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, html)

    def _draw_html_box(self, painter, box_data, html_text):
        painter.save()
        doc = QTextDocument()
        doc.setDocumentMargin(0) 
        
        # 0. Limpeza Retroativa: Remove cores e links para que o gerador não imprima azul
        clean_html = re.sub(r"color\s*:[^;\"]+;?", "", html_text)
        clean_html = re.sub(r"background-color\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"text-decoration\s*:[^;\"]+;?", "", clean_html)
        clean_html = re.sub(r"(?i)<a\b[^>]*>", "", clean_html)
        clean_html = re.sub(r"(?i)</a>", "", clean_html)
        
        # 1. Injetar o HTML limpo
        doc.setHtml(clean_html)

        # 2. Aplicar a mesma Fonte Global nativa usada no DesignerBox
        font_family = box_data.get("font_family", "Arial")
        font_size = box_data.get("font_size", 16)
        font = QFont(font_family, font_size)
        doc.setDefaultFont(font)
        
        font_color = box_data.get("font_color", "#000000")
        
        cursor_color = QTextCursor(doc)
        cursor_color.select(QTextCursor.SelectionType.Document)
        char_fmt = QTextCharFormat()
        char_fmt.setForeground(QBrush(QColor(font_color)))
        cursor_color.mergeCharFormat(char_fmt)

        # 3. Aplicar Alinhamento Horizontal
        align_str = box_data.get("align", "left")
        opts = doc.defaultTextOption()
        if align_str == "center":
            opts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif align_str == "right":
            opts.setAlignment(Qt.AlignmentFlag.AlignRight)
        elif align_str == "justify":
            opts.setAlignment(Qt.AlignmentFlag.AlignJustify)
        else:
            opts.setAlignment(Qt.AlignmentFlag.AlignLeft)
        doc.setDefaultTextOption(opts)
        
        # 4. Clonar as exatas propriedades de Margem e Entrelinha do Editor
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextBlockFormat()
        fmt.setTextIndent(box_data.get("indent_px", 0.0))
        fmt.setLineHeight(box_data.get("line_height", 1.15) * 100.0, 1) # '1' = ProportionalHeight
        cursor.mergeBlockFormat(fmt)

        # 5. Salvar os caracteres com descender (p, g, ç) injetando margem apenas na base do rootFrame
        fm = QFontMetrics(font)
        root_frame = doc.rootFrame()
        frame_fmt = root_frame.frameFormat()
        frame_fmt.setBottomMargin(fm.descent())
        root_frame.setFrameFormat(frame_fmt)
        
        w = box_data.get("w", 300)
        h = box_data.get("h", 100)
        rotation = box_data.get("rotation", 0)
        doc.setTextWidth(w)
                
        # Força o recálculo do layout para obter a altura real do conteúdo
        layout = doc.documentLayout()
        content_h = layout.documentSize().height()
        
        y_offset = 0
        if box_data.get("vertical_align") == "center":
            y_offset = max(0, (h - content_h) / 2)
        elif box_data.get("vertical_align") == "bottom":
            y_offset = max(0, h - content_h)

        center_x = box_data.get("x", 0) + (w / 2)
        center_y = box_data.get("y", 0) + (h / 2)
        
        painter.translate(center_x, center_y)
        painter.rotate(rotation)
        painter.translate(-w / 2, -h / 2)
        
        painter.setClipRect(0, 0, w, h)
        painter.translate(0, y_offset)
        doc.drawContents(painter)
        painter.restore()