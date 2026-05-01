from PySide6.QtGui import QImage, QPainter, QColor, QPen, QPixmap, QPageLayout
from PySide6.QtCore import Qt, QPointF

DPI = 300

def mm_to_px_300(mm):
    return int((mm * DPI) / 25.4)

class SheetAssembler:
    def __init__(self, target_w_mm: float, target_h_mm: float, sheet_w_mm: float = 210.0, sheet_h_mm: float = 297.0, crop_marks: bool = True, bleed_margin: bool = False):
        self.target_w_mm = target_w_mm
        self.target_h_mm = target_h_mm
        self.crop_marks = crop_marks
        self.bleed_margin = bleed_margin
        
        # Configuração das linhas de corte e seus tamanhos
        if self.crop_marks:
            self.mark_gap_mm = 2.0  
            self.mark_len_mm = 3.0  
        else:
            self.mark_gap_mm = 0.0
            self.mark_len_mm = 0.0

        # Cálculo cumulativo da reserva de borda (reduz a área útil da folha)
        self.edge_reserve_mm = 0.0
        
        if self.bleed_margin:
            self.edge_reserve_mm += 5.0 # Adiciona 5mm de proteção
            
        if self.crop_marks:
            self.edge_reserve_mm += (self.mark_gap_mm + self.mark_len_mm) # Adiciona 5mm para as marcas

        self.card_w_px = mm_to_px_300(target_w_mm)
        self.card_h_px = mm_to_px_300(target_h_mm)
        self.mark_len = mm_to_px_300(self.mark_len_mm)
        self.mark_gap = mm_to_px_300(self.mark_gap_mm)
        
        full_sheet_w_px = mm_to_px_300(sheet_w_mm)
        full_sheet_h_px = mm_to_px_300(sheet_h_mm)
        reserve_px = mm_to_px_300(self.edge_reserve_mm * 2) 
        
        usable_w_px = full_sheet_w_px - reserve_px
        usable_h_px = full_sheet_h_px - reserve_px

        cols_p = max(0, usable_w_px // self.card_w_px)
        rows_p = max(0, usable_h_px // self.card_h_px)
        cap_p = cols_p * rows_p
        
        cols_l = usable_h_px // self.card_w_px
        rows_l = usable_w_px // self.card_h_px
        cap_l = cols_l * rows_l
        
        if cap_l > cap_p:
            self.sheet_w = full_sheet_h_px  
            self.sheet_h = full_sheet_w_px
            self.cols = cols_l
            self.rows = rows_l
            self.capacity = cap_l
            self.orientation = QPageLayout.Orientation.Landscape
        else:
            self.sheet_w = full_sheet_w_px
            self.sheet_h = full_sheet_h_px
            self.cols = cols_p
            self.rows = rows_p
            self.capacity = cap_p
            self.orientation = QPageLayout.Orientation.Portrait
            self.sheet_w = full_sheet_w_px
            self.sheet_h = full_sheet_h_px
            self.cols = cols_p
            self.rows = rows_p
            self.capacity = cap_p

        total_grid_w = self.cols * self.card_w_px
        total_grid_h = self.rows * self.card_h_px
        
        self.margin_left = (self.sheet_w - total_grid_w) // 2
        self.margin_top = (self.sheet_h - total_grid_h) // 2

    def render_sheet(self, cards: list[QImage]) -> QImage:
        sheet = QImage(self.sheet_w, self.sheet_h, QImage.Format_ARGB32)
        sheet.fill(Qt.GlobalColor.white)
        
        painter = QPainter(sheet)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        idx = 0
        limit = len(cards)
        
        if limit == 0:
            painter.end()
            return sheet

        # Calcula a malha efetivamente ocupada nesta folha
        actual_cols = min(self.cols, limit)
        actual_rows = (limit + self.cols - 1) // self.cols
        
        for r in range(self.rows):
            for c in range(self.cols):
                if idx >= limit:
                    break
                original_img = cards[idx]
                # A margem continua sendo a estática (baseada na grade máxima)
                x = self.margin_left + (c * self.card_w_px)
                y = self.margin_top + (r * self.card_h_px)
                
                scaled_pix = QPixmap.fromImage(original_img).scaled(
                    self.card_w_px, self.card_h_px,
                    Qt.AspectRatioMode.IgnoreAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                painter.drawPixmap(x, y, scaled_pix)
                idx += 1

        if self.crop_marks:
            self._draw_crop_marks(painter, actual_cols, actual_rows)
        painter.end()
        return sheet

    def _draw_crop_marks(self, painter: QPainter, cols: int, rows: int):
        pen = QPen(Qt.GlobalColor.black)
        pen.setWidth(2) 
        painter.setPen(pen)

        grid_start_x = self.margin_left
        # Usa as colunas e linhas dinâmicas para travar o fim do bloco
        grid_end_x = self.margin_left + (cols * self.card_w_px)
        grid_start_y = self.margin_top
        grid_end_y = self.margin_top + (rows * self.card_h_px)

        for c in range(cols + 1):
            x = grid_start_x + (c * self.card_w_px)
            p1_top = QPointF(x, grid_start_y - self.mark_gap)
            p2_top = QPointF(x, grid_start_y - self.mark_gap - self.mark_len)
            painter.drawLine(p1_top, p2_top)
            
            p1_btm = QPointF(x, grid_end_y + self.mark_gap)
            p2_btm = QPointF(x, grid_end_y + self.mark_gap + self.mark_len)
            painter.drawLine(p1_btm, p2_btm)

        for r in range(rows + 1):
            y = grid_start_y + (r * self.card_h_px)
            p1_lft = QPointF(grid_start_x - self.mark_gap, y)
            p2_lft = QPointF(grid_start_x - self.mark_gap - self.mark_len, y)
            painter.drawLine(p1_lft, p2_lft)
            
            p1_rgt = QPointF(grid_end_x + self.mark_gap, y)
            p2_rgt = QPointF(grid_end_x + self.mark_gap + self.mark_len, y)
            painter.drawLine(p1_rgt, p2_rgt)