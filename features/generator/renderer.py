from PySide6.QtGui import (QPainter, QImage, QPixmap, QTextDocument, QFont, 
                           QTextCursor, QTextBlockFormat, QTextCharFormat, QColor, QBrush, QFontMetrics)
from PySide6.QtCore import Qt, QPointF, QRectF
import re
from pathlib import Path

class NativeRenderer:
    def __init__(self, template_data: dict):
        self.tpl = template_data

    def _draw_pixmap_item(self, painter: QPainter, pixmap: QPixmap, x, y, w, h, rotation=0, opacity=1.0) -> QRectF:
        painter.save()
        try:
            painter.setOpacity(opacity)
            if rotation:
                center_x = float(x) + (w / 2)
                center_y = float(y) + (h / 2)
                painter.translate(center_x, center_y)
                painter.rotate(rotation)
                target_rect = QRectF(-w / 2, -h / 2, w, h)
                painter.drawPixmap(target_rect, pixmap, QRectF(pixmap.rect()))
                return painter.transform().mapRect(target_rect)

            target_rect = QRectF(float(x), float(y), w, h)
            painter.drawPixmap(target_rect, pixmap, QRectF(pixmap.rect()))
            return target_rect
        finally:
            painter.restore()


    def render_row(self, row_plain: dict, row_rich: dict, out_path: Path, out_links: list = None):
        
        w = self.tpl["canvas_size"]["w"]
        h = self.tpl["canvas_size"]["h"]
        
        image = QImage(w, h, QImage.Format_ARGB32)
        image.setDotsPerMeterX(3780) # Trava o Gerador em exatos 96 DPI
        image.setDotsPerMeterY(3780)
        image.fill(Qt.GlobalColor.white)

        painter = QPainter(image)
        try:
            self._paint_card(painter, row_rich, out_links)
        finally:
            painter.end()

        image.save(str(out_path), "PNG")

    
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
    

    def render_to_qimage(self, row_plain: dict, row_rich: dict, out_links: list = None) -> QImage:
        
        w = self.tpl["canvas_size"]["w"]
        h = self.tpl["canvas_size"]["h"]
        
        image = QImage(w, h, QImage.Format_ARGB32)
        image.setDotsPerMeterX(3780) # Trava o Gerador em exatos 96 DPI
        image.setDotsPerMeterY(3780)
        image.fill(Qt.GlobalColor.white)

        painter = QPainter(image)
        try:
            self._paint_card(painter, row_rich, out_links)
        finally:
            painter.end()
        return image
    

    def resolve_html(self, html: str, row_rich: dict) -> str:
        def repl(match):
            key = match.group(1)
            return str(row_rich.get(key, ""))
        return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, html)
    

    def _paint_card(self, painter: QPainter, row_rich: dict, out_links: list = None):
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
                bg_props = self.tpl.get("bg_props", {})
                
                w = bg_props.get("w", self.tpl["canvas_size"]["w"])
                h = bg_props.get("h", self.tpl["canvas_size"]["h"])
                x = bg_props.get("x", 0)
                y = bg_props.get("y", 0)
                
                scaled_bg = bg.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                painter.setOpacity(bg_props.get("opacity", 1.0))
                painter.drawPixmap(QPointF(float(x), float(y)), scaled_bg)
                painter.setOpacity(1.0)

        for img in self.tpl.get("images", []):
            if not img.get("visible", True): continue
            
            raw_path = img.get("path", "")
            img_path = Path(raw_path)
            
            # Fallback de resolução de caminho (resolve assets relativos quando acionado via gerador)
            if not img_path.exists():
                # 1. Tenta achar matematicamente pelo nome do modelo (Pareto)
                try:
                    from core.template_manager import slugify_model_name
                    from core.paths import get_models_dir
                    if "name" in self.tpl:
                        alt_path = get_models_dir() / slugify_model_name(self.tpl["name"]) / raw_path
                        if alt_path.exists(): 
                            img_path = alt_path
                except ImportError:
                    pass
                
                # 2. Hack antigo via background (mantido como segurança extra)
                if not img_path.exists() and self.tpl.get("background_path"):
                    bg_path = Path(self.tpl["background_path"])
                    if bg_path.is_absolute():
                        alt_path = bg_path.parent.parent / raw_path
                        if alt_path.exists(): 
                            img_path = alt_path

            if img_path.exists():
                pix = QPixmap(str(img_path))
                w, h = img.get("width", 0), img.get("height", 0)
                
                # Blindagem contra corrompimento de QImage/QPixmap ou dimensões ausentes
                if not pix.isNull() and w > 0 and h > 0:
                    rect = self._draw_pixmap_item(
                        painter,
                        pix,
                        float(img.get("x", 0)),
                        float(img.get("y", 0)),
                        w,
                        h,
                        img.get("rotation", 0),
                        img.get("opacity", 1.0),
                    )

                    if img.get("has_link") and img.get("link_key"):
                        url = row_rich.get(img["link_key"], "").strip()
                        if url and out_links is not None:
                            if not url.startswith(("http://", "https://", "mailto:", "tel:")):
                                url = "https://" + url
                            out_links.append({"url": url, "rect": rect})

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
                painter.setOpacity(box.get("opacity", 1.0))
                self._draw_html_box(painter, box, html_resolved, row_rich, out_links)
                painter.setOpacity(1.0)
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
                if not pix.isNull():
                    self._draw_pixmap_item(
                        painter,
                        pix,
                        float(sig.get("x", 0)),
                        float(sig.get("y", 0)),
                        sig["width"],
                        sig["height"],
                        sig.get("rotation", 0),
                        sig.get("opacity", 1.0),
                    )

    
    def _draw_html_box(self, painter, box_data, html_text, row_rich=None, out_links=None):
        painter.save()
        try:
            doc = QTextDocument()
            doc.setDocumentMargin(0) 
            
            # Limpeza Retroativa
            clean_html = re.sub(r"color\s*:[^;\"]+;?", "", html_text)
            clean_html = re.sub(r"background-color\s*:[^;\"]+;?", "", clean_html)
            clean_html = re.sub(r"text-decoration\s*:[^;\"]+;?", "", clean_html)
            clean_html = re.sub(r"font-size\s*:[^;\"]+;?", "", clean_html)
            clean_html = re.sub(r"font-family\s*:[^;\"]+;?", "", clean_html)
            clean_html = re.sub(r"(?i)<a\b[^>]*>", "", clean_html)
            clean_html = re.sub(r"(?i)</a>", "", clean_html)
            
            doc.setHtml(clean_html)

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
            
            cursor = QTextCursor(doc)
            cursor.select(QTextCursor.SelectionType.Document)
            fmt = QTextBlockFormat()
            fmt.setTextIndent(box_data.get("indent_px", 0.0))
            fmt.setLineHeight(box_data.get("line_height", 1.15) * 100.0, 1)
            cursor.mergeBlockFormat(fmt)

            root_frame = doc.rootFrame()
            frame_fmt = root_frame.frameFormat()
            frame_fmt.setMargin(0)
            root_frame.setFrameFormat(frame_fmt)
            
            w = box_data.get("w", 300)
            h = box_data.get("h", 100)
            rotation = box_data.get("rotation", 0)
            doc.setTextWidth(w)
                    
            layout = doc.documentLayout()
            logical_h = layout.documentSize().height()
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
                        tight_rect = fm.tightBoundingRect("AÇgjpqy|{}")
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
                        tight_rect = fm.tightBoundingRect("AÇgjpqy|{}")
                        block_y = layout.blockBoundingRect(last_valid_block).y()
                        real_bottom = block_y + last_line.y() + last_line.ascent() + tight_rect.bottom()
                        
            content_h = real_bottom - real_top
            
            y_offset = 0
            if box_data.get("vertical_align") == "center":
                y_offset = (h - content_h) / 2 - real_top
            elif box_data.get("vertical_align") == "bottom":
                y_offset = h - content_h - real_top
            else: 
                y_offset = -real_top

            center_x = box_data.get("x", 0) + (w / 2)
            center_y = box_data.get("y", 0) + (h / 2)
            
            painter.translate(center_x, center_y)
            painter.rotate(rotation)
            painter.translate(-w / 2, -h / 2)
            
            painter.setClipRect(0, -10000, w, 20000)
            painter.translate(0, y_offset)
            doc.drawContents(painter)
            
            # Mapeamento do Hiperlink isolado
            if box_data.get("has_link") and box_data.get("link_key") and row_rich and out_links is not None:
                url = row_rich.get(box_data["link_key"], "").strip()
                if url:
                    if not url.startswith(("http://", "https://", "mailto:", "tel:")):
                        url = "https://" + url
                    ideal_w = min(doc.idealWidth(), w)
                    # Calcula x_start baseado no alinhamento horizontal
                    if align_str == "center":
                        x_start = (w - ideal_w) / 2
                    elif align_str == "right":
                        x_start = w - ideal_w
                    else:
                        x_start = 0
                    # real_top é o topo da tinta no espaço local do doc (antes do y_offset)
                    # y_offset desloca o doc inteiro; o topo real no espaço da caixa é real_top + y_offset
                    local_rect = QRectF(x_start, real_top, ideal_w, content_h)
                    mapped_rect = painter.transform().mapRect(local_rect)
                    out_links.append({"url": url, "rect": mapped_rect})

        except Exception as e:
            print(f"[WARN] Falha interna no layout do texto: {e}")
        finally:
            # ESTA LINHA É A CURA DO EFEITO CASCATA. Sempre será executada!
            painter.restore()
