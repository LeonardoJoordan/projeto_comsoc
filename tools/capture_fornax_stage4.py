"""Comparação local dos três modos; somente fixture sintética e diretório de validação."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import sys
import tempfile
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader
from tools.capture_fornax_stage1_baseline import FIXTURE, _measure
from core.model_document import load_model_document
from core.fornax_container import PUBLIC_MODE, SIGNATURES_MODE, FULL_MODE, save_public_fornax, save_protected_fornax, open_public_fornax, unlock_fornax
from core.fornax_session import FornaxSessionManager
from features.editor.editor_window import EditorWindow
from features.generator.renderer import renderers_for_document
from features.generator.workers import DirectRenderWorker
from features.preview.sheet_preview_worker import SheetPreviewWorker

PASSWORD = 'Synthetic benchmark password 2026'
ROW = {'Nome': 'Ada Lovelace', 'Cargo': 'Referência', 'Site': 'https://example.invalid/ada',
       'Foto': 'missing-photo', 'Observacao': 'Contrato visual do verso',
       '__use_signature__:sig-stage1-visible': True, '__use_signature__:sig-stage1-hidden': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / '.validation/fornax_stage4/modern')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    original = load_model_document(FIXTURE)
    document = deepcopy(original)
    for page in document['pages']:
        removed = {item['object_id'] for item in page['images'] if item.get('path') == 'assets/intentionally-missing.png'}
        page['images'] = [item for item in page['images'] if item['object_id'] not in removed]
        page['layer_order'] = [key for key in page['layer_order'] if key not in removed]
    report = {'environment': {'platform': platform.platform(), 'python': platform.python_version(),
                              'pyside': __import__('PySide6').__version__, 'qt': os.environ.get('QT_QPA_PLATFORM')},
              'captured_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'modes': {},
              'fixture_sha256': hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
              'notes': ['Asset ausente invisível removido para permitir empacotamento válido.',
                        'Modo público compara contra referência sem assinaturas; demais modos preservam ambas.',
                        'Tempos locais sintéticos; cold inclui uma amostra, não é benchmark de hardware modesto.',
                        'RSS é pico acumulado do processo; não somar nem atribuir integralmente a cada modo.']}
    for mode in (PUBLIC_MODE, SIGNATURES_MODE, FULL_MODE):
        source = deepcopy(document)
        if mode == PUBLIC_MODE:
            for page in source['pages']:
                removed = {item['object_id'] for item in page['signatures']}
                page['signatures'] = []
                page['layer_order'] = [key for key in page['layer_order'] if key not in removed]
        reference = renderers_for_document(source)
        expected = [renderer.render_to_qimage(ROW, ROW) for renderer in reference]
        if mode != PUBLIC_MODE:
            assert expected == [r.render_to_qimage(ROW, ROW) for r in renderers_for_document(original)]
        target = output / f'{mode}.fornax'
        if target.exists():
            raise RuntimeError(f'Use um diretório novo: {target}')
        create = (lambda: save_public_fornax(source, target, source_dir=FIXTURE.parent)) if mode == PUBLIC_MODE else (
            lambda: save_protected_fornax(source, target, PASSWORD, mode=mode, source_dir=FIXTURE.parent))
        _, create_time = _measure(create, 1)
        opened, unlock_time = _measure(lambda: open_public_fornax(target) if mode == PUBLIC_MODE else unlock_fornax(target, PASSWORD), 5)
        renderers = renderers_for_document(opened.document(), asset_provider=opened.asset)
        images, cold_render = _measure(lambda: [r.render_to_qimage(ROW, ROW) for r in renderers], 1)
        _, warm_render = _measure(lambda: [r.render_to_qimage(ROW, ROW) for r in renderers], 30)
        assert images == expected, f'Paridade visual falhou: {mode}'
        hashes = []
        for index, image in enumerate(images):
            path = output / f'{mode}-page{index+1}.png'
            assert image.save(str(path))
            hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
        sessions = FornaxSessionManager()
        status = sessions.select(target) if mode == PUBLIC_MODE else sessions.unlock(target, PASSWORD)
        editor = EditorWindow()
        _, editor_time = _measure(lambda: editor.load_from_fornax(sessions.document(), path=target, mode=mode,
                                 model_id=status.descriptor.model_id, asset_provider=sessions.asset, session_manager=sessions), 1)
        app.processEvents()
        editor._last_saved_state = editor.get_current_scene_state()
        editor._last_saved_document_state = editor._capture_document_history_state()
        editor.close()
        app.processEvents()
        _, save_time = _measure(lambda: sessions.save(sessions.document()), 3)
        batch = output / f'pdf-{mode}'
        batch.mkdir()
        tasks = [(i, i, 0, {**ROW, 'Nome': f'Pessoa {i}'}, {**ROW, 'Nome': f'Pessoa {i}'}, f'item-{i:03d}') for i in range(100)]
        worker = DirectRenderWorker(tasks, renderers, batch, 'PDF', False, 100, 60, secure_output=mode != PUBLIC_MODE)
        errors = []
        worker.error_occurred.connect(errors.append)
        _, generate_time = _measure(worker.run, 1)
        assert not errors, errors
        pdfs = list(batch.glob('*.pdf'))
        assert len(pdfs) == 100 and all(len(PdfReader(p).pages) == 2 for p in pdfs)
        rows = [{**ROW, 'Nome': f'Pessoa {i}'} for i in range(500)]
        settings = {'enabled': True, 'sheet_w_mm': 210, 'sheet_h_mm': 297, 'target_w_mm': 100,
                    'target_h_mm': 60, 'crop_marks': False, 'bleed_margin': False, 'duplex': True}
        snapshot = sessions.borrow_job()
        preview = SheetPreviewWorker(snapshot.document(), list(zip(rows, rows)), settings, None, 1, cache_limit=4,
                                     memory_only=True, asset_provider=snapshot.asset, authorized_snapshot=snapshot)
        previews = []
        preview.pageReady.connect(lambda *data: previews.append(data))
        preview.pageFailed.connect(lambda *data: errors.append(data))
        _, sheet_time = _measure(preview.run, 1)
        assert not errors and previews, errors
        report['modes'][mode] = {'create': create_time, 'open_or_unlock': unlock_time, 'editor_load': editor_time,
                                  'render_cold': cold_render, 'render_warm': warm_render, 'save_authorized': save_time,
                                  'generate_100_items_200_pages': generate_time, 'preview_500_rows_4_faces': sheet_time,
                                  'preview_faces': len(previews), 'package_bytes': target.stat().st_size,
                                  'png_sha256': hashes, 'pdf_files': len(pdfs), 'pdf_pages': 200,
                                  'process_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        sessions.close()
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(output / 'report.json')


if __name__ == '__main__':
    main()
