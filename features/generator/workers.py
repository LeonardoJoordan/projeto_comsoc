import traceback
import shutil
from PySide6.QtCore import QThread, Signal, QSizeF, QMarginsF
from PySide6.QtGui import QImage, QPainter, QPdfWriter, QPageLayout, QPageSize

from .imposition import SheetAssembler
from .pdf_links import inject_pdf_links
from core.i18n import tr


def physical_page(width_mm, height_mm):
    # Evita que medidas personalizadas próximas de A4 sejam arredondadas para A4.
    return QPageSize(QSizeF(width_mm, height_mm), QPageSize.Unit.Millimeter,
                     "", QPageSize.SizeMatchPolicy.ExactMatch)


def pdf_painter(writer):
    painter = QPainter(writer)
    if not painter.isActive():
        raise OSError(tr("Não foi possível abrir o PDF para gravação."))
    return painter


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
                layout.setPageSize(physical_page(self.target_w_mm, self.target_h_mm))
                layout.setMargins(QMarginsF(0, 0, 0, 0))
                writer.setPageLayout(layout)
                painter = pdf_painter(writer)

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
                        layout_single.setPageSize(physical_page(self.target_w_mm, self.target_h_mm))
                        layout_single.setMargins(QMarginsF(0, 0, 0, 0))
                        writer_single.setPageLayout(layout_single)
                        painter_single = pdf_painter(writer_single)
                        painter_single.drawImage(layout_single.paintRectPixels(writer_single.resolution()), img)
                        painter_single.end()
                        
                        del painter_single
                        del layout_single
                        del writer_single
                        
                        # --- PÓS-PROCESSAMENTO: Injeção de Hiperlinks ---
                        if local_links and not self.single_pdf:
                            try:
                                canvas_w = self.renderer.tpl.get("canvas_size", {}).get("w", 1000)
                                canvas_h = self.renderer.tpl.get("canvas_size", {}).get("h", 1000)
                                inject_pdf_links(
                                    out_path,
                                    {0: local_links},
                                    canvas_w,
                                    canvas_h,
                                )
                                
                            except Exception as e:
                                self.error_occurred.emit(tr("Falha ao adicionar links ao PDF {arquivo}: {erro}").format(arquivo=out_path.name, erro=e))
                                
                        self.card_finished.emit(out_path.name, original_idx, local_links)
                else:
                    out_path = self.output_dir / f"{filename}.png"
                    self.renderer.render_row(row_plain, row_rich, out_path, out_links=local_links,
                                             target_w_mm=self.target_w_mm, target_h_mm=self.target_h_mm)
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
                w_sheet_mm = self.assembler.sheet_w_mm
                h_sheet_mm = self.assembler.sheet_h_mm
                layout.setPageSize(physical_page(w_sheet_mm, h_sheet_mm))
                layout.setMargins(QMarginsF(0, 0, 0, 0))
                writer.setPageLayout(layout)
                painter = pdf_painter(writer)

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
                        w_sheet_mm = self.assembler.sheet_w_mm
                        h_sheet_mm = self.assembler.sheet_h_mm
                        layout_single.setPageSize(physical_page(w_sheet_mm, h_sheet_mm))
                        layout_single.setMargins(QMarginsF(0, 0, 0, 0))
                        writer_single.setPageLayout(layout_single)
                        painter_single = pdf_painter(writer_single)
                        painter_single.drawImage(layout_single.paintRectPixels(writer_single.resolution()), sheet_img)
                        painter_single.end()
                        del painter_single
                        del layout_single
                        del writer_single
                        final_name = out_path.name
                else:
                    if not sheet_img.save(str(out_path), "PNG"):
                        raise OSError(f"Não foi possível gravar {out_path}.")
                    final_name = out_path.name
                
                msg = f"🖨️ FOLHA {page_task['page_num']:02d} OK ({len(card_images)} itens)"
                self.page_finished.emit(len(card_images), final_name, msg)
                
                card_images.clear()
                del sheet_img

            if painter:
                painter.end()

        except Exception as e:
            self.error_occurred.emit(tr("Erro no processamento: {erro}\n{detalhes}").format(erro=e, detalhes=traceback.format_exc()))
            
            
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
                bleed = self.imposition_settings.get("bleed_margin", False)

                # Recalcula a orientação vencedora para o PDF final
                temp_asm = SheetAssembler(tw, th, sheet_w, sheet_h, marks, bleed)
                layout.setPageSize(physical_page(temp_asm.sheet_w_mm, temp_asm.sheet_h_mm))
            else:
                layout.setPageSize(physical_page(self.target_w_mm, self.target_h_mm))
                
            writer.setPageLayout(layout)
            painter = pdf_painter(writer)

            # Os arquivos já virão ordenados perfeitamente pelo índice
            sorted_files = sorted(self.generated_files)

            for i, filename in enumerate(sorted_files):
                if i > 0:
                    writer.newPage()
                img_path = self.work_dir / filename
                img = QImage(str(img_path))
                if img.isNull():
                    painter.end()
                    raise OSError(f"Imagem ausente ou inválida na montagem: {img_path.name}")
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
                    inject_pdf_links(
                        out_path_single,
                        self.all_links,
                        self.canvas_w,
                        self.canvas_h,
                    )
                except Exception as e:
                    raise OSError(f"Erro ao injetar links no PDF Híbrido: {e}") from e

            shutil.rmtree(self.work_dir, ignore_errors=True)
            self.finished_assembly.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class PreviewRenderWorker(QThread):
    preview_ready = Signal(str, str) # model_name, thumb_path
    error_occurred = Signal(str)

    def __init__(self, model_name, template_data, model_dir):
        super().__init__()
        self.model_name = model_name
        self.template_data = template_data
        self.model_dir = model_dir
        import hashlib
        source = model_dir / "template_v3.json"
        self._source_hash = hashlib.sha256(source.read_bytes()).digest() if source.is_file() else None

    def run(self):
        try:
            from features.generator.renderer import NativeRenderer
            from PySide6.QtCore import Qt
            
            renderer = NativeRenderer(self.template_data)
            
            cache_folder = self.model_dir / ".render_cache"
            cache_folder.mkdir(parents=True, exist_ok=True)
            thumb_path = cache_folder / "thumbnail_raw.png"
            
            # Prepara os placeholders para a thumbnail crua
            placeholders = self.template_data.get("placeholders", [])
            row_rich = {p: f"{{{p}}}" for p in placeholders}
            
            img = renderer.render_preview_image(row_rich, max_side=1600)
            import hashlib
            source = self.model_dir / "template_v3.json"
            if self._source_hash is not None and (not source.is_file() or hashlib.sha256(source.read_bytes()).digest() != self._source_hash):
                return
            if not img.save(str(thumb_path), "PNG"):
                raise OSError("Não foi possível gravar a miniatura.")

            # Avisa a Janela Principal que terminou
            self.preview_ready.emit(self.model_name, str(thumb_path))
            
        except Exception as e:
            self.error_occurred.emit(tr("Erro na prévia em segundo plano: {erro}").format(erro=e))
