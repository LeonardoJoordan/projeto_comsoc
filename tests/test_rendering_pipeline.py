import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader

from features.generator.imposition import SheetAssembler
from features.generator.manager import RenderManager
from features.generator.renderer import NativeRenderer
from features.generator.workers import HybridAssemblerWorker


APP = QApplication.instance() or QApplication([])


def template():
    shape = {
        "object_id": "shape:1", "shape_type": "rectangle",
        "x": 20, "y": 20, "width": 160, "height": 110,
        "rotation": 0, "opacity": 1, "visible": True,
        "fill_color": "#e02020", "fill_opacity": 1,
        "outline_enabled": True, "outline_color": "#000000",
        "outline_opacity": 1, "outline_width": 4,
        "outline_position": "inside", "outline_join": "miter",
        "has_link": True, "link_key": "Site",
    }
    return {
        "name": "Pipeline Test", "canvas_size": {"w": 240, "h": 180},
        "target_w_mm": 80, "target_h_mm": 60,
        "background_path": None, "images": [], "boxes": [],
        "signatures": [], "shapes": [shape],
        "layer_order": ["shape:1"], "placeholders": ["Site"],
    }


class RenderingPipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def produce(self, rows, *, fmt="PDF", single=False):
        output = self.base / f"output_{fmt}_{single}"
        output.mkdir()
        manager = RenderManager(
            NativeRenderer(template()), rows, rows, output, "item_{Site}",
            export_format=fmt, single_pdf=single,
            target_w_mm=80, target_h_mm=60,
        )
        errors, done = [], []
        manager.error_occurred.connect(errors.append)
        manager.finished_process.connect(lambda: done.append(True))
        try:
            with patch("features.generator.manager.os.cpu_count", return_value=4):
                manager.start()
            for _ in range(1000):
                if done:
                    break
                QTest.qWait(10)
            self.assertTrue(done, "Geração não concluiu em 10 segundos")
            self.assertFalse(errors, errors)
            return [output / name for name in sorted(manager.generated_files)]
        finally:
            manager.stop()
            if hasattr(manager, "assembler_worker"):
                manager.assembler_worker.wait()

    def test_shape_links_and_static_cache_match(self):
        renderer = NativeRenderer(template())
        values = {"Site": "example.com"}
        links = []
        expected = renderer.render_to_qimage(values, values, links)
        self.assertEqual(expected.pixelColor(80, 70), QColor("#e02020"))
        self.assertEqual(links[0]["url"], "https://example.com")
        renderer.pre_render_static_base()
        cached_links = []
        actual = renderer.render_to_qimage(values, values, cached_links)
        self.assertEqual(expected, actual)
        self.assertEqual(links, cached_links)

    def test_pdf_per_item_and_grouped_keep_size_and_links(self):
        rows = [{"Site": "https://example.com/a"}, {"Site": "https://example.com/b"}]
        for single in (False, True):
            files = self.produce(rows, single=single)
            pages = [page for path in files for page in PdfReader(path).pages]
            self.assertEqual(len(pages), 2)
            for row, page in zip(rows, pages):
                self.assertAlmostEqual(float(page.mediabox.width) * 25.4 / 72, 80, delta=.18)
                self.assertAlmostEqual(float(page.mediabox.height) * 25.4 / 72, 60, delta=.18)
                annotations = page.get("/Annots", [])
                urls = [item.get_object()["/A"]["/URI"] for item in annotations]
                self.assertEqual(urls, [row["Site"]])

    def test_imposition_capacity_and_partial_sheet(self):
        assembler = SheetAssembler(80, 60, 210, 297, True)
        self.assertGreater(assembler.capacity, 1)
        card = NativeRenderer(template()).render_to_qimage({}, {})
        full = assembler.render_sheet([card] * assembler.capacity)
        partial = assembler.render_sheet([card])
        self.assertEqual(full.size(), partial.size())
        self.assertEqual(full.pixelColor(assembler.margin_left + 50, assembler.margin_top + 50),
                         partial.pixelColor(assembler.margin_left + 50, assembler.margin_top + 50))
        self.assertEqual(partial.pixelColor(partial.width() - 1, partial.height() - 1), QColor(Qt.white))

    def test_failures_finish_once_and_do_not_report_false_success(self):
        manager = RenderManager(NativeRenderer(template()), [], [], self.base, "item")
        errors, done = [], []
        manager.error_occurred.connect(errors.append)
        manager.finished_process.connect(lambda: done.append(True))
        manager.start()
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(done), 1)

        cache = self.base / "cache"
        cache.mkdir()
        worker = HybridAssemblerWorker(["missing.png"], cache, self.base, False, {}, 80, 60)
        worker_errors, assembled = [], []
        worker.error_occurred.connect(worker_errors.append)
        worker.finished_assembly.connect(lambda: assembled.append(True))
        worker.run()
        self.assertEqual(len(worker_errors), 1)
        self.assertFalse(assembled)
        self.assertTrue(cache.exists())


if __name__ == "__main__":
    unittest.main()
