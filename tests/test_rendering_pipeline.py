import tempfile
import unittest
import copy
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPageLayout
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader

from features.generator.imposition import SheetAssembler
from features.generator.manager import RenderManager
from features.generator.renderer import (
    NativeRenderer,
    renderers_for_document,
    signature_is_visible,
)
from features.generator.workers import DirectRenderWorker, HybridAssemblerWorker
from features.preview.sheet_preview_worker import SheetPreviewWorker
from core.model_document import add_blank_back_page


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


def two_page_template():
    front = template()
    back_shape = copy.deepcopy(front["shapes"][0])
    back_shape.update({
        "fill_color": "#2050e0",
        "link_key": "SiteVerso",
        "rotation": 25,
    })
    return {
        "schema_version": 4,
        "name": "Pipeline frente e verso",
        "canvas_size": copy.deepcopy(front["canvas_size"]),
        "target_w_mm": front["target_w_mm"],
        "target_h_mm": front["target_h_mm"],
        "placeholders": ["Site", "SiteVerso"],
        "guidelines_visible": True,
        "guidelines_locked": False,
        "pages": [
            {
                "page_id": "front", "field_ids": ["Site"],
                "background_path": None, "guidelines": [],
                "boxes": [], "images": [], "signatures": [],
                "shapes": copy.deepcopy(front["shapes"]),
                "layer_order": ["shape:1"],
            },
            {
                "page_id": "back", "field_ids": ["SiteVerso"],
                "background_path": None, "guidelines": [],
                "boxes": [], "images": [], "signatures": [],
                "shapes": [back_shape], "layer_order": ["shape:1"],
            },
        ],
    }


class RenderingPipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def signature_asset(self, name, color):
        path = self.base / name
        image = QImage(12, 12, QImage.Format_ARGB32)
        image.fill(QColor(color))
        self.assertTrue(image.save(str(path), "PNG"))
        return str(path)

    @staticmethod
    def signature(signature_id, path, x):
        return {
            "object_id": f"signature:{signature_id}",
            "signature_id": signature_id,
            "custom_name": signature_id,
            "path": path,
            "visible": True,
            "opacity": 1.0,
            "x": x,
            "y": 10,
            "width": 20,
            "height": 20,
            "rotation": 0,
        }

    def produce(self, rows, *, fmt="PDF", single=False, template_data=None, imposition=None):
        output = self.base / f"output_{fmt}_{single}"
        output.mkdir()
        source = template_data or template()
        renderers = (
            renderers_for_document(source)
            if source.get("schema_version") == 4 else [NativeRenderer(source)]
        )
        manager = RenderManager(
            renderers, rows, rows, output, "item_{Site}",
            export_format=fmt, single_pdf=single,
            target_w_mm=80, target_h_mm=60,
            imposition_settings=imposition,
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

    def test_each_signature_column_controls_only_its_own_signature(self):
        red = self.signature_asset("red.png", "#ef3038")
        blue = self.signature_asset("blue.png", "#2878e8")
        first = self.signature("sig-red", red, 10)
        second = self.signature("sig-blue", blue, 50)
        source = {
            "name": "Assinaturas independentes",
            "canvas_size": {"w": 90, "h": 40},
            "background_path": None,
            "images": [], "boxes": [], "shapes": [],
            "signatures": [first, second],
            "layer_order": [first["object_id"], second["object_id"]],
        }
        values = {
            "__signature_visibility__": {
                "sig-red": False,
                "sig-blue": True,
            }
        }
        renderer = NativeRenderer(source)

        image = renderer.render_to_qimage(values, values)
        self.assertEqual(image.pixelColor(20, 20), QColor("#ffffff"))
        self.assertEqual(image.pixelColor(60, 20), QColor("#2878e8"))

        # A otimização usada na geração em lote não pode congelar uma
        # assinatura na base estática e ignorar a decisão da tabela.
        renderer.pre_render_static_base()
        cached = renderer.render_to_qimage(values, values)
        self.assertEqual(cached, image)

    def test_signature_visibility_keeps_legacy_and_model_fallbacks(self):
        signature = {"signature_id": "sig-a", "visible": False}
        self.assertTrue(signature_is_visible(signature, {"__use_signature__": True}))
        self.assertFalse(signature_is_visible(signature, {"__use_signature__": False}))
        self.assertFalse(signature_is_visible(signature, {}))
        self.assertTrue(signature_is_visible(
            signature,
            {"__signature_visibility__": {"sig-a": True}},
        ))
        # Um mapa atual incompleto não deixa o booleano legado controlar as
        # demais assinaturas; para elas vale a configuração do modelo.
        self.assertFalse(signature_is_visible(signature, {
            "__signature_visibility__": {"outra": True},
            "__use_signature__": True,
        }))

    def test_front_and_back_use_the_same_individual_signature_map(self):
        red = self.signature_asset("front-signature.png", "#ef3038")
        blue = self.signature_asset("back-signature.png", "#2878e8")
        document = two_page_template()
        document["pages"][0]["signatures"] = [self.signature("front-signature", red, 10)]
        document["pages"][0]["layer_order"].append("signature:front-signature")
        document["pages"][1]["signatures"] = [self.signature("back-signature", blue, 10)]
        document["pages"][1]["layer_order"].append("signature:back-signature")
        values = {
            "__signature_visibility__": {
                "front-signature": False,
                "back-signature": True,
            }
        }

        front, back = renderers_for_document(document)
        front_image = front.render_to_qimage(values, values)
        back_image = back.render_to_qimage(values, values)

        self.assertNotEqual(front_image.pixelColor(20, 20), QColor("#ef3038"))
        self.assertEqual(back_image.pixelColor(20, 20), QColor("#2878e8"))

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

    def test_landscape_back_rotates_each_card_and_its_links_in_place(self):
        assembler = SheetAssembler(60, 40, 100, 140, False, False, auto_rotate=True)
        self.assertEqual(assembler.orientation, QPageLayout.Orientation.Landscape)
        card = QImage(120, 80, QImage.Format_ARGB32)
        card.fill(QColor("#ffffff"))
        painter = QPainter(card)
        painter.fillRect(0, 0, 40, 30, QColor("#e02020"))
        painter.end()
        links = []

        sheet = assembler.render_sheet(
            [card], preserve_slots=True,
            card_links=[[{"url": "https://example.com", "rect": QRectF(0, 0, 40, 30)}]],
            canvas_size=(120, 80), out_links=links, rotate_cards_180=True,
        )

        x = assembler.margin_left
        y = assembler.margin_top
        cell_w = assembler._grid_x(1) - x
        cell_h = assembler._grid_y(1) - y
        self.assertEqual(sheet.pixelColor(x + cell_w - 20, y + cell_h - 20), QColor("#e02020"))
        self.assertEqual(sheet.pixelColor(x + 20, y + 20), QColor("#ffffff"))
        self.assertGreater(links[0]["rect"].x(), x + cell_w / 2)
        self.assertGreater(links[0]["rect"].y(), y + cell_h / 2)

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
        self.assertFalse((self.base / f"{self.base.name}_Completo.pdf").exists())
        self.assertFalse(any(self.base.glob("*.partial.pdf")))

    def test_two_page_png_uses_one_base_name_and_page_suffixes(self):
        rows = [
            {"Site": "A", "SiteVerso": "A-verso"},
            {"Site": "B", "SiteVerso": "B-verso"},
        ]

        files = self.produce(rows, fmt="PNG", template_data=two_page_template())

        self.assertEqual(
            [path.name for path in files],
            ["item_A_pag1.png", "item_A_pag2.png", "item_B_pag1.png", "item_B_pag2.png"],
        )
        self.assertEqual(QImage(str(files[0])).pixelColor(80, 70), QColor("#e02020"))
        self.assertEqual(QImage(str(files[1])).pixelColor(80, 70), QColor("#2050e0"))

    def test_two_page_pdf_per_item_and_grouped_keep_order_and_links(self):
        rows = [
            {"Site": "https://example.com/a", "SiteVerso": "https://example.com/a-verso"},
            {"Site": "https://example.com/b", "SiteVerso": "https://example.com/b-verso"},
        ]
        expected_urls = [
            rows[0]["Site"], rows[0]["SiteVerso"],
            rows[1]["Site"], rows[1]["SiteVerso"],
        ]

        for grouped in (False, True):
            files = self.produce(rows, single=grouped, template_data=two_page_template())
            pages = [page for path in files for page in PdfReader(path).pages]
            self.assertEqual(len(pages), 4)
            urls = [
                annotation.get_object()["/A"]["/URI"]
                for page in pages
                for annotation in page.get("/Annots", [])
            ]
            self.assertEqual(urls, expected_urls)
            rectangles = [
                [float(value) for value in annotation.get_object()["/Rect"]]
                for page in pages
                for annotation in page.get("/Annots", [])
            ]
            # O link do verso acompanha a caixa delimitadora da forma rotacionada.
            self.assertGreater(rectangles[1][2] - rectangles[1][0], rectangles[0][2] - rectangles[0][0])
            for page in pages:
                self.assertAlmostEqual(float(page.mediabox.width) * 25.4 / 72, 80, delta=.18)
                self.assertAlmostEqual(float(page.mediabox.height) * 25.4 / 72, 60, delta=.18)

    def test_protected_grouped_pdf_uses_memory_pipeline_and_releases_snapshot(self):
        output = self.base / "protected-output"
        output.mkdir()
        snapshot = Mock()
        rows = [
            {"Site": "https://example.com/a", "SiteVerso": "https://example.com/a-verso"},
            {"Site": "https://example.com/b", "SiteVerso": "https://example.com/b-verso"},
        ]
        manager = RenderManager(
            renderers_for_document(two_page_template()), rows, rows, output,
            "item_{Site}", export_format="PDF", single_pdf=True,
            target_w_mm=80, target_h_mm=60,
            authorized_snapshot=snapshot, protected_content=True,
        )
        errors, done = [], []
        manager.error_occurred.connect(errors.append)
        manager.finished_process.connect(lambda: done.append(True))
        try:
            manager.start()
            for _ in range(1000):
                if done:
                    break
                QTest.qWait(10)
            self.assertTrue(done)
            self.assertFalse(errors)
            self.assertEqual(snapshot.close.call_count, 1)
            self.assertEqual(manager.page_renderers, [])
            self.assertIsNone(manager.renderer)
            for worker in manager.workers:
                self.assertEqual(worker.renderers, [])
            self.assertFalse((output / ".temp_hybrid").exists())
            self.assertFalse(list(output.glob(".*.partial.*")))
            self.assertFalse(list(output.glob(".*.links.tmp")))
            result = output / manager.generated_files[0]
            self.assertEqual(len(PdfReader(result).pages), 4)
        finally:
            manager.stop()

    def test_protected_individual_outputs_publish_only_final_files(self):
        rows = [{"Site": "A", "SiteVerso": "A-verso"}]
        for export_format in ("PNG", "PDF"):
            with self.subTest(export_format=export_format):
                output = self.base / f"protected-{export_format.lower()}"
                output.mkdir()
                snapshot = Mock()
                manager = RenderManager(
                    renderers_for_document(two_page_template()), rows, rows,
                    output, "item_{Site}", export_format=export_format,
                    target_w_mm=80, target_h_mm=60,
                    authorized_snapshot=snapshot, protected_content=True,
                )
                errors, done = [], []
                manager.error_occurred.connect(errors.append)
                manager.finished_process.connect(lambda: done.append(True))
                try:
                    manager.start()
                    for _ in range(1000):
                        if done:
                            break
                        QTest.qWait(10)
                    self.assertTrue(done)
                    self.assertFalse(errors)
                    self.assertEqual(snapshot.close.call_count, 1)
                    self.assertFalse(list(output.glob(".*.partial.*")))
                    self.assertFalse(list(output.glob(".*.links.tmp")))
                    self.assertEqual(len(manager.generated_files), 2 if export_format == "PNG" else 1)
                finally:
                    manager.stop()

    def test_protected_duplex_imposition_groups_faces_without_disk_cache(self):
        output = self.base / "protected-imposition"
        output.mkdir()
        snapshot = Mock()
        rows = [
            {"Site": f"https://example.com/{index}",
             "SiteVerso": f"https://example.com/{index}-verso"}
            for index in range(2)
        ]
        settings = {
            "enabled": True,
            "target_w_mm": 100.0, "target_h_mm": 140.0,
            "sheet_w_mm": 210.0, "sheet_h_mm": 297.0,
            "crop_marks": False, "bleed_margin": False,
        }
        manager = RenderManager(
            renderers_for_document(two_page_template()), rows, rows, output,
            "item_{Site}", export_format="PDF", single_pdf=True,
            target_w_mm=100, target_h_mm=140, imposition_settings=settings,
            authorized_snapshot=snapshot, protected_content=True,
        )
        errors, done = [], []
        manager.error_occurred.connect(errors.append)
        manager.finished_process.connect(lambda: done.append(True))
        try:
            manager.start()
            for _ in range(1000):
                if done:
                    break
                QTest.qWait(10)
            self.assertTrue(done)
            self.assertFalse(errors)
            self.assertEqual(snapshot.close.call_count, 1)
            self.assertEqual(manager.page_renderers, [])
            self.assertIsNone(manager.renderer)
            for worker in manager.workers:
                self.assertEqual(worker.renderers, [])
            self.assertFalse((output / ".temp_hybrid").exists())
            result = output / manager.generated_files[0]
            pages = PdfReader(result).pages
            self.assertEqual(len(pages), 2)
            urls = [
                [annotation.get_object()["/A"]["/URI"] for annotation in page.get("/Annots", [])]
                for page in pages
            ]
            self.assertEqual(urls[0], [row["Site"] for row in rows])
            self.assertEqual(urls[1], [row["SiteVerso"] for row in reversed(rows)])
        finally:
            manager.stop()

    def test_two_page_png_failure_does_not_publish_half_a_document(self):
        document = two_page_template()
        renderers = renderers_for_document(document)
        worker = DirectRenderWorker(
            [(0, 0, 1, {"Site": "A"}, {"Site": "A"}, "item_A")],
            renderers, self.base, "PNG", False, 80, 60,
        )
        worker.renderers[1].render_row = Mock(side_effect=OSError("falha no verso"))
        errors, finished = [], []
        worker.error_occurred.connect(errors.append)
        worker.card_finished.connect(lambda *args: finished.append(args))

        worker.run()

        self.assertEqual(errors, ["falha no verso"])
        self.assertFalse(finished)
        self.assertFalse((self.base / "item_A_pag1.png").exists())
        self.assertFalse((self.base / "item_A_pag2.png").exists())
        self.assertFalse(any(self.base.glob("*.partial.png")))

    def test_existing_blank_back_is_exported_as_second_png(self):
        document = two_page_template()
        document["pages"] = document["pages"][:1]
        document["placeholders"] = ["Site"]
        document = add_blank_back_page(document)

        files = self.produce(
            [{"Site": "A"}], fmt="PNG", template_data=document,
        )

        self.assertEqual([path.name for path in files], ["item_A_pag1.png", "item_A_pag2.png"])
        self.assertEqual(QImage(str(files[1])).pixelColor(120, 90), QColor("#ffffff"))

    def test_duplex_imposition_creates_front_and_back_pngs(self):
        settings = {
            "enabled": True,
            "target_w_mm": 100.0, "target_h_mm": 140.0,
            "sheet_w_mm": 210.0, "sheet_h_mm": 297.0,
            "crop_marks": False, "bleed_margin": False,
        }
        rows = [
            {"Site": "A", "SiteVerso": "A-verso"},
            {"Site": "B", "SiteVerso": "B-verso"},
            {"Site": "C", "SiteVerso": "C-verso"},
        ]

        files = self.produce(
            rows, fmt="PNG", template_data=two_page_template(), imposition=settings,
        )

        self.assertEqual(
            [path.name for path in files],
            ["item_Site_Folha_01_frente.png", "item_Site_Folha_01_verso.png"],
        )
        for path in files:
            image = QImage(str(path))
            self.assertEqual(image.width(), round(210 * 300 / 25.4))
            self.assertEqual(image.height(), round(297 * 300 / 25.4))

    def test_duplex_imposition_pdf_is_one_physical_sheet_with_two_faces(self):
        settings = {
            "enabled": True,
            "target_w_mm": 100.0, "target_h_mm": 140.0,
            "sheet_w_mm": 210.0, "sheet_h_mm": 297.0,
            "crop_marks": False, "bleed_margin": False,
        }
        rows = [
            {"Site": "https://example.com/a", "SiteVerso": "https://example.com/a-verso"},
            {"Site": "https://example.com/b", "SiteVerso": "https://example.com/b-verso"},
        ]

        for grouped in (False, True):
            files = self.produce(
                rows, single=grouped, template_data=two_page_template(), imposition=settings,
            )
            self.assertEqual(len(files), 1)
            pages = PdfReader(files[0]).pages
            self.assertEqual(len(pages), 2)
            urls = [
                [annotation.get_object()["/A"]["/URI"] for annotation in page.get("/Annots", [])]
                for page in pages
            ]
            self.assertEqual(urls[0], [rows[0]["Site"], rows[1]["Site"]])
            self.assertEqual(urls[1], [rows[1]["SiteVerso"], rows[0]["SiteVerso"]])
            for page in pages:
                self.assertAlmostEqual(float(page.mediabox.width) * 25.4 / 72, 210, delta=.18)
                self.assertAlmostEqual(float(page.mediabox.height) * 25.4 / 72, 297, delta=.18)

    def test_sheet_preview_prioritizes_requested_face_and_limits_cache(self):
        output = self.base / "preview"
        settings = {
            "enabled": True, "duplex": True,
            "target_w_mm": 100.0, "target_h_mm": 140.0,
            "sheet_w_mm": 210.0, "sheet_h_mm": 297.0,
            "crop_marks": False, "bleed_margin": False,
        }
        rows = [
            ({"Site": str(i)}, {"Site": str(i), "SiteVerso": f"verso-{i}"})
            for i in range(10)
        ]
        ready, failed = [], []
        worker = SheetPreviewWorker(
            two_page_template(), rows, settings, output, 7,
            first_page=1, first_face=1, cache_limit=3,
        )
        worker.pageReady.connect(lambda *args: ready.append(args))
        worker.pageFailed.connect(lambda *args: failed.append(args))

        worker.run()

        self.assertFalse(failed)
        self.assertEqual(len(ready), 3)
        self.assertEqual(ready[0][0:2], (1, 1))
        self.assertTrue(Path(ready[0][2]).is_file())
        self.assertTrue(all(event[3] == 7 for event in ready))

    def test_protected_sheet_preview_stays_in_memory_and_releases_snapshot(self):
        settings = {
            "enabled": True, "duplex": True,
            "target_w_mm": 100.0, "target_h_mm": 140.0,
            "sheet_w_mm": 210.0, "sheet_h_mm": 297.0,
            "crop_marks": False, "bleed_margin": False,
        }
        rows = [({"Site": "A"}, {"Site": "A", "SiteVerso": "A-verso"})]
        snapshot = Mock()
        ready, failed = [], []
        worker = SheetPreviewWorker(
            two_page_template(), rows, settings, None, 9,
            cache_limit=2, memory_only=True, authorized_snapshot=snapshot,
        )
        worker.pageReady.connect(lambda *args: ready.append(args))
        worker.pageFailed.connect(lambda *args: failed.append(args))

        worker.run()

        self.assertFalse(failed)
        self.assertEqual(len(ready), 2)
        self.assertTrue(all(isinstance(event[2], QImage) for event in ready))
        self.assertEqual(snapshot.close.call_count, 1)
        self.assertFalse(list(self.base.glob("fornax_sheet_preview_*")))

    def test_duplex_landscape_keeps_four_items_and_maps_back_by_rows(self):
        settings = {
            "enabled": True,
            "target_w_mm": 60.0, "target_h_mm": 40.0,
            "sheet_w_mm": 100.0, "sheet_h_mm": 140.0,
            "crop_marks": False, "bleed_margin": False,
        }
        rows = [
            {
                "Site": f"https://example.com/{label}",
                "SiteVerso": f"https://example.com/{label}-verso",
            }
            for label in ("a", "b", "c", "d")
        ]

        files = self.produce(
            rows, template_data=two_page_template(), imposition=settings,
        )

        self.assertEqual(len(files), 1)
        pages = PdfReader(files[0]).pages
        self.assertEqual(len(pages), 2)
        urls = [
            [annotation.get_object()["/A"]["/URI"] for annotation in page.get("/Annots", [])]
            for page in pages
        ]
        self.assertEqual(urls[0], [row["Site"] for row in rows])
        self.assertEqual(
            urls[1],
            [rows[index]["SiteVerso"] for index in (2, 3, 0, 1)],
        )
        self.assertGreater(float(pages[0].mediabox.width), float(pages[0].mediabox.height))

if __name__ == "__main__":
    unittest.main()
