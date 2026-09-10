"""Objetos estáveis da cena e reprodução gráfica sem acessar QTextDocument."""
from PySide6.QtCore import QAbstractListModel, QSortFilterProxyModel, QModelIndex, QObject, Property, Signal, Qt, QRectF
from PySide6.QtGui import QPicture, QPainter
from PySide6.QtQuick import QQuickPaintedItem
from core.document_layers import layer_entries
from features.editor_qml.layer_paint_cache import LayerPaintCache
from copy import deepcopy
from pathlib import Path
import html


class LayerData(QObject):
    viewChanged = Signal()
    pictureChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view = {}
        self.picture = QPicture()
        self._bounds = QRectF()

    @Property('QVariantMap', notify=viewChanged)
    def view(self):
        return self._view

    @Property('QVariantMap', notify=viewChanged)
    def uiView(self):
        return {key: value for key, value in self._view.items() if key != 'html'}

    @Property(QRectF, notify=pictureChanged)
    def bounds(self):
        return self._bounds

    def refresh(self, view, picture):
        if self._view != view:
            self._view = view
            self.viewChanged.emit()
        if self.picture is not picture:
            self.picture = picture
            self._bounds = QRectF(picture.boundingRect()).adjusted(-2, -2, 2, 2)
            self.pictureChanged.emit()


class LayerSceneModel(QAbstractListModel):
    ROLE = Qt.UserRole + 1
    ORDER_ROLE = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache = LayerPaintCache()
        self.keys = []
        self.objects = {}
        self.items = {}
        self._sources = {}
        self._base = None
        self.reverse = QSortFilterProxyModel(self)
        self.reverse.setSourceModel(self)
        self.reverse.setSortRole(self.ORDER_ROLE)
        self.reverse.sort(0, Qt.DescendingOrder)

    def invalidate(self):
        self._sources.clear()
        self.cache._entries.clear()

    def invalidate_asset(self, path):
        path = str(Path(path).resolve())
        self.cache._renderer._image_cache.pop(path, None)
        for key, (_, item) in self.items.items():
            if item.get('path') == path:
                self._sources.pop(key, None)
                self.cache._entries.pop(key, None)

    @staticmethod
    def _paint_input(kind, item):
        ignored = {'x', 'y', 'locked', 'custom_name', 'layer_id', 'z_value',
                   'has_link', 'link_key', 'object_id', 'visible'}
        return kind, {k: v for k, v in item.items() if k not in ignored}

    def roleNames(self):
        return {self.ROLE: b'layerData', self.ORDER_ROLE: b'layerOrder'}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.keys)

    def data(self, index, role=Qt.DisplayRole):
        if role == self.ORDER_ROLE and index.isValid():
            return index.row()
        if role == self.ROLE and index.isValid() and 0 <= index.row() < len(self.keys):
            return self.objects[self.keys[index.row()]]

    def sync(self, document, views, base=None):
        previous_order = list(self.keys)
        if base != self._base:
            self.invalidate()
            self._base = base
        entries = list(layer_entries(document))
        wanted = {key for key, _, _ in entries}
        for index in reversed(range(len(self.keys))):
            key = self.keys[index]
            if key not in wanted:
                self.beginRemoveRows(QModelIndex(), index, index)
                self.keys.pop(index)
                obj = self.objects.pop(key)
                self._sources.pop(key, None)
                self.items.pop(key, None)
                self.endRemoveRows()
                obj.deleteLater()
        by_key = {view['key']: view for view in views}
        for index, (key, kind, item) in enumerate(entries):
            old = self._sources.get(key)
            if old is not None and old == (kind, item):
                picture = self.objects[key].picture
            else:
                resolved = deepcopy(item)
                if base is not None and resolved.get('path'):
                    resolved['path'] = str((Path(base)/resolved['path']).resolve())
                if kind == 'text':
                    resolved.setdefault('html', '<p>'+html.escape(resolved.get('id', 'Texto'))+'</p>')
                previous = self.items.get(key)
                if old is not None and previous and self._paint_input(*previous) == self._paint_input(kind, resolved):
                    picture = self.objects[key].picture
                else:
                    picture = self.cache.picture(key, kind, resolved)
                self.items[key] = (kind, resolved)
                self._sources[key] = (kind, deepcopy(item))
            if key not in self.objects:
                obj = LayerData(self)
                obj.refresh(by_key[key], picture)
                self.beginInsertRows(QModelIndex(), index, index)
                self.keys.insert(index, key)
                self.objects[key] = obj
                self.endInsertRows()
            else:
                previous = self.keys.index(key)
                if previous != index:
                    self.beginMoveRows(QModelIndex(), previous, previous, QModelIndex(), index)
                    self.keys.insert(index, self.keys.pop(previous))
                    self.endMoveRows()
                self.objects[key].refresh(by_key[key], picture)
        self.cache.retain(wanted)
        if self.keys != previous_order and self.keys:
            self.dataChanged.emit(self.index(0), self.index(len(self.keys)-1), [self.ORDER_ROLE])


class CanvasLayer(QQuickPaintedItem):
    sourceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = None
        self._picture = QPicture()
        self._bounds = QRectF()
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setAntialiasing(True)

    @Property(QObject, notify=sourceChanged)
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if self._source is value:
            return
        if self._source is not None:
            self._source.pictureChanged.disconnect(self._refresh)
        self._source = value
        if value is not None:
            value.pictureChanged.connect(self._refresh)
        self._refresh()
        self.sourceChanged.emit()

    def _refresh(self):
        self._picture = self._source.picture if self._source else QPicture()
        self._bounds = self._source.bounds if self._source else QRectF()
        self.update()

    def paint(self, painter):
        # Apenas cópias de comandos/bounds preparadas na GUI, inclusive no render loop threaded.
        bounds = self._bounds
        if bounds.width() <= 0 or bounds.height() <= 0:
            return
        if self.width() != bounds.width() or self.height() != bounds.height():
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.scale(self.width()/bounds.width(), self.height()/bounds.height())
        painter.translate(-bounds.x(), -bounds.y())
        painter.drawPicture(0, 0, self._picture)
