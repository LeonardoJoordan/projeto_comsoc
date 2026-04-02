from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
import traceback

# Imports relativos do novo domínio
from .imposition import SheetAssembler

class PageRenderWorker(QThread):
    page_finished = Signal(int, str, str) 
    error_occurred = Signal(str)

    def __init__(self, tasks, renderer, output_dir, imposition_settings):
        super().__init__()
        self.tasks = tasks
        self.renderer = renderer
        self.output_dir = output_dir
        
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
                
                sheet_img.save(str(out_path))
                
                msg = f"🖨️  FOLHA {page_num:02d} OK ({len(card_images)} itens)"
                self.page_finished.emit(len(card_images), out_name, msg)
                
                card_images.clear()
                del sheet_img

        except Exception as e:
            self.error_occurred.emit(f"Erro no Worker: {str(e)}\n{traceback.format_exc()}")


class DirectRenderWorker(QThread):
    card_finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, chunk_data, renderer, output_dir):
        super().__init__()
        self.chunk_data = chunk_data
        self.renderer = renderer
        self.output_dir = output_dir
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            for (row_plain, row_rich, filename) in self.chunk_data:
                if not self._is_running: break
                
                out_path = self.output_dir / f"{filename}.png"
                self.renderer.render_row(row_plain, row_rich, out_path)
                self.card_finished.emit(f"{filename}.png")
        except Exception as e:
            self.error_occurred.emit(str(e))