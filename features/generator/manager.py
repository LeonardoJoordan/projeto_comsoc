from PySide6.QtCore import Signal, QObject
import os
import math

# Imports corrigidos para a nova arquitetura
from core.naming_engine import build_output_filename
from .imposition import SheetAssembler
from .workers import PageRenderWorker, DirectRenderWorker

class RenderManager(QObject):
    progress_updated = Signal(int)
    log_updated = Signal(str)
    finished_process = Signal()
    error_occurred = Signal(str)

    def __init__(self, renderer, rows_plain, rows_rich, output_dir, filename_pattern, imposition_settings=None):
        super().__init__()
        self.renderer = renderer
        self.rows_plain = rows_plain
        self.rows_rich = rows_rich
        self.output_dir = output_dir
        self.pattern = filename_pattern
        
        self.imposition_settings = imposition_settings or {"enabled": False}
        self.is_imposition = self.imposition_settings.get("enabled", False)
        
        self.workers = []
        self.total_cards = len(rows_plain)
        self.cards_done = 0
        self.generated_files = []
        self._is_running = False

    def start(self):
        self._is_running = True
        self.cards_done = 0
        self.generated_files = []
        self.workers = []
        
        self.log_updated.emit("📋 Planejando produção...")
        
        all_tasks_data = []
        used_names = set()
        for i, row in enumerate(self.rows_plain):
            fname = build_output_filename(self.pattern, row, used_names)
            all_tasks_data.append( (self.rows_plain[i], self.rows_rich[i], fname) )

        cpu_count = os.cpu_count() or 4
        num_threads = max(1, cpu_count - 2)

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
            
            w = PageRenderWorker(worker_tasks, self.renderer, self.output_dir, self.imposition_settings)
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
            
            w = DirectRenderWorker(chunk, self.renderer, self.output_dir)
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
            if self._is_running:
                self.progress_updated.emit(100)
                self.finished_process.emit()
                self.log_updated.emit("✅ Processo finalizado com sucesso!")