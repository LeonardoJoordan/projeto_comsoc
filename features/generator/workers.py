import traceback
import shutil
import fitz 
from PySide6.QtCore import QThread, Signal, QSizeF, QMarginsF
from PySide6.QtGui import QImage, QPainter, QPdfWriter, QPageLayout, QPageSize

from .imposition import SheetAssembler


class DirectRenderWorker(QThread):
    card_finished = Signal(str, int, list)
    error_occurred = Signal(str)

    def __init__(self, chunk_data, renderer, output_dir, export_format="PNG", single_pdf=False, target_w_mm=100.0, target_h_mm=150.0):
        super().__init__()
        self.chunk_data = chunk_data
        self.renderer = renderer
        self.output_dir = output_dir
        self.export_format = export_format
        self.single_pdf = single_pdf
        self.target_w_mm = target_w_mm
        self.target_h_mm = target_h_mm
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            writer = None
            painter = None
            layout = None
            out_path_single = self.output_dir / f"{self.output_dir.name}_Completo.pdf"

            if self.single_pdf and self.export_format == "PDF":
                writer = QPdfWriter(str(out_path_single))
                writer.setPageSize(QPageSize(QPageSize.PageSizeId.Custom))
                layout = writer.pageLayout()
                layout.setPageSize(QPageSize(QSizeF(self.target_w_mm, self.target_h_mm), QPageSize.Unit.Millimeter))
                layout.setMargins(QMarginsF(0, 0, 0, 0))
                writer.setPageLayout(layout)
                painter = QPainter(writer)

            for i, (original_idx, row_plain, row_rich, filename) in enumerate(self.chunk_data):
                if not self._is_running: break
                
                local_links = []
                
                if self.export_format == "PDF":
                    img = self.renderer.render_to_qimage(row_plain, row_rich, out_links=local_links)
                    if self.single_pdf:
                        if i > 0:
                            writer.newPage()
                        painter.drawImage(layout.paintRectPixels(writer.resolution()), img)
                        self.card_finished.emit(out_path_single.name, original_idx, local_links)
                    else:
                        out_path = self.output_dir / f"{filename}.pdf"
                        writer_single = QPdfWriter(str(out_path))
                        writer_single.setPageSize(QPageSize(QPageSize.PageSizeId.Custom))
                        layout_single = writer_single.pageLayout()
                        layout_single.setPageSize(QPageSize(QSizeF(self.target_w_mm, self.target_h_mm), QPageSize.Unit.Millimeter))
                        layout_single.setMargins(QMarginsF(0, 0, 0, 0))
                        writer_single.setPageLayout(layout_single)
                        painter_single = QPainter(writer_single)
                        painter_single.drawImage(layout_single.paintRectPixels(writer_single.resolution()), img)
                        painter_single.end()
                        
                        del painter_single
                        del layout_single
                        del writer_single
                        
                        # --- PÓS-PROCESSAMENTO: Injeção de Hiperlinks ---
                        if local_links and not self.single_pdf:
                            try:
                                pdf_doc = fitz.open(str(out_path))
                                page = pdf_doc[0]
                                
                                page_rect = page.rect
                                canvas_w = self.renderer.tpl.get("canvas_size", {}).get("w", 1000)
                                canvas_h = self.renderer.tpl.get("canvas_size", {}).get("h", 1000)
                                
                                scale_x = page_rect.width / canvas_w
                                scale_y = page_rect.height / canvas_h
                                
                                for link_data in local_links:
                                    r = link_data["rect"]
                                    url = link_data["url"]
                                    
                                    x0 = r.x() * scale_x
                                    y0 = r.y() * scale_y
                                    x1 = (r.x() + r.width()) * scale_x
                                    y1 = (r.y() + r.height()) * scale_y
                                    
                                    link_rect = fitz.Rect(x0, y0, x1, y1)
                                    page.insert_link({"kind": fitz.LINK_URI, "from": link_rect, "uri": url})
                                
                                # TRUQUE: Salva em um arquivo .tmp e move por cima. Burla 100% o File Lock.
                                tmp_path = str(out_path) + ".tmp"
                                pdf_doc.save(tmp_path)
                                pdf_doc.close()
                                shutil.move(tmp_path, str(out_path))
                                
                            except Exception as e:
                                self.error_occurred.emit(f"Falha ao injetar links no PDF {out_path.name}: {e}")
                                
                        self.card_finished.emit(out_path.name, original_idx, local_links)
                else:
                    out_path = self.output_dir / f"{filename}.png"
                    self.renderer.render_row(row_plain, row_rich, out_path, out_links=local_links)
                    self.card_finished.emit(out_path.name, original_idx, local_links)
            
            if painter:
                painter.end()

        except Exception as e:
            self.error_occurred.emit(str(e))

