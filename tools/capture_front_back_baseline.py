"""Captura evidências locais anteriores ao suporte a frente e verso."""

import argparse
import gc
import hashlib
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QMimeData
from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from pypdf import PdfReader

from features.editor.canvas_items import DesignerBox
from features.editor.editor_window import EditorWindow
from features.generator.renderer import NativeRenderer
from features.generator.workers import DirectRenderWorker
from features.spreadsheet.table_panel import RichTableWidget


FIXTURE = ROOT / "tests" / "fixtures" / "front_back_baseline" / "template_v3.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def model_manifest(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assets = []
    for asset in sorted((path.parent / "assets").glob("**/*")):
        if not asset.is_file():
            continue
        reader = QImageReader(str(asset))
        size = reader.size()
        assets.append({
            "relative_path": str(asset.relative_to(path.parent)),
            "bytes": asset.stat().st_size,
            "image_px": [size.width(), size.height()],
            "sha256": sha256(asset),
        })
    return {
        "name": data.get("name"),
        "json_sha256": sha256(path),
        "canvas_px": data.get("canvas_size"),
        "physical_mm": [data.get("target_w_mm"), data.get("target_h_mm")],
        "placeholders": data.get("placeholders", []),
        "counts": {key: len(data.get(key, [])) for key in ("boxes", "images", "signatures", "shapes")},
        "active_links": sum(
            bool(item.get("has_link"))
            for key in ("boxes", "images", "shapes") for item in data.get(key, [])
        ),
        "assets": assets,
    }


def timed(callable_, repetitions=1):
    samples = []
    result = None
    for _ in range(repetitions):
        started = time.perf_counter()
        result = callable_()
        samples.append((time.perf_counter() - started) * 1000)
    return result, {"median_ms": round(percentile(samples, .5), 3), "p95_ms": round(percentile(samples, .95), 3), "samples": len(samples)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / ".validation" / "front_back_baseline")
    parser.add_argument("--real-models", type=Path, default=ROOT / "models")
    args = parser.parse_args()
    output = args.output.resolve()
    references = output / "references"
    real_copies = output / "real-model-copies"
    references.mkdir(parents=True, exist_ok=True)
    real_copies.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    template = json.loads(FIXTURE.read_text(encoding="utf-8"))
    template["__model_dir"] = str(FIXTURE.parent)
    row = {"Nome": "Ada Lovelace", "Cargo": "Referência", "Site": "https://example.com", "__use_signature__": True}
    renderer = NativeRenderer(template)

    image, first_preview = timed(lambda: renderer.render_to_qimage(row, row), 1)
    png_path = references / "fixture.png"
    if not image.save(str(png_path), "PNG"):
        raise OSError(f"Não foi possível gravar {png_path}")
    _, warm_preview = timed(lambda: renderer.render_to_qimage(row, row), 30)

    pdf_dir = references / "pdf"
    pdf_dir.mkdir(exist_ok=True)
    worker = DirectRenderWorker(
        [(0, 0, 0, row, row, "fixture")],
        renderer, pdf_dir, "PDF", False, 80.0, 50.0,
    )
    errors = []
    worker.error_occurred.connect(errors.append)
    _, pdf_time = timed(worker.run)
    if errors:
        raise RuntimeError(errors)
    pdf_path = pdf_dir / "fixture.pdf"
    pdf = PdfReader(pdf_path)

    editor = EditorWindow()
    _, editor_open = timed(lambda: editor.load_from_json(FIXTURE))
    app.processEvents()
    box = next(item for item in editor.scene.items() if isinstance(item, DesignerBox))
    def move_box():
        for index in range(200):
            box.setPos(28 + index % 9, 45 + index % 7)
        app.processEvents()
    _, scene_moves = timed(move_box, 5)
    def edit_text():
        for index in range(100):
            box.text_item.setHtml(f"<p>Pessoa {index}</p>")
        app.processEvents()
    _, text_edits = timed(edit_text, 5)
    editor._last_saved_state = editor.get_current_scene_state()
    editor.close()
    editor.deleteLater()
    app.processEvents()

    table = RichTableWidget(1, 4)
    for column, header in enumerate(("Cópias", "Nome", "Cargo", "Site")):
        table.setHorizontalHeaderItem(column, QTableWidgetItem(header))
    table.setCurrentCell(0, 1)
    mime = QMimeData()
    mime.setText("\n".join(f"Pessoa {index}\tCargo {index}\thttps://example.com/{index}" for index in range(500)))
    QApplication.clipboard().setMimeData(mime)
    _, paste_500 = timed(table._paste_from_clipboard)
    app.processEvents()
    def change_row():
        for index in range(500):
            table.setCurrentCell(index, 1)
        app.processEvents()
    _, row_navigation = timed(change_row, 5)
    table.deleteLater()

    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    def render_batch():
        for index in range(100):
            values = {**row, "Nome": f"Pessoa {index}", "Cargo": f"Cargo {index}"}
            renderer.render_to_qimage(values, values, out_links=[])
    _, batch_100 = timed(render_batch)
    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    real_models = []
    if args.real_models.is_dir():
        for source_json in sorted(args.real_models.glob("*/template_v3.json")):
            target = real_copies / source_json.parent.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source_json.parent, target)
            real_models.append(model_manifest(target / "template_v3.json"))

    page = pdf.pages[0]
    annotations = page.get("/Annots", [])
    if hasattr(annotations, "get_object"):
        annotations = annotations.get_object()
    report = {
        "purpose": "baseline-before-front-back-support",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "platform": {"system": platform.platform(), "python": sys.version.split()[0], "qt": __import__("PySide6").__version__},
        "git": {
            "branch": subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, text=True, capture_output=True).stdout.strip(),
            "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True).stdout.strip(),
        },
        "fixture": model_manifest(FIXTURE),
        "reference_outputs": {
            "png": {"path": str(png_path.relative_to(output)), "sha256": sha256(png_path), "px": [image.width(), image.height()]},
            "pdf": {
                "path": str(pdf_path.relative_to(output)), "sha256": sha256(pdf_path), "pages": len(pdf.pages),
                "page_mm": [round(float(page.mediabox.width) * 25.4 / 72, 3), round(float(page.mediabox.height) * 25.4 / 72, 3)],
                "links": len(annotations),
            },
        },
        "measurements": {
            "preview_first": first_preview, "preview_warm": warm_preview, "editor_open": editor_open,
            "scene_200_moves": scene_moves, "text_100_edits": text_edits,
            "paste_500_rows": paste_500, "navigate_500_rows": row_navigation,
            "render_100_documents": batch_100,
            "process_max_rss_kib": rss_after,
            "max_rss_growth_kib": max(0, rss_after - rss_before),
        },
        "real_model_copies": real_models,
        "notes": [
            "Tempos são comparativos desta máquina; não são limites universais.",
            "Hash de PDF pode conter metadados variáveis; valide páginas, medidas e links além do hash.",
            "ru_maxrss não mede com precisão toda memória nativa do Qt e registra apenas o pico do processo.",
            "Movimentos de cena são programáticos; a fluidez visual ainda exige teste manual nativo.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output / "report.json")
    QApplication.clipboard().clear()
    del page, pdf, worker, table, editor, box, move_box, edit_text, change_row, renderer, image
    gc.collect()
    app.processEvents()


if __name__ == "__main__":
    main()
