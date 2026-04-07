from PySide6.QtCore import Signal, QObject
import os
import math

# Imports corrigidos para a nova arquitetura
from core.naming_engine import build_output_filename
from .imposition import SheetAssembler
from .workers import PageRenderWorker, DirectRenderWorker, HybridAssemblerWorker

class RenderManager(QObject):
    progress_updated = Signal(int)
    log_updated = Signal(str)
    finished_process = Signal()
    error_occurred = Signal(str)

    def __init__(self, renderer, rows_plain, rows_rich, output_dir, filename_pattern, imposition_settings=None, export_format="PNG", single_pdf=False, target_w_mm=100.0, target_h_mm=150.0):
        super().__init__()
        self.renderer = renderer
        self.rows_plain = rows_plain
        self.rows_rich = rows_rich
        self.output_dir = output_dir
        self.pattern = filename_pattern
        self.export_format = export_format.upper()
        self.single_pdf = single_pdf
        self.target_w_mm = target_w_mm
        self.target_h_mm = target_h_mm
        
        self.imposition_settings = imposition_settings or {"enabled": False}
        self.is_imposition = self.imposition_settings.get("enabled", False)
        
        self.workers = []
        self.total_cards = len(rows_plain)
        self.cards_done = 0
        self.generated_files = []
        self._is_running = False

    def start(self):
        self._is_running = True
        self._finish_emitted = False # Trava de segurança da Etapa Anterior
        self.cards_done = 0
        self.generated_files = []
        self.workers = []
        
        self.log_updated.emit("📋 Planejando produção...")
        
        cpu_count = os.cpu_count() or 4
        num_threads = max(1, cpu_count - 2)
        
        # --- LÓGICA HÍBRIDA (Fim do castramento de threads) ---
        self.is_hybrid = (self.single_pdf and self.export_format == "PDF")
        self.work_dir = self.output_dir / ".temp_hybrid" if self.is_hybrid else self.output_dir
        self.worker_format = "PNG" if self.is_hybrid else self.export_format

        if self.is_hybrid:
            self.work_dir.mkdir(parents=True, exist_ok=True)
            self.log_updated.emit(f"⚡ Modo Híbrido: Gerando em cache ({num_threads} threads)...")

        all_tasks_data = []
        used_names = set()
        
        for i in range(len(self.rows_plain)):
            row = self.rows_plain[i]
            fname = build_output_filename(self.pattern, row, used_names)
            
            # Indexação oculta: Garante que mesmo processados fora de ordem,
            # os arquivos sejam montados na sequência exata da planilha.
            if self.is_hybrid and not self.is_imposition:
                fname = f"{i:05d}_{fname}"
                
            all_tasks_data.append( (self.rows_plain[i], self.rows_rich[i], fname) )

        if self.is_imposition:
            self._start_imposition_mode(all_tasks_data, num_threads)
        else:
            self._start_direct_mode(all_tasks_data, num_threads)

    def _start_imposition_mode(self, all_data, num_threads):
        w_mm = self.imposition_settings.get("target_w_mm", 100)
        h_mm = self.imposition_settings.get("target_h_mm", 150)
        temp_asm = SheetAssembler(w_mm, h_mm)
        capacity = temp_asm.capacity
        
        total_pages = math.ceil(len(all_data) / capacity)
        self.log_updated.emit(f"📚 Modo Imposição: {len(all_data)} cartões cabem em {total_pages} folhas (Capacidade: {capacity}/fl).")
        self.log_updated.emit(f"🚀 Distribuindo trabalho para {num_threads} threads...")

        pages_jobs = []
        safe_pattern = self.pattern.replace("{", "").replace("}", "")

        for page_idx in range(total_pages):
            start_idx = page_idx * capacity
            end_idx = min(start_idx + capacity, len(all_data))
            
            page_cards = all_data[start_idx:end_idx]
            page_num = page_idx + 1
            
            job = {
                "page_num": page_num,
                "output_filename": f"{safe_pattern}_Folha_{page_num:02d}.png",
                "cards": page_cards
            }
            pages_jobs.append(job)

        chunk_size = math.ceil(total_pages / num_threads)
        
        for i in range(num_threads):
            start = i * chunk_size
            end = start + chunk_size
            worker_tasks = pages_jobs[start:end]
            
            if not worker_tasks: continue
            
            w = PageRenderWorker(worker_tasks, self.renderer, self.work_dir, self.imposition_settings, self.worker_format, False)
            w.page_finished.connect(self._on_page_finished)
            w.error_occurred.connect(self.error_occurred)
            w.finished.connect(self._check_all_finished)
            
            self.workers.append(w)
            w.start()

    def _start_direct_mode(self, all_data, num_threads):
        self.log_updated.emit(f"🚀 Modo Direto: Processando {len(all_data)} arquivos em {num_threads} threads...")
        
        chunk_size = math.ceil(len(all_data) / num_threads)
        
        for i in range(num_threads):
            start = i * chunk_size
            end = start + chunk_size
            chunk = all_data[start:end]
            
            if not chunk: continue
            
            w = DirectRenderWorker(chunk, self.renderer, self.work_dir, self.worker_format, False, self.target_w_mm, self.target_h_mm)
            w.card_finished.connect(self._on_direct_card_finished)
            w.error_occurred.connect(self.error_occurred)
            w.finished.connect(self._check_all_finished)
            
            self.workers.append(w)
            w.start()

    def stop(self):
        self._is_running = False
        self.log_updated.emit("🛑 Parando threads...")
        for w in self.workers:
            w.stop()
            w.quit()
            w.wait()

    def _on_page_finished(self, num_cards, filename, msg):
        if not self._is_running: return
        self.cards_done += num_cards
        self.log_updated.emit(msg)
        self.generated_files.append(filename)
        self._update_progress()

    def _on_direct_card_finished(self, filename):
        if not self._is_running: return
        self.cards_done += 1
        self.log_updated.emit(f"[{self.cards_done}/{self.total_cards}] Salvo: {filename}")
        self.generated_files.append(filename)
        self._update_progress()

    def _update_progress(self):
        done = min(self.cards_done, self.total_cards)
        percent = int((done / self.total_cards) * 100)
        self.progress_updated.emit(percent)

    def _check_all_finished(self):
        if all(w.isFinished() for w in self.workers):
            if self._is_running and not getattr(self, '_finish_emitted', False):
                self._finish_emitted = True
                self.progress_updated.emit(100)
                
                if getattr(self, 'is_hybrid', False):
                    self._start_hybrid_assembly()
                else:
                    self.finished_process.emit()
                    self.log_updated.emit("✅ Processo finalizado com sucesso!")

    def _start_hybrid_assembly(self):
        self.log_updated.emit("📦 Montando arquivo PDF Único final em segundo plano...")
        self.assembler_worker = HybridAssemblerWorker(
            self.generated_files, self.work_dir, self.output_dir, 
            self.is_imposition, self.imposition_settings, 
            self.target_w_mm, self.target_h_mm
        )
        self.assembler_worker.finished_assembly.connect(self._on_hybrid_assembly_finished)
        self.assembler_worker.error_occurred.connect(self._on_hybrid_assembly_error)
        self.assembler_worker.start()

    def _on_hybrid_assembly_finished(self):
        out_name = f"{self.output_dir.name}_Imposicao.pdf" if self.is_imposition else f"{self.output_dir.name}_Completo.pdf"
        self.generated_files = [out_name]
        self.finished_process.emit()
        self.log_updated.emit("✅ Processo finalizado com sucesso!")

    def _on_hybrid_assembly_error(self, error_msg):
        self.error_occurred.emit(f"Erro na montagem do PDF: {error_msg}")
        self.finished_process.emit()