class PageRenderWorker(QThread):
    page_finished = Signal(int, str, str) 
    error_occurred = Signal(str)

    def __init__(self, tasks, renderer, output_dir, imposition_settings, export_format="PNG", single_pdf=False):
        super().__init__()
        self.tasks = tasks
        self.renderer = renderer
        self.output_dir = output_dir
        self.export_format = export_format
        self.single_pdf = single_pdf
        
        w_mm = imposition_settings.get("target_w_mm", 100)
        h_mm = imposition_settings.get("target_h_mm", 150)
        sheet_w = imposition_settings.get("sheet_w_mm", 210.0)
        sheet_h = imposition_settings.get("sheet_h_mm", 297.0)
        crop_marks = imposition_settings.get("crop_marks", True)
        bleed_margin = imposition_settings.get("bleed_margin", False)
        
        self.assembler = SheetAssembler(w_mm, h_mm, sheet_w, sheet_h, crop_marks, bleed_margin)
        
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            writer = None
            painter = None
            layout = None
            out_path_single = self.output_dir / f"{self.output_dir.name}_Imposicao.pdf"

            if self.single_pdf and self.export_format == "PDF":
                writer = QPdfWriter(str(out_path_single))
                
                # A folha física agora é gerada com precisão em milímetros baseada na montagem final
                writer.setPageSize(QPageSize(QPageSize.PageSizeId.Custom))
                layout = writer.pageLayout()
                w_sheet_mm = (self.assembler.sheet_w * 25.4) / 300.0
                h_sheet_mm = (self.assembler.sheet_h * 25.4) / 300.0
                layout.setPageSize(QPageSize(QSizeF(w_sheet_mm, h_sheet_mm), QPageSize.Unit.Millimeter))
                layout.setOrientation(self.assembler.orientation)
                layout.setMargins(QMarginsF(0, 0, 0, 0))
                writer.setPageLayout(layout)
                painter = QPainter(writer)

            for i, page_task in enumerate(self.tasks):
                if not self._is_running: break

                page_num = page_task["page_num"]
                cards_data = page_task["cards"]
                
                card_images = []
                for (original_idx, r_plain, r_rich, fname) in cards_data:
                    img = self.renderer.render_to_qimage(r_plain, r_rich)
                    card_images.append(img)
                
                sheet_img = self.assembler.render_sheet(card_images)
                out_name = page_task["output_filename"]
                out_path = self.output_dir / out_name
                
                if self.export_format == "PDF":
                    if self.single_pdf:
                        if i > 0:
                            writer.newPage()
                        painter.drawImage(layout.paintRectPixels(writer.resolution()), sheet_img)
                        final_name = out_path_single.name
                    else:
                        out_path = out_path.with_suffix(".pdf")
                        writer_single = QPdfWriter(str(out_path))
                        
                        # Mesmo cálculo milimétrico para os PDFs Avulsos do modo de Imposição
                        writer_single.setPageSize(QPageSize(QPageSize.PageSizeId.Custom))
                        layout_single = writer_single.pageLayout()
                        w_sheet_mm = (self.assembler.sheet_w * 25.4) / 300.0
                        h_sheet_mm = (self.assembler.sheet_h * 25.4) / 300.0
                        layout_single.setPageSize(QPageSize(QSizeF(w_sheet_mm, h_sheet_mm), QPageSize.Unit.Millimeter))
                        layout_single.setMargins(QMarginsF(0, 0, 0, 0))
                        writer_single.setPageLayout(layout_single)
                        painter_single = QPainter(writer_single)
                        painter_single.drawImage(layout_single.paintRectPixels(writer_single.resolution()), sheet_img)
                        painter_single.end()
                        final_name = out_path.name
                else:
                    sheet_img.save(str(out_path))
                    final_name = out_path.name
                
                msg = f"🖨️ FOLHA {page_task['page_num']:02d} OK ({len(card_images)} itens)"
                self.page_finished.emit(len(card_images), final_name, msg)
                
                card_images.clear()
                del sheet_img

            if painter:
                painter.end()

        except Exception as e:
            self.error_occurred.emit(f"Erro no Worker: {str(e)}\n{traceback.format_exc()}")
            
            
