from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
import traceback
from PySide6.QtGui import QPainter, QPdfWriter, QPageLayout, QPageSize
from PySide6.QtCore import QMarginsF

# Imports relativos do novo domínio
from .imposition import SheetAssembler

class PageRenderWorker(QThread):
    page_finished = Signal(int, str, str) 
    error_occurred = Signal(str)

    def __init__(self, tasks, renderer, output_dir, imposition_settings, export_format="PNG"):
        super().__init__()
        self.tasks = tasks
        self.renderer = renderer
        self.output_dir = output_dir
        self.export_format = export_format
        
        w_mm = imposition_settings.get("target_w_mm", 100)
        h_mm = imposition_settings.get("target_h_mm", 150)
        self.assembler = SheetAssembler(w_mm, h_mm)
        
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            for page_task in self.tasks:
                if not self._is_running: break

                page_num = page_task["page_num"]
                cards_data = page_task["cards"]
                
                card_images = []
                for (r_plain, r_rich, fname) in cards_data:
                    img = self.renderer.render_to_qimage(r_plain, r_rich)
                    card_images.append(img)
                
                sheet_img = self.assembler.render_sheet(card_images)
                out_name = page_task["output_filename"]
                out_path = self.output_dir / out_name
                
                if self.export_format == "PDF":
                    out_path = out_path.with_suffix(".pdf")
                    writer = QPdfWriter(str(out_path))
                    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                    # Define orientação baseada no assembler
                    layout = writer.pageLayout()
                    if self.assembler.sheet_w > self.assembler.sheet_h:
                        layout.setOrientation(QPageLayout.Orientation.Landscape)
                    else:
                        layout.setOrientation(QPageLayout.Orientation.Portrait)
                    layout.setMargins(QMarginsF(0, 0, 0, 0))
                    writer.setPageLayout(layout)
                    
                    painter = QPainter(writer)
                    painter.drawImage(layout.paintRectPixels(writer.resolution()), sheet_img)
                    painter.end()
                else:
                    sheet_img.save(str(out_path))
                
                msg = f"🖨️  FOLHA {page_num:02d} OK ({len(card_images)} itens)"
                # Garante que o nome enviado ao log de arquivos gerados tenha a extensão correta
                final_name = out_path.name
                self.page_finished.emit(len(card_images), final_name, msg)
                
                card_images.clear()
                del sheet_img

        except Exception as e:
            self.error_occurred.emit(f"Erro no Worker: {str(e)}\n{traceback.format_exc()}")


class DirectRenderWorker(QThread):
    card_finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, chunk_data, renderer, output_dir, export_format="PNG"):
        super().__init__()
        self.chunk_data = chunk_data
        self.renderer = renderer
        self.output_dir = output_dir
        self.export_format = export_format
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            for (row_plain, row_rich, filename) in self.chunk_data:
                if not self._is_running: break
                
                if self.export_format == "PDF":
                    out_path = self.output_dir / f"{filename}.pdf"
                    img = self.renderer.render_to_qimage(row_plain, row_rich)
                    
                    # Converte dimensões de px (96dpi) para mm para o PDF
                    w_mm = (img.width() * 25.4) / 96.0
                    h_mm = (img.height() * 25.4) / 96.0
                    
                    writer = QPdfWriter(str(out_path))
                    writer.setPageSize(QPageSize(QPageSize.Custom))
                    # Define o tamanho da página exatamente igual ao do cartão
                    from PySide6.QtCore import QSizeF
                    layout = writer.pageLayout()
                    layout.setPageSize(QPageSize(QSizeF(w_mm, h_mm), QPageSize.Unit.Millimeter))
                    layout.setMargins(QMarginsF(0, 0, 0, 0))
                    writer.setPageLayout(layout)
                    
                    painter = QPainter(writer)
                    painter.drawImage(layout.paintRectPixels(writer.resolution()), img)
                    painter.end()
                else:
                    out_path = self.output_dir / f"{filename}.png"
                    self.renderer.render_row(row_plain, row_rich, out_path)
                
                # Refinamento: Emite o nome real do arquivo gerado para o log
                self.card_finished.emit(out_path.name)
        except Exception as e:
            self.error_occurred.emit(str(e))