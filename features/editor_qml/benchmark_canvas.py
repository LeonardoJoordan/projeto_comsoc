"""Benchmark isolado: atualizações programáticas e ciclos gráficos observados.

Executar cada editor em processo separado. Nunca grava nos modelos de origem.
As métricas de apresentação são proxies do Qt, não latência física de monitor.
"""
import argparse
from copy import deepcopy
import faulthandler
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import statistics
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from PySide6 import __version__ as qt_binding_version
from PySide6.QtCore import QObject, QEvent, QTimer, qVersion
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor, QPainter
from core.template_manager import slugify_model_name


def summary(values):
    values = sorted(values)
    return dict(samples=len(values), median_ms=round(statistics.median(values), 3),
                p95_ms=round(values[max(0, math.ceil(len(values)*.95)-1)], 3),
                max_ms=round(max(values), 3)) if values else dict(samples=0)


def synthetic(folder):
    folder.mkdir(parents=True)
    image = QImage(2400, 3300, QImage.Format_RGB32)
    image.fill(QColor('#f6f3ec'))
    painter = QPainter(image)
    for y in range(0, 3300, 50):
        painter.fillRect(0, y, 2400, 3, QColor('#cbd5e1'))
    painter.end()
    image.save(str(folder/'background.png'))
    data = dict(name='Benchmark', canvas_size=dict(w=2400, h=3300), target_w_mm=203.2,
                target_h_mm=279.4, background_path='background.png', images=[], signatures=[],
                boxes=[], placeholders=[], guidelines=[])
    for index in range(150):
        text = ('Texto de desempenho com acentuação e formatação. ' * (100 if index == 0 else 4))
        data['boxes'].append(dict(id=f'Texto {index}', x=100+(index%5)*440,
                                 y=100+(index//5)*100, w=400, h=90,
                                 html=f'<p><b>{index}</b> {text}</p>', font_family='DejaVu Sans',
                                 font_size=14, keep_proportion=False))
    path = folder/'template_v3.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    return path


class Run(QObject):
    def __init__(self, app, args, path, data):
        super().__init__()
        self.app, self.args, self.path, self.data = app, args, path, data
        self.result = dict(editor=args.editor, model=args.model or 'synthetic', platform=platform.platform(),
                           cpu_count=os.cpu_count(), render_loop=os.environ.get('QSG_RENDER_LOOP', 'default'),
                           qt=qVersion(), pyside=qt_binding_version, qpa=app.platformName(),
                           screen_hz=app.primaryScreen().refreshRate(),
                           canvas=data['canvas_size'], objects={g:len(data.get(g, [])) for g in
                           ('boxes', 'images', 'signatures', 'shapes')}, has_background=bool(data.get('background_path')),
                           model_directory_bytes=sum(p.stat().st_size for p in path.parent.rglob('*') if p.is_file()))
        self.phase = None
        self.pending = None
        self.samples = {}
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.window = None
        QTimer.singleShot(0, self.open)

    def open(self):
        start = time.perf_counter()
        if self.args.editor == 'qml':
            from features.editor_qml.session import EditorSession
            self.session = EditorSession(self.path)
            self.window = self.session.window
            self.bridge = self.session.bridge
            self.key = self.bridge._data['boxes'][0]['object_id']
            self.bridge.select(self.key)
            self.bridge.setValue('locked', False)
            self.bridge.setValue('keep_proportion', False)
            self.initial = dict(self.bridge.state['selected'])
            self.window.frameSwapped.connect(self.present)
            self.result['presentation_proxy'] = 'frameSwapped recebido no loop da GUI'
        else:
            from features.editor.editor_window import EditorWindow
            from features.editor.canvas_items import DesignerBox
            self.library_patch = patch('features.editor.editor_window.get_models_dir', return_value=self.path.parent.parent)
            self.library_patch.start()
            self.window = EditorWindow()
            self.window.load_from_json(str(self.path))
            self.window.resize(1500, 930)
            self.window.show()
            boxes = [o for o in self.window.scene.items() if isinstance(o, DesignerBox)]
            target = self.data['boxes'][0]
            self.item = min(boxes, key=lambda o: abs(o.pos().x()-target.get('x', 0))+abs(o.pos().y()-target.get('y', 0)))
            self.item.setSelected(True)
            from PySide6.QtWidgets import QGraphicsItem
            self.item.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.item.keep_proportion = False
            self.initial = dict(x=self.item.pos().x(), y=self.item.pos().y(), w=self.item.rect().width(), h=self.item.rect().height())
            self.window.view.viewport().installEventFilter(self)
            self.result['presentation_proxy'] = 'callback após evento Paint do viewport Widgets'
            self.result['opened_canvas'] = self.window.get_current_scene_state()['canvas_size']
        self.result['open_api_ms'] = round((time.perf_counter()-start)*1000, 3)
        self.result['window_size'] = [self.window.width(), self.window.height()]
        self.result['target_adjustments'] = 'Texto escolhido desbloqueado e proporção livre nas cópias de ambos os editores'
        self.window.requestActivate() if self.args.editor == 'qml' else self.window.activateWindow()
        QTimer.singleShot(400, lambda: self.start_phase('move'))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Paint:
            QTimer.singleShot(0, self.present)
        return False

    def present(self):
        if self.phase and self.pending is not None:
            self.samples[self.phase]['presentation_proxy'].append((time.perf_counter()-self.pending)*1000)
            self.pending = None

    def start_phase(self, phase):
        self.phase, self.index = phase, 0
        self.samples[phase] = dict(api=[], presentation_proxy=[], delivery_intervals=[])
        self.last_tick = None
        if self.args.editor == 'qml':
            if not self.bridge.beginTransform(self.key, phase == 'resize'):
                raise RuntimeError('O benchmark não iniciou o gesto')
            self.before_recordings = self.bridge.canvasLayers.cache.recordings
        self.timer.start()

    def tick(self):
        if self.index >= self.args.samples:
            self.timer.stop()
            QTimer.singleShot(100, self.finish_phase)
            return
        start = time.perf_counter()
        if self.last_tick is not None:
            self.samples[self.phase]['delivery_intervals'].append((start-self.last_tick)*1000)
        self.last_tick = start
        if self.pending is None:
            self.pending = start
        dx = math.sin(self.index/10)*80
        dy = math.cos(self.index/10)*40
        if self.args.editor == 'qml':
            self.bridge.updateTransform(dx, dy)
        elif self.phase == 'move':
            self.item.setPos(self.initial['x']+dx, self.initial['y']+dy)
        else:
            self.item.resize_from_handle(self.initial['w']+dx, self.initial['h']+dy)
        self.samples[self.phase]['api'].append((time.perf_counter()-start)*1000)
        self.index += 1

    def finish_phase(self):
        phase, self.phase = self.phase, None
        self.pending = None
        self.result[phase] = {name:summary(values) for name, values in self.samples[phase].items()}
        start = time.perf_counter()
        if self.args.editor == 'qml':
            self.bridge.finishTransform()
            self.result[phase]['recordings'] = self.bridge.canvasLayers.cache.recordings-self.before_recordings
        else:
            self.window.save_snapshot()
        self.result[phase]['commit_ms'] = round((time.perf_counter()-start)*1000, 3)
        if phase == 'move':
            QTimer.singleShot(100, lambda: self.start_phase('resize'))
        else:
            self.finish()

    def finish(self):
        self.result['peak_rss_mib'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, 1)
        Path(self.args.output).write_text(json.dumps(self.result, indent=2, ensure_ascii=False))
        if self.args.editor == 'qml':
            self.bridge._saved = deepcopy(self.bridge._data)
            self.session.close()
        else:
            self.window._last_saved_state = self.window.get_current_scene_state()
            self.window.close()
            self.library_patch.stop()
        self.app.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--editor', choices=['qml', 'legacy'], required=True)
    parser.add_argument('--model', help='Sem este argumento, usa o cenário sintético pesado.')
    parser.add_argument('--samples', type=int, default=90)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.samples < 2:
        parser.error('--samples deve ser pelo menos 2')
    faulthandler.enable()
    faulthandler.dump_traceback_later(60, exit=True)
    app = QApplication([])
    def failed(kind, value, traceback):
        sys.__excepthook__(kind, value, traceback)
        app.exit(1)
    sys.excepthook = failed
    with tempfile.TemporaryDirectory(prefix='comsoc-benchmark-') as temp:
        original_hashes = {}
        if args.model:
            source = Path(args.model).resolve()
            data = json.loads(source.read_text())
            original_hashes = {p:hashlib.sha256(p.read_bytes()).digest() for p in source.parent.rglob('*') if p.is_file()}
            folder = Path(temp)/slugify_model_name(data.get('name', source.parent.name))
            shutil.copytree(source.parent, folder)
            path = folder/source.name
        else:
            path = synthetic(Path(temp)/'benchmark')
            data = json.loads(path.read_text())
        run = Run(app, args, path, data)
        code = app.exec()
        if code:
            raise SystemExit(code)
        assert all(hashlib.sha256(p.read_bytes()).digest() == value for p, value in original_hashes.items())
        print(args.output, flush=True)
    faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
