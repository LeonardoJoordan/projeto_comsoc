"""Geração sequencial das folhas de prévia fora da thread da interface."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt

from features.generator.production_plan import build_imposition_plan
from features.generator.renderer import NativeRenderer


class SheetPreviewWorker(QThread):
    pageReady = Signal(int, str, int)
    pageFailed = Signal(int, str, int)

    def __init__(self, template, rows, settings, output_dir, generation, first_page=0, parent=None):
        super().__init__(parent)
        self.template = template
        self.rows = rows
        self.settings = settings
        self.output_dir = Path(output_dir)
        self.generation = generation
        self.first_page = first_page
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        try:
            plan = build_imposition_plan(self.rows, self.settings)
            if not plan.pages:
                return
            renderer = NativeRenderer(self.template)
            renderer.pre_render_static_base()
            first = min(max(0, self.first_page), len(plan.pages) - 1)
            order = [first] + [index for index in range(len(plan.pages)) if index != first]

            self.output_dir.mkdir(parents=True, exist_ok=True)
            for page_index in order:
                if not self._running or self.isInterruptionRequested():
                    return
                cards = [
                    renderer.render_to_qimage(row_plain, row_rich)
                    for row_plain, row_rich in plan.pages[page_index]
                ]
                if not self._running or self.isInterruptionRequested():
                    return
                image = plan.assembler.render_sheet(cards)
                if max(image.width(), image.height()) > 1800:
                    image = image.scaled(
                        1800, 1800,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                path = self.output_dir / f"sheet_{page_index:05d}.png"
                if not image.save(str(path), "PNG"):
                    raise OSError(f"Não foi possível gravar {path.name}")
                self.pageReady.emit(page_index, str(path), self.generation)
        except Exception as exc:
            self.pageFailed.emit(self.first_page, str(exc), self.generation)
