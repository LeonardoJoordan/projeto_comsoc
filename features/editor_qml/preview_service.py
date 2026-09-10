"""Prévia assíncrona: um trabalho ativo e somente o pedido mais recente na fila."""
from copy import deepcopy
from PySide6.QtCore import QObject, Signal, Slot, QRunnable, QThreadPool
from features.generator.renderer import NativeRenderer
from core.document_layers import GROUPS


def paint_preview(data, editing_key=""):
    if not editing_key:
        return NativeRenderer(data).render_preview_image(max_side=1600), None
    order = data["layer_order"]
    position = order.index(editing_key)

    def subset(keys):
        result = {**data, "layer_order": keys}
        for group in GROUPS.values():
            result[group] = [item for item in data.get(group, []) if item["object_id"] in keys]
        return result

    lower = NativeRenderer(subset(order[:position])).render_preview_image(max_side=1600)
    upper = NativeRenderer(subset(order[position+1:])).render_preview_image(max_side=1600, transparent=True)
    return lower, upper


class Completion(QObject):
    done = Signal(int, object, str)


class PreviewTask(QRunnable):
    def __init__(self, serial, data, editing_key, completion):
        super().__init__()
        self.serial, self.data, self.editing_key = serial, data, editing_key
        self.completion = completion

    def run(self):
        try:
            self.completion.done.emit(self.serial, paint_preview(self.data, self.editing_key), "")
        except Exception as exc:
            self.completion.done.emit(self.serial, None, str(exc))


class PreviewService(QObject):
    ready = Signal(int, object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.completion = Completion(self)
        self.completion.done.connect(self._done)
        self.running = False
        self.pending = None
        self.closed = False

    def request(self, serial, data, editing_key):
        if self.closed:
            return
        self.pending = (serial, deepcopy(data), editing_key)
        if not self.running:
            self._start()

    def _start(self):
        args, self.pending = self.pending, None
        self.running = True
        self.pool.start(PreviewTask(*args, self.completion))

    @Slot(int, object, str)
    def _done(self, serial, result, error):
        self.running = False
        if not self.closed:
            self.ready.emit(serial, result, error)
            if self.pending:
                self._start()

    def close(self):
        self.closed = True
        self.pending = None
        self.pool.waitForDone()
