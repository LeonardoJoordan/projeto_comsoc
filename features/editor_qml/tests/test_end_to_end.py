"""Validação com cópias dos modelos reais e a mesma produção usada pelo workspace."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from pypdf import PdfReader
from features.editor_qml.bridge import EditorBridge
from features.generator.renderer import NativeRenderer
from features.generator.manager import RenderManager
from features.generator.imposition import SheetAssembler
from features.generator.workers import HybridAssemblerWorker

APP = QApplication.instance() or QApplication([])
MODELS = Path(__file__).resolve().parents[3] / "models"


def pixels(image):
    converted = image.convertToFormat(QImage.Format_RGBA8888)
    return bytes(converted.constBits())


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.bridge = EditorBridge()
        self.bridge.attachCanvas()

    def tearDown(self):
        self.bridge.shutdown()
        self.temp.cleanup()

    def produce(self, data, folder, fmt, single=False, imposition=None, rows=None, size=(210.312, 297.349)):
        folder.mkdir()
        rows = rows or [{"Nome": "Ana"}, {"Nome": "Bruno"}, {"Nome": "Carla"}]
        manager = RenderManager(NativeRenderer(data), rows, rows, folder, "{Nome}",
                                imposition, fmt, single, *size)
        errors, done = [], []
        manager.error_occurred.connect(errors.append)
        manager.finished_process.connect(lambda: done.append(True))
        try:
            with patch("features.generator.manager.os.cpu_count", return_value=4):
                manager.start()
            for _ in range(3000):
                if done or errors:
                    break
                QTest.qWait(10)
            self.assertFalse(errors, errors)
            self.assertTrue(done, "Produção não concluiu em 30 segundos")
            if os.environ.get("COMSOC_VALIDATION_ARTIFACTS"):
                target = Path(os.environ["COMSOC_VALIDATION_ARTIFACTS"]) / folder.relative_to(self.base)
                target.mkdir(parents=True, exist_ok=True)
                for name in manager.generated_files:
                    shutil.copy2(folder / name, target / name)
            return [folder / name for name in sorted(manager.generated_files)]
        finally:
            manager.stop()
            if hasattr(manager, "assembler_worker"):
                manager.assembler_worker.wait()

    def assert_page(self, page, width, height):
        # O MediaBox do Qt é quantizado em pontos inteiros (1 pt = 0,353 mm).
        self.assertAlmostEqual(float(page.mediabox.width) * 25.4 / 72, width, delta=0.18)
        self.assertAlmostEqual(float(page.mediabox.height) * 25.4 / 72, height, delta=0.18)
        self.assertTrue(page.images, "PDF sem imagem do modelo")

    def test_real_models_migrate_save_reopen_and_export_without_pixel_changes(self):
        originals = {p: hashlib.sha256(p.read_bytes()).digest()
                     for p in MODELS.rglob("*") if p.is_file()}
        self.assertTrue(originals)
        for source in sorted(MODELS.glob("*/template_v3.json")):
            with self.subTest(model=source.parent.name):
                copied = self.base / source.parent.name
                shutil.copytree(source.parent, copied)
                path = copied / source.name
                data = json.loads(path.read_text())
                data["__model_dir"] = str(copied)
                # Caminhos de imagens/assinaturas resolvidos como no workspace;
                # fundo relativo exercita também a resolução direta no renderer.
                for group in ("images", "signatures"):
                    for item in data.get(group, []):
                        item["path"] = str(copied / item["path"])
                self.assertTrue(self.bridge.load(str(path)))
                self.assertEqual(self.bridge._data["canvas_size"], data["canvas_size"])
                dest = self.base / (source.parent.name + "_saved") / source.name
                self.assertTrue(self.bridge.save_to(dest))
                self.assertTrue(self.bridge.load(str(dest)))
                old, new = NativeRenderer(data), NativeRenderer(self.bridge.render_data())
                for filled, signature in ((False, False), (True, True)):
                    row = {key: ("Validação Áé <b>texto</b>" if filled else "")
                           for key in data.get("placeholders", [])}
                    row["__use_signature__"] = signature
                    expected = old.render_to_qimage(row, row)
                    actual = new.render_to_qimage(row, row)
                    self.assertEqual(pixels(expected), pixels(actual))
                    new.pre_render_static_base()
                    self.assertEqual(pixels(expected), pixels(new.render_to_qimage(row, row)))
                w = data.get("target_w_mm", data["canvas_size"]["w"] * 25.4 / 300)
                h = data.get("target_h_mm", data["canvas_size"]["h"] * 25.4 / 300)
                for fmt in ("PNG", "PDF"):
                    files = self.produce(self.bridge.render_data(), copied / fmt, fmt,
                                         rows=[row], size=(w, h))
                    self.assertEqual(len(files), 1)
                    if fmt == "PNG":
                        result = QImage(str(files[0]))
                        self.assertEqual(pixels(expected), pixels(result))
                        self.assertAlmostEqual(result.width()*1000/result.dotsPerMeterX(), w, delta=0.03)
                    else:
                        self.assert_page(PdfReader(files[0]).pages[0], w, h)
        self.assertEqual(originals, {p: hashlib.sha256(p.read_bytes()).digest() for p in originals})

    def test_legacy_opens_real_copies_and_exposes_existing_dimension_difference(self):
        from features.editor.editor_window import EditorWindow
        models = self.base / "models"
        shutil.copytree(MODELS, models)
        with patch("features.editor.editor_window.get_models_dir", return_value=models):
            window = EditorWindow()
            try:
                for path in sorted(models.glob("*/template_v3.json")):
                    with self.subTest(model=path.parent.name):
                        original = json.loads(path.read_text())
                        window.load_from_json(str(path))
                        state = window.get_current_scene_state()
                        for group in ("boxes", "images", "signatures"):
                            self.assertEqual(len(state.get(group, [])), len(original.get(group, [])))
                        if original.get("background_path"):
                            self.assertTrue(state.get("background_path"))
                        if path.parent.name == "teste":
                            self.assertEqual(original["canvas_size"], {"w": 1000, "h": 1000})
                            self.assertEqual(state["canvas_size"], {"w": 1181, "h": 1771})
            finally:
                window._last_saved_state = window.get_current_scene_state()
                window.close()
                window.deleteLater()

    def test_modern_model_direct_and_combined_pdf_links_and_page_sizes(self):
        self.bridge.setDocumentSize("400", "300", "210.312", "297.349")
        self.bridge.addItem("shape")
        self.bridge.setValue("fill_color", "#e02020")
        self.bridge.setValue("outline_enabled", True)
        self.bridge.setValue("outline_width", 5)
        self.bridge.setValue("rotation", 15)
        self.bridge.setValue("has_link", True)
        self.bridge.setValue("link_key", "Site")
        self.bridge.addItem("text")
        self.bridge.setValue("html", "<p><b>{Nome}</b></p>")
        self.bridge.setValue("outline_enabled", True)
        dest = self.base / "modern" / "template_v3.json"
        self.assertTrue(self.bridge.save_to(dest))
        self.assertTrue(self.bridge.load(str(dest)))
        rows = [{"Nome": name, "Site": "https://example.com/" + name}
                for name in ("Ana", "Bruno", "Carla")]
        for single in (False, True):
            files = self.produce(self.bridge.render_data(), self.base / str(single), "PDF", single, rows=rows)
            pages = [page for path in files for page in PdfReader(path).pages]
            self.assertEqual(len(pages), 3)
            for row, page in zip(rows, pages):
                self.assert_page(page, 210.312, 297.349)
                links = [a.get_object()["/A"]["/URI"] for a in page["/Annots"]]
                self.assertEqual(links, [row["Site"]])

    def test_imposition_png_pdf_combined_portrait_landscape_and_partial_sheet(self):
        self.bridge.setDocumentSize("120", "100", "40", "50")
        self.bridge.addItem("shape")
        self.bridge.setValue("fill_color", "#ff0000")
        data = self.bridge.render_data()
        for width, height in ((95, 134.3), (40, 50)):
            settings = dict(enabled=True, target_w_mm=width, target_h_mm=height,
                            sheet_w_mm=210, sheet_h_mm=297, crop_marks=True)
            assembler = SheetAssembler(width, height)
            rows = [{"Nome": str(i)} for i in range(assembler.capacity + 1)]
            for fmt, single in (("PNG", False), ("PDF", False), ("PDF", True)):
                with self.subTest(size=(width, height), format=fmt, combined=single):
                    files = self.produce(data, self.base / f"{width}_{fmt}_{single}", fmt,
                                         single, settings, rows)
                    if fmt == "PNG":
                        self.assertEqual(len(files), 2)
                        for index, path in enumerate(files):
                            count = assembler.capacity if index == 0 else 1
                            card = NativeRenderer(data).render_to_qimage({}, {})
                            expected = assembler.render_sheet([card] * count)
                            actual = QImage(str(path))
                            self.assertEqual(pixels(expected), pixels(actual))
                            self.assertAlmostEqual(actual.dotsPerMeterX() * .0254, 300, delta=.02)
                    else:
                        pages = [page for path in files for page in PdfReader(path).pages]
                        self.assertEqual(len(pages), 2)
                        for page in pages:
                            self.assert_page(page, assembler.sheet_w_mm, assembler.sheet_h_mm)

    def test_png_write_failure_is_reported(self):
        renderer = NativeRenderer(self.bridge.render_data())
        with self.assertRaises(OSError):
            renderer.render_row({}, {}, self.base / "missing" / "output.png")

    @unittest.skipUnless(shutil.which("pdftoppm"), "Poppler necessário para comparação visual independente")
    def test_pdf_raster_matches_modern_renderer(self):
        self.bridge.setDocumentSize("400", "300", "100", "75")
        self.bridge.addItem("shape")
        self.bridge.setValue("fill_color", "#e02020")
        self.bridge.setValue("outline_enabled", True)
        self.bridge.setValue("rotation", 15)
        self.bridge.addItem("text")
        self.bridge.setValue("html", "<p>{Nome}</p>")
        self.bridge.setValue("outline_enabled", True)
        data = self.bridge.render_data()
        row = {"Nome": "Validação"}
        pdf = self.produce(data, self.base / "raster", "PDF", rows=[row], size=(100, 75))[0]
        subprocess.run(["pdftoppm", "-scale-to-x", "400", "-scale-to-y", "300",
                        "-singlefile", "-png", str(pdf), str(self.base / "rasterized")],
                       check=True, capture_output=True, timeout=30)
        expected = NativeRenderer(data).render_to_qimage(row, row)
        actual = QImage(str(self.base / "rasterized.png"))
        self.assertEqual(actual.size(), expected.size())
        reference, rendered = pixels(expected), pixels(actual)
        error = [sum(abs(a-b) for a, b in zip(reference[c::4], rendered[c::4])) / (400*300)
                 for c in range(3)]
        self.assertLess(max(error), 8, f"Erro médio por canal (0–255): {error}")

    def test_generation_errors_release_workspace_completion(self):
        data = self.bridge.render_data()
        for rows, settings, output in (
            ([], None, self.base),
            ([{}], dict(enabled=True, target_w_mm=1000, target_h_mm=1000), self.base),
            ([{}], None, self.base / "missing"),
        ):
            manager = RenderManager(NativeRenderer(data), rows, rows, output, "item", settings)
            errors, done = [], []
            manager.error_occurred.connect(errors.append)
            manager.finished_process.connect(lambda: done.append(True))
            try:
                manager.start()
                for _ in range(500):
                    if done:
                        break
                    QTest.qWait(10)
                self.assertEqual(len(done), 1)
                self.assertEqual(len(errors), 1)
            finally:
                manager.stop()

    def test_missing_hybrid_image_reports_error_instead_of_success(self):
        work = self.base / "cache"
        work.mkdir()
        worker = HybridAssemblerWorker(["missing.png"], work, self.base, False, {}, 100, 75)
        errors, done = [], []
        worker.error_occurred.connect(errors.append)
        worker.finished_assembly.connect(lambda: done.append(True))
        worker.run()
        self.assertEqual(len(errors), 1)
        self.assertFalse(done)
        self.assertTrue(work.exists())


if __name__ == "__main__":
    unittest.main()