class HybridAssemblerWorker(QThread):
    finished_assembly = Signal()
    error_occurred = Signal(str)

    def __init__(self, generated_files, work_dir, output_dir, is_imposition, imposition_settings, target_w_mm, target_h_mm, all_links=None, canvas_w=1000, canvas_h=1000):
        super().__init__()
        self.generated_files = generated_files
        self.work_dir = work_dir
        self.output_dir = output_dir
        self.is_imposition = is_imposition
        self.imposition_settings = imposition_settings
        self.target_w_mm = target_w_mm
        self.target_h_mm = target_h_mm
        self.all_links = all_links or {}
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h

    def run(self):
        try:
            out_path_single = self.output_dir / f"{self.output_dir.name}_Completo.pdf"
            if self.is_imposition:
                out_path_single = self.output_dir / f"{self.output_dir.name}_Imposicao.pdf"

            writer = QPdfWriter(str(out_path_single))
            writer.setPageSize(QPageSize(QPageSize.PageSizeId.Custom))
            
            layout = writer.pageLayout()
            layout.setMargins(QMarginsF(0, 0, 0, 0))

            if self.is_imposition:
                sheet_w = self.imposition_settings.get("sheet_w_mm", 210.0)
                sheet_h = self.imposition_settings.get("sheet_h_mm", 297.0)
                tw = self.imposition_settings.get("target_w_mm", 100.0)
                th = self.imposition_settings.get("target_h_mm", 150.0)
                marks = self.imposition_settings.get("crop_marks", True)
                
                # Recalcula a orientação vencedora para o PDF final
                temp_asm = SheetAssembler(tw, th, sheet_w, sheet_h, marks)
                layout.setPageSize(QPageSize(QSizeF(sheet_w, sheet_h), QPageSize.Unit.Millimeter))
                layout.setOrientation(temp_asm.orientation)
            else:
                layout.setPageSize(QPageSize(QSizeF(self.target_w_mm, self.target_h_mm), QPageSize.Unit.Millimeter))
                
            writer.setPageLayout(layout)
            painter = QPainter(writer)

            # Os arquivos já virão ordenados perfeitamente pelo índice
            sorted_files = sorted(self.generated_files)

            for i, filename in enumerate(sorted_files):
                if i > 0:
                    writer.newPage()
                img_path = self.work_dir / filename
                if not img_path.exists(): continue
                
                img = QImage(str(img_path))
                painter.drawImage(layout.paintRectPixels(writer.resolution()), img)
                del img 
            
            painter.end()
            
            # Força a liberação do arquivo final antes de injetar os links
            del painter
            del layout
            del writer

            # --- PÓS-PROCESSAMENTO: Injeção de Hiperlinks no PDF Único ---
            if not self.is_imposition and self.all_links:
                try:
                    pdf_doc = fitz.open(str(out_path_single))
                    # O PDF único terá várias páginas, uma para cada cartão
                    for page_idx, links in self.all_links.items():
                        if page_idx >= len(pdf_doc): continue
                        
                        page = pdf_doc[page_idx]
                        page_rect = page.rect
                        
                        # Cálculo de escala (assumindo que todas as páginas têm o mesmo tamanho)
                        # Buscamos o canvas_size do template via manager se necessário, ou usamos proporção
                        # Como é o modo híbrido, a imagem original foi gerada no tamanho do canvas
                        # Aqui usamos uma lógica de proporção simples baseada no rect da página
                        scale_x = page_rect.width / self.canvas_w
                        scale_y = page_rect.height / self.canvas_h

                        for link_data in links:
                            r = link_data["rect"]
                            url = link_data["url"]
                            link_rect = fitz.Rect(
                                r.x() * scale_x, 
                                r.y() * scale_y, 
                                (r.x() + r.width()) * scale_x, 
                                (r.y() + r.height()) * scale_y
                            )
                            page.insert_link({"kind": fitz.LINK_URI, "from": link_rect, "uri": url})
                    
                    pdf_doc.saveIncr()
                    pdf_doc.close()
                except Exception as e:
                    print(f"[WARN] Erro ao injetar links no PDF Híbrido: {e}")

            shutil.rmtree(self.work_dir, ignore_errors=True)
            self.finished_assembly.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))