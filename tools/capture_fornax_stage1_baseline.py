"""Captura a referência funcional e de desempenho anterior ao formato .fornax."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import statistics
import sys
import tempfile
import time
import zipfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader

from core.model_document import adapt_model_page, install_model_directory, load_model_document
from features.editor.editor_window import EditorWindow
from features.generator.renderer import renderers_for_document
from features.generator.workers import DirectRenderWorker


FIXTURE = ROOT / "tests" / "fixtures" / "fornax_stage1" / "template_v4.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _measure(function, repetitions: int) -> tuple[object, dict]:
    samples = []
    result = None
    for _ in range(repetitions):
        started = time.perf_counter()
        result = function()
        samples.append((time.perf_counter() - started) * 1000)
    ordered = sorted(samples)
    p95 = ordered[min(len(ordered) - 1, round((len(ordered) - 1) * 0.95))]
    return result, {
        "median_ms": round(statistics.median(samples), 3),
        "p95_ms": round(p95, 3),
        "min_ms": round(min(samples), 3),
        "max_ms": round(max(samples), 3),
        "samples": repetitions,
    }


def _fixture_manifest() -> dict:
    document = load_model_document(FIXTURE)
    assets = []
    for path in sorted((FIXTURE.parent / "assets").iterdir()):
        if not path.is_file():
            continue
        size = QImageReader(str(path)).size()
        assets.append({
            "path": str(path.relative_to(FIXTURE.parent)),
            "bytes": path.stat().st_size,
            "pixels": [size.width(), size.height()],
            "sha256": _sha256(path),
        })
    return {
        "json_bytes": FIXTURE.stat().st_size,
        "json_sha256": _sha256(FIXTURE),
        "pages": len(document["pages"]),
        "canvas_pixels": document["canvas_size"],
        "physical_mm": [document["target_w_mm"], document["target_h_mm"]],
        "placeholders": document["placeholders"],
        "page_counts": [{
            key: len(page.get(key, []))
            for key in ("boxes", "images", "signatures", "shapes")
        } for page in document["pages"]],
        "assets": assets,
    }


def _make_legacy_batch_zip(path: Path, models: int = 100) -> None:
    source = FIXTURE.read_bytes()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for index in range(models):
            archive.writestr(f"modelo-{index:03d}/template_v4.json", source)


def _scan_legacy_batch_zip(path: Path) -> int:
    valid = 0
    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        folders = {name.split("/")[0] for name in names if "/" in name}
        for folder in folders:
            entry = f"{folder}/template_v4.json"
            if entry not in names:
                continue
            json.loads(archive.read(entry).decode("utf-8"))
            valid += 1
    return valid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / ".validation" / "fornax_stage1",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    references = output / "references"
    references.mkdir(parents=True, exist_ok=True)
    QApplication.instance() or QApplication([])

    document, cold_load = _measure(lambda: load_model_document(FIXTURE), 1)
    _, warm_load = _measure(lambda: load_model_document(FIXTURE), 50)
    _, page_switch = _measure(
        lambda: (adapt_model_page(document, "front"), adapt_model_page(document, "back")),
        100,
    )
    editor = EditorWindow()
    _, editor_open = _measure(lambda: editor.load_from_json(FIXTURE), 1)
    QApplication.processEvents()
    editor._last_saved_state = editor.get_current_scene_state()
    editor.close()
    editor.deleteLater()
    QApplication.processEvents()

    row = {
        "Nome": "Ada Lovelace", "Cargo": "Referência",
        "Site": "https://example.invalid/ada", "Foto": "missing-photo",
        "Observacao": "Contrato visual do verso",
        "__use_signature__:sig-stage1-visible": True,
        "__use_signature__:sig-stage1-hidden": False,
    }
    renderers = renderers_for_document(document)
    images, cold_render = _measure(
        lambda: [renderer.render_to_qimage(row, row) for renderer in renderers], 1
    )
    _, warm_render = _measure(
        lambda: [renderer.render_to_qimage(row, row) for renderer in renderers], 30
    )
    pngs = []
    for page_id, image in zip(("front", "back"), images):
        target = references / f"{page_id}.png"
        if not image.save(str(target), "PNG"):
            raise OSError(f"Falha ao salvar {target}")
        pngs.append({
            "path": str(target.relative_to(output)), "sha256": _sha256(target),
            "pixels": [image.width(), image.height()], "bytes": target.stat().st_size,
        })

    batch_output = output / "generated"
    batch_output.mkdir(exist_ok=True)
    tasks = [
        (index, index, 0, {**row, "Nome": f"Pessoa {index}"},
         {**row, "Nome": f"Pessoa {index}"}, f"item-{index:03d}")
        for index in range(100)
    ]
    worker = DirectRenderWorker(
        tasks, renderers, batch_output, "PDF", False, 100.0, 60.0
    )
    failures = []
    worker.error_occurred.connect(failures.append)
    _, generate_100 = _measure(worker.run, 1)
    if failures:
        raise RuntimeError(failures)
    generated_pdfs = sorted(batch_output.glob("*.pdf"))
    pdf_page_counts = [len(PdfReader(path).pages) for path in generated_pdfs]

    with tempfile.TemporaryDirectory(prefix="fornax-stage1-") as temporary:
        archive = Path(temporary) / "legacy-100.zip"
        _make_legacy_batch_zip(archive)
        archive_size = archive.stat().st_size
        found, scan_zip_100 = _measure(lambda: _scan_legacy_batch_zip(archive), 10)
        library = Path(temporary) / "library"
        library.mkdir()

        def install_20_models():
            for index in range(20):
                install_model_directory(FIXTURE.parent, library / f"model-{index:02d}")

        _, install_20 = _measure(install_20_models, 1)
    if found != 100:
        raise AssertionError(f"Pacote sintético retornou {found} modelos")

    rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report = {
        "purpose": "reference-before-fornax-container-and-protection",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "environment": {
            "platform": platform.platform(), "python": platform.python_version(),
            "pyside": __import__("PySide6").__version__,
            "qt_qpa_platform": os.environ.get("QT_QPA_PLATFORM"),
        },
        "fixture": _fixture_manifest(),
        "reference_outputs": {
            "png": pngs,
            "pdf_batch": {
                "files": len(generated_pdfs),
                "pages_per_file": sorted(set(pdf_page_counts)),
                "total_pages": sum(pdf_page_counts),
                "total_bytes": sum(path.stat().st_size for path in generated_pdfs),
                "first_file_sha256": _sha256(generated_pdfs[0]),
            },
        },
        "measurements": {
            "load_cold": cold_load, "load_warm": warm_load,
            "adapt_front_and_back": page_switch,
            "editor_open": editor_open,
            "render_two_pages_cold": cold_render,
            "render_two_pages_warm": warm_render,
            "generate_100_items_200_pdf_pages": generate_100,
            "scan_legacy_zip_100_models": scan_zip_100,
            "install_20_legacy_models": install_20,
            "legacy_zip_100_models_bytes": archive_size,
            "process_max_rss_kib": rss_kib,
        },
        "notes": [
            "Tempos valem para esta máquina e devem ser comparados no mesmo ambiente.",
            "Cold usa uma amostra e registra custo inicial; warm registra múltiplas amostras.",
            "O scan ZIP reproduz descoberta/leitura, não diálogos nem publicação na biblioteca.",
            "Hash de PDF pode variar por metadados; páginas, dimensões e conteúdo também devem ser testados.",
            "ru_maxrss é pico do processo e não representa toda alocação nativa do Qt.",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report_path)


if __name__ == "__main__":
    main()
