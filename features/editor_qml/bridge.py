"""Adaptador do frontend QML para o formato v3 e serviços existentes.

Não importa o editor Widgets; compartilha ordenação e layout com o renderer.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
import math
from pathlib import Path
import shutil

from PySide6.QtCore import QObject, Property, Signal, Slot, QSaveFile, QIODevice, QTimer, Qt
from PySide6.QtGui import QColor, QImage, QTextDocument, QTextCursor, QTextCharFormat, QTextBlockFormat, QFont
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from core.history_manager import HistoryManager
from core.paths import get_models_dir
from core.template_manager import slugify_model_name
from core.document_layers import upgrade_layers, layer_entries
from core.text_layout import build_document, ALIGNMENTS, variables_in_html
from core.font_utils import missing_template_fonts
from features.editor_qml.preview_service import PreviewService, paint_preview
from uuid import uuid4
from features.editor_qml.canvas_layers import LayerSceneModel


class PreviewProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self.image = QImage(1, 1, QImage.Format_ARGB32)
        self.image.fill(QColor("white"))
        self.above = QImage(self.image)
        self.above.fill(Qt.transparent)

    def requestImage(self, _id, size, requested_size):
        image = self.above if _id.startswith("above/") else self.image
        size.setWidth(image.width())
        size.setHeight(image.height())
        return image


class EditorBridge(QObject):
    changed = Signal()
    documentChanged = Signal()
    previewChanged = Signal()
    error = Signal(str)
    editingChanged = Signal()
    textFormatChanged = Signal()
    modelSaved = Signal(str, list, str)
    transformChanged = Signal()
    GROUPS = {"text": "boxes", "image": "images", "signature": "signatures", "shape": "shapes"}

    def __init__(self, provider=None):
        super().__init__()
        self.provider = provider or PreviewProvider()
        self.history = HistoryManager(60)
        self._canvas_layers = LayerSceneModel(self)
        self._canvas_attached = False
        self._transform = None
        self._guide_transform = None
        self._path = None
        self.library_mode = False
        self._disk_hash = None
        self._selected = ""
        self._revision = 0
        self._message = ""
        self._editing_key = ""
        self._text_editor = None
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self.requestPreview)
        self._preview_serial = 0
        self._preview_busy = False
        self._preview_service = PreviewService(self)
        self._preview_service.ready.connect(self._preview_ready)
        self._missing_fonts = []
        self._views_cache = None
        self._item_views = {}
        self._text_metadata = {}
        self._format_cache = {}
        self._font_signature = None
        self._data = self.blank()
        self._saved = deepcopy(self._data)
        self.history.push(deepcopy(self._data))

    @staticmethod
    def blank():
        return {"name": "Novo modelo", "canvas_size": {"w": 1000, "h": 700}, "layer_order": [],
                "target_w_mm": 84.67, "target_h_mm": 59.27,
                "boxes": [], "images": [], "signatures": [], "shapes": [], "placeholders": [],
                "background_path": None, "guidelines": []}

    @Property(QObject, constant=True)
    def canvasLayers(self):
        return self._canvas_layers

    @Property(QObject, constant=True)
    def layerList(self):
        return self._canvas_layers.reverse

    @Slot()
    def attachCanvas(self):
        self._canvas_attached = True
        self._render_timer.stop()
        self._sync_canvas()

    def _sync_canvas(self):
        base = self._path.parent if self._path else Path.cwd()
        self._canvas_layers.sync(self._data, self._views(), base=base)

    @Property(bool, notify=transformChanged)
    def transforming(self):
        return self._transform is not None or self._guide_transform is not None

    @Property('QVariantMap', notify=transformChanged)
    def guideGesture(self):
        return dict(self._guide_transform or {})

    @Slot(int, result=bool)
    def beginGuideTransform(self, index):
        self.cancelTransform()
        self.finishTextSession()
        guides = self._data.get('guidelines', [])
        if (self._data.get('guidelines_locked', False) or not self._data.get('guidelines_visible', True)
                or not 0 <= index < len(guides) or not guides[index].get('visible', True)):
            return False
        self._guide_transform = dict(index=index, position=guides[index]['pos'])
        self.transformChanged.emit()
        return True

    @Slot(float)
    def updateGuideTransform(self, position):
        if self._guide_transform is not None and math.isfinite(position):
            self._guide_transform['position'] = round(position, 2)
            self.transformChanged.emit()

    @Slot()
    def finishGuideTransform(self):
        gesture, self._guide_transform = self._guide_transform, None
        if gesture is not None:
            self.transformChanged.emit()
            self.moveGuide(gesture['index'], gesture['position'])

    @Slot(str, bool, result=bool)
    def beginTransform(self, key, resize):
        self.cancelTransform()
        self.finishTextSession()
        self.select(key)
        layer = self._canvas_layers.objects.get(key)
        if layer is None or layer.view.get('locked') or not layer.view.get('visible'):
            return False
        self._transform = dict(key=key, resize=resize, view=dict(layer.view),
                               picture=layer.picture, cache=self._canvas_layers.cache._entries[key],
                               geometry=None)
        self.transformChanged.emit()
        return True

    @Slot(float, float)
    def updateTransform(self, dx, dy):
        gesture = self._transform
        if gesture is None or not all(map(math.isfinite, (dx, dy))):
            return
        original = gesture['view']
        view = dict(original)
        key = gesture['key']
        layer = self._canvas_layers.objects[key]
        picture = gesture['picture']
        if gesture['resize']:
            angle = math.radians(original['rotation'])
            c, s = math.cos(angle), math.sin(angle)
            local_x, local_y = c*dx+s*dy, -s*dx+c*dy
            w = max(1, original['w']+local_x)
            h = max(1, original['h']+local_y)
            if original['keep_proportion'] or original.get('shape_type') in ('square', 'circle'):
                w = max(w, original['w']/max(original['h'], 1))
                h = w * original['h']/max(original['w'], 1)
            w, h = round(w, 2), round(h, 2)
            dw, dh = w-original['w'], h-original['h']
            # Manter fixo o canto superior esquerdo no espaço girado da página.
            view.update(w=w, h=h, x=round(original['x']+((c-1)*dw-s*dh)/2, 2),
                        y=round(original['y']+(s*dw+(c-1)*dh)/2, 2))
            kind, raw = self._canvas_layers.items[key]
            item = dict(raw)
            wk, hk = ('w', 'h') if kind == 'text' else ('width', 'height')
            item.update({wk: w, hk: h})
            picture = self._canvas_layers.cache.picture(key, kind, item)
        else:
            view.update(x=round(original['x']+dx, 2), y=round(original['y']+dy, 2))
        gesture['geometry'] = {field: view[field] for field in ('x', 'y', 'w', 'h')}
        layer.refresh(view, picture)

    @Slot()
    def cancelTransform(self):
        if self._guide_transform is not None:
            self._guide_transform = None
            self.transformChanged.emit()
        gesture, self._transform = self._transform, None
        if gesture is None:
            return
        key = gesture['key']
        layer = self._canvas_layers.objects.get(key)
        if layer is not None:
            self._canvas_layers.cache._entries[key] = gesture['cache']
            layer.refresh(gesture['view'], gesture['picture'])
        self.transformChanged.emit()

    @Slot()
    def finishTransform(self):
        gesture = self._transform
        if gesture is None:
            return
        geometry = gesture['geometry']
        # Conservar a pintura final para que notify não recalcule o resize.
        self._transform = None
        self.transformChanged.emit()
        if geometry is None:
            return
        kind, item = self.current()
        if item is None or self._selected != gesture['key'] or item.get('locked'):
            self._sync_canvas()
            return
        if all(geometry[field] == gesture['view'][field] for field in geometry):
            return
        item.update(x=geometry['x'], y=geometry['y'])
        if gesture['resize']:
            wk, hk = ('w', 'h') if kind == 'text' else ('width', 'height')
            item.update({wk: geometry['w'], hk: geometry['h']})
        self.notify(True)

    def fail(self, message):
        self._message = str(message)
        self.changed.emit()
        self.error.emit(self._message)
        return False

    @Slot(str)
    def report(self, message):
        self.fail(message)

    @Property(bool, notify=editingChanged)
    def editingText(self):
        return bool(self._editing_key)

    @Property("QVariantMap", notify=textFormatChanged)
    def textFormat(self):
        if self._editing_key:
            return self._text_editor.formatState
        selected = self.state["selected"]
        if selected.get("type") == "text" and selected.get("rich_text_version") == 1:
            signature = tuple(selected.get(key) for key in ('html', 'font_family', 'font_size',
                              'font_color', 'align', 'indent_px', 'line_height'))
            cached = self._format_cache.get(selected['key'])
            if cached and cached[0] == signature:
                selected.update(cached[1])
                return selected
            doc = build_document(selected, selected.get("html", ""))
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            fmt, block = cursor.charFormat(), cursor.blockFormat()
            alignment = block.alignment() if block.hasProperty(QTextBlockFormat.BlockAlignment) else doc.defaultTextOption().alignment()
            selected.update(font_family=fmt.font().family() or doc.defaultFont().family(),
                            font_size=fmt.fontPointSize() or doc.defaultFont().pointSizeF(),
                            font_color=fmt.foreground().color().name(),
                            align=next((key for key, flag in ALIGNMENTS.items() if alignment & flag), "left"),
                            indent_px=block.textIndent())
            if block.lineHeightType() == QTextBlockFormat.ProportionalHeight:
                selected["line_height"] = block.lineHeight()/100
            self._format_cache[selected['key']] = (signature, {key: selected[key] for key in
                ('font_family', 'font_size', 'font_color', 'align', 'indent_px', 'line_height')})
        return selected

    @Property('QVariantMap', notify=textFormatChanged)
    def uiTextFormat(self):
        return {key: value for key, value in self.textFormat.items() if key != 'html'}

    @Slot(QObject)
    def attachTextEditor(self, item):
        self._text_editor = item
        item.contentsEdited.connect(self._live_text_changed)
        item.formatChanged.connect(self.textFormatChanged)
        item.finishRequested.connect(self.finishTextSession)
        item.feedback.connect(self.error)

    @Slot(str)
    def startTextSession(self, key):
        self.select(key)
        kind, item = self.current()
        if kind != "text" or item.get("locked", False) or self._text_editor is None:
            return
        if self._editing_key == key:
            self._text_editor.forceActiveFocus()
            return
        self._session_before = deepcopy(self._data)
        self._session_item = deepcopy(item)
        self._editing_key = key
        self._text_editor.beginEditing(self.item_view(key, kind, item))
        self._session_html = self._text_editor.text
        self.editingChanged.emit()
        if not self._canvas_attached:
            self.render()

    def _live_text_changed(self, content):
        if not self._editing_key:
            return
        for key, kind, item in self.entries():
            if key == self._editing_key:
                item.update(html=content, rich_text_version=1)
                self._views_cache = None
                if content == self._session_html:
                    item["html"] = self._session_item.get("html", "")
                    if "rich_text_version" in self._session_item:
                        item["rich_text_version"] = self._session_item["rich_text_version"]
                    else:
                        item.pop("rich_text_version", None)
                self.sync_fields()
                self.changed.emit()
                self.textFormatChanged.emit()
                break

    @Slot()
    def finishTextSession(self):
        if not self._editing_key:
            return
        self._editing_key = ""
        self.editingChanged.emit()
        self.textFormatChanged.emit()
        self.notify(self._data != self._session_before)

    def entries(self):
        return layer_entries(self._data)

    def current(self):
        return next(((kind, item) for key, kind, item in self.entries() if key == self._selected), ("", None))

    def item_view(self, key, kind, item):
        content = item.get("html", html.escape(item.get("id", "Texto")) if kind == "text" else "")
        cached = self._text_metadata.get(key)
        if cached is None or cached[0] != (kind, content):
            plain, bold, italic, underline = '', False, False, False
            if kind == 'text':
                doc = QTextDocument()
                doc.setHtml(content)
                cursor = QTextCursor(doc)
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                fmt = cursor.charFormat()
                plain = doc.toPlainText()
                bold, italic, underline = fmt.fontWeight() >= QFont.Bold, fmt.fontItalic(), fmt.fontUnderline()
            cached = ((kind, content), (plain, bold, italic, underline))
            self._text_metadata[key] = cached
        plain, bold, italic, underline = cached[1]
        title = item.get("custom_name") or (plain[:45] if kind == "text" else Path(item.get("path") or self._data.get("background_path") or kind).stem)
        width_key, height_key = ("w", "h") if kind in ("text", "background") else ("width", "height")
        canvas = self._data["canvas_size"]
        return {**item, "key": key, "type": kind, "title": title or "Texto",
                "kind": "T" if kind == "text" else ("□" if kind == "shape" else ("✍" if kind == "signature" else "▧")),
                "detail": {"text": "Texto", "shape": "Forma", "signature": "Assinatura"}.get(kind, "Imagem"),
                "x": float(item.get("x", 0)), "y": float(item.get("y", 0)),
                "w": float(item.get(width_key, canvas["w"] if kind == "background" else 300)),
                "h": float(item.get(height_key, canvas["h"] if kind == "background" else 100)),
                "rotation": float(item.get("rotation", 0)) if kind != "background" else 0,
                "opacity": float(item.get("opacity", 1)), "visible": item.get("visible", True),
                "locked": item.get("locked", kind == "background"),
                "keep_proportion": item.get("keep_proportion", True),
                "html": item.get("html", "<p>" + html.escape(plain) + "</p>"),
                "font_family": item.get("font_family", "Arial"), "font_size": item.get("font_size", 16),
                "font_color": item.get("font_color", "#000000"), "align": item.get("align", "left"),
                "vertical_align": item.get("vertical_align", "top"),
                "line_height": item.get("line_height", 1.15), "indent_px": item.get("indent_px", 0),
                "has_link": item.get("has_link", False), "bold": bold,
                "italic": italic, "underline": underline}

    @Property("QVariantMap", notify=changed)
    def state(self):
        layers = self._views()
        selected = dict(next((item for item in layers if item["key"] == self._selected), {}))
        return {"name": self._data.get("name", "Modelo"), "path": str(self._path or ""),
                "dirty": self._data != self._saved, "selected": selected, "layers": list(reversed(layers)),
                "paintLayers": layers, "width": self._data["canvas_size"]["w"], "height": self._data["canvas_size"]["h"],
                "fields": self._data.get("placeholders", []), "guides": self._data.get("guidelines", []),
                "guidesVisible": self._data.get("guidelines_visible", True),
                "guidesLocked": self._data.get("guidelines_locked", False),
                "canUndo": self.history.can_undo(), "canRedo": self.history.can_redo(), "message": self._message,
                "previewBusy": self._preview_busy, "missingFonts": self._missing_fonts}

    @Property('QVariantMap', notify=changed)
    def uiState(self):
        # Não transportar as listas completas para cada binding QML de um campo.
        # state conserva a API Python usada pelos consumidores existentes.
        state = self.state
        state['layerCount'] = len(state.pop('layers'))
        state.pop('paintLayers')
        state['selected'].pop('html', None)
        return state

    @Property("QVariantMap", notify=changed)
    def documentSize(self):
        return {**self._data["canvas_size"], "widthMm": self._data.get("target_w_mm", self._data["canvas_size"]["w"]*25.4/300),
                "heightMm": self._data.get("target_h_mm", self._data["canvas_size"]["h"]*25.4/300)}

    @Slot(str, str, str, str, result=bool)
    def setDocumentSize(self, width, height, width_mm, height_mm):
        try:
            values = [float(str(value).replace(",", ".")) for value in (width, height, width_mm, height_mm)]
            if any(not math.isfinite(value) or value <= 0 or value > 100000 for value in values):
                raise ValueError()
            w, h = [max(1, round(value)) for value in values[:2]]
        except ValueError:
            return self.fail("Informe dimensões positivas e finitas, até 100.000.")
        self.finishTextSession()
        self._data.update(canvas_size={**self._data["canvas_size"], "w": w, "h": h}, target_w_mm=values[2], target_h_mm=values[3])
        self.notify(True)
        return True

    @Property(str, notify=previewChanged)
    def previewUrl(self):
        return f"image://model/{self._revision}"

    @Property(str, notify=previewChanged)
    def aboveUrl(self):
        return f"image://model/above/{self._revision}"

    @Property("QVariantList", notify=documentChanged)
    def paintLayers(self):
        return self._views()

    def _views(self):
        if self._views_cache is None:
            views, keep = [], set()
            canvas = self._data['canvas_size']
            for key, kind, item in self.entries():
                keep.add(key)
                cached = self._item_views.get(key)
                if cached is None or cached[:3] != (kind, item, canvas):
                    cached = (kind, deepcopy(item), dict(canvas), self.item_view(key, kind, item))
                    self._item_views[key] = cached
                views.append(cached[3])
            self._item_views = {key: value for key, value in self._item_views.items() if key in keep}
            self._text_metadata = {key: value for key, value in self._text_metadata.items() if key in keep}
            self._format_cache = {key: value for key, value in self._format_cache.items() if key in keep}
            self._views_cache = views
        return self._views_cache

    @Property("QVariantList", notify=documentChanged)
    def layers(self):
        return list(reversed(self.paintLayers))

    def notify(self, commit=False):
        self.cancelTransform()
        previous_views = self._views_cache
        self._views_cache = None
        if self._data != self._saved:
            self._message = "Alterações não salvas"
        elif self._message == "Alterações não salvas":
            self._message = "Sem alterações pendentes"
        self._preview_serial += 1
        font_signature = [(item.get('font_family'), item.get('rich_text_version'),
                           item.get('html') if item.get('rich_text_version') == 1 else None)
                          for item in self._data.get('boxes', [])]
        if font_signature != self._font_signature:
            self._missing_fonts = missing_template_fonts(self._data)
            self._font_signature = font_signature
        if commit:
            self.history.push(deepcopy(self._data))
        if previous_views != self._views():
            self.documentChanged.emit()
        self.changed.emit()
        self.textFormatChanged.emit()
        if self._canvas_attached:
            self._sync_canvas()
        else:
            self._render_timer.start(30)

    def render_data(self):
        result = deepcopy(self._data)
        base = self._path.parent if self._path else Path.cwd()
        result["__model_dir"] = str(base)
        if result.get("background_path"):
            result["background_path"] = str((base / result["background_path"]).resolve())
        for group in ("images", "signatures"):
            for item in result.get(group, []):
                item["path"] = str((base / item["path"]).resolve())
        for item in result.get("boxes", []):
            item.setdefault("html", "<p>" + html.escape(item.get("id", "Texto")) + "</p>")
            for variable in variables_in_html(item["html"]):
                if variable not in result.setdefault("placeholders", []):
                    result["placeholders"].append(variable)
        return result

    @Slot()
    def render(self):
        self._render_timer.stop()
        self._preview_serial += 1
        try:
            self._preview_ready(self._preview_serial, paint_preview(self.render_data(), self._editing_key), "")
        except Exception as exc:
            self.fail(f"Não foi possível gerar a prévia: {exc}")

    @Slot()
    def requestPreview(self):
        self._preview_serial += 1
        self._preview_busy = True
        self.changed.emit()
        self._preview_service.request(self._preview_serial, self.render_data(), self._editing_key)

    @Slot(int, object, str)
    def _preview_ready(self, serial, result, error):
        if serial != self._preview_serial:
            return
        self._preview_busy = False
        if error:
            self.fail(f"Não foi possível gerar a prévia: {error}")
            return
        self.provider.image, above = result
        if above is not None:
            self.provider.above = above
        self._revision += 1
        self.previewChanged.emit()
        self.changed.emit()

    def shutdown(self):
        self._render_timer.stop()
        self._preview_serial += 1
        self._preview_service.close()

    @Slot(str, result=bool)
    def load(self, filename):
        try:
            path = Path(filename).expanduser().resolve()
            raw = path.read_bytes()
            data = json.loads(raw)
            size = data["canvas_size"]
            if not all(isinstance(size[k], (int, float)) and math.isfinite(size[k]) and 0 < size[k] <= 100000 for k in ("w", "h")):
                raise ValueError("Dimensões inválidas no modelo")
            for group in ("boxes", "images", "signatures", "shapes", "guidelines"):
                if not isinstance(data.get(group, []), list) or not all(isinstance(item, dict) for item in data.get(group, [])):
                    raise ValueError(f"Lista inválida: {group}")
            data = upgrade_layers(data)
            data["canvas_size"] = {**size, "w": max(1, round(size["w"])), "h": max(1, round(size["h"]))}
            for object_id, kind, item in layer_entries(data):
                for field in ("x", "y", "w", "h", "width", "height", "rotation", "opacity", "font_size", "line_height", "indent_px", "outline_width"):
                    if field not in item:
                        continue
                    value = item[field]
                    if not isinstance(value, (int, float)) or not math.isfinite(value):
                        raise ValueError(f"Valor inválido em {kind}: {field}")
                    if field in ("w", "h", "width", "height", "font_size", "line_height", "outline_width") and value <= 0:
                        raise ValueError(f"Dimensão inválida em {kind}: {field}")
                if kind == "text" and "html" in item and not isinstance(item["html"], str):
                    raise ValueError("Conteúdo de texto inválido")
                if kind in ("image", "signature") and not isinstance(item.get("path"), str):
                    raise ValueError("Caminho de imagem inválido")
            self.finishTextSession()
            self._data, self._path = data, path
            self._canvas_layers.invalidate()
            self._font_signature = None
            self._format_cache.clear()
            self._disk_hash = hashlib.sha256(raw).hexdigest()
            self._selected = ""
            self._saved = deepcopy(data)
            self.history.clear()
            self.history.push(deepcopy(data))
            self._message = "Modelo carregado"
            self.notify()
            return True
        except Exception as exc:
            return self.fail(f"Não foi possível abrir o modelo: {exc}")

    def confirm_discard(self):
        self.finishTextSession()
        if self._data == self._saved:
            return True
        answer = QMessageBox.question(None, "Alterações não salvas", "Salvar as alterações antes de continuar?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
        return self.save() if answer == QMessageBox.Save else answer == QMessageBox.Discard

    @Slot(result=bool)
    def canClose(self):
        self.cancelTransform()
        return self.confirm_discard()

    @Slot()
    def openDialog(self):
        if not self.confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(None, "Abrir modelo", str(get_models_dir()), "Modelo COMSOC (*.json)")
        if path:
            self.load(path)

    @Slot()
    def newDocument(self):
        if not self.confirm_discard():
            return
        self._data = self.blank()
        self._path, self._disk_hash, self._selected = None, None, ""
        self._saved = deepcopy(self._data)
        self.history.clear()
        self.history.push(deepcopy(self._data))
        self.notify()

    @Slot(result=bool)
    def save(self):
        self.finishTextSession()
        if not self._path:
            return self.saveAs()
        if self.library_mode and (not self._path.is_relative_to(get_models_dir().resolve()) or self._path.name != "template_v3.json"):
            return self.saveAs()
        return self.save_to(self._path)

    @Slot(result=bool)
    def saveAs(self):
        self.finishTextSession()
        name, ok = QInputDialog.getText(None, "Salvar modelo como", "Nome do modelo:", text=self._data.get("name", "Modelo"))
        if not ok or not name.strip():
            return False
        suggested = get_models_dir() / slugify_model_name(name) / "template_v3.json"
        if self.library_mode:
            if suggested.exists() and suggested.resolve() != self._path:
                answer = QMessageBox.question(None, "Substituir modelo", f"Já existe um modelo chamado {name.strip()}. Substituir o arquivo da biblioteca?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if answer != QMessageBox.Yes:
                    return False
            return self.save_to(suggested, name.strip())
        path, _ = QFileDialog.getSaveFileName(None, "Salvar modelo como", str(suggested), "Modelo COMSOC (*.json)")
        if not path:
            return False
        return self.save_to(Path(path), name.strip())

    def save_to(self, filename, name=None):
        self.cancelTransform()
        """Gravação atômica; conserva chaves desconhecidas e caminhos relativos."""
        self.finishTextSession()
        try:
            path = Path(filename).expanduser().resolve()
            if path == self._path and path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != self._disk_hash:
                return self.fail("O arquivo foi alterado por outro editor. Reabra o modelo ou use Salvar como para não sobrescrever essas alterações.")
            data = deepcopy(self._data)
            if name:
                data["name"] = name
            path.parent.mkdir(parents=True, exist_ok=True)
            old_base = self._path.parent if self._path else Path.cwd()
            refs = [(data, "background_path")]
            refs += [(item, "path") for group in ("images", "signatures") for item in data.get(group, [])]
            for owner, key in refs:
                if not owner.get(key):
                    continue
                source = (old_base / owner[key]).resolve()
                if not source.is_file():
                    # Preserve missing relative assets on an in-place save, never drop them.
                    if path.parent != old_base:
                        raise ValueError(f"Imagem ausente: {source}")
                    continue
                try:
                    owner[key] = source.relative_to(path.parent).as_posix()
                except ValueError:
                    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
                    target = path.parent / "assets" / (digest + source.suffix.lower())
                    target.parent.mkdir(exist_ok=True)
                    if not target.exists():
                        shutil.copy2(source, target)
                    owner[key] = target.relative_to(path.parent).as_posix()
            raw = json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")
            output = QSaveFile(str(path))
            if not output.open(QIODevice.WriteOnly) or output.write(raw) != len(raw) or not output.commit():
                raise OSError(output.errorString())
            same_directory = self._path is not None and self._path.parent == path.parent
            self._data, self._path = data, path
            self._disk_hash = hashlib.sha256(raw).hexdigest()
            self._saved = deepcopy(data)
            self._views_cache = None
            if not same_directory:
                self.history.clear()
            self.history.push(deepcopy(data))
            self._message = "Modelo salvo"
            if self._canvas_attached:
                self._sync_canvas()
            self.render()
            try:
                cache = path.parent / ".render_cache"
                cache.mkdir(exist_ok=True)
                if not self.provider.image.save(str(cache / "thumbnail_raw.png"), "PNG"):
                    raise OSError("Falha na gravação da miniatura")
            except OSError:
                self._message = "Modelo salvo; não foi possível atualizar a miniatura."
            self.changed.emit()
            self.modelSaved.emit(data.get("name", "Modelo"), list(data.get("placeholders", [])), str(path))
            return True
        except Exception as exc:
            return self.fail(f"Não foi possível salvar o modelo: {exc}")

    @Slot(str)
    def select(self, key):
        if self._guide_transform is not None:
            self.cancelTransform()
        if self._transform and key != self._transform['key']:
            self.cancelTransform()
        if self._editing_key and key != self._editing_key:
            self.finishTextSession()
        self._selected = key if any(k == key for k, _, _ in self.entries()) else ""
        self.changed.emit()
        self.textFormatChanged.emit()

    def sync_fields(self):
        found = []
        for key, kind, item in self.entries():
            if kind == "text":
                for var in variables_in_html(item.get("html", "")):
                    if var not in found:
                        found.append(var)
            if kind in ("text", "image", "shape") and item.get("has_link") and item.get("link_key"):
                if item["link_key"] not in found:
                    found.append(item["link_key"])
        previous = self._data.get("placeholders", [])
        self._data["placeholders"] = [v for v in previous if v in found] + [v for v in found if v not in previous]

    @Slot(str)
    def addItem(self, kind):
        if kind == "text":
            item = {"html": "<p>Texto</p>", "id": "Texto", "x": 50, "y": 50, "w": 300, "h": 100,
                    "font_family": "Arial", "font_size": 24, "font_color": "#000000", "custom_name": "Texto"}
            self.insert_item(kind, item)
        elif kind == "shape":
            self.insert_item(kind, {"shape_type": "rectangle", "fill_color": "#FFFFFF",
                                  "outline_enabled": False, "outline_color": "#000000", "outline_width": 1,
                                  "x": 50, "y": 50, "width": 200, "height": 120,
                                  "keep_proportion": False, "custom_name": "Forma"})
        elif kind in ("image", "signature"):
            filename, _ = QFileDialog.getOpenFileName(None, "Adicionar imagem" if kind == "image" else "Adicionar assinatura", "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.svg)")
            if filename:
                self.add_asset(kind, filename)

    def insert_item(self, kind, item):
        self.finishTextSession()
        group = self.GROUPS[kind]
        items = self._data.setdefault(group, [])
        layer_ids = [entry.get("layer_id", 0) or 0 for _, _, entry in self.entries()]
        item["layer_id"] = max(layer_ids, default=0) + 1
        item["object_id"] = uuid4().hex
        item.setdefault("z_value", len(self.entries()))
        items.append(item)
        self._data.setdefault("layer_order", []).append(item["object_id"])
        for index, (_, _, value) in enumerate(self.entries()):
            value["z_value"] = index
        self._selected = item["object_id"]
        self.sync_fields()
        self.notify(True)

    def add_asset(self, kind, filename):
        image = QImage(str(filename))
        if image.isNull():
            return self.fail("Não foi possível abrir a imagem selecionada.")
        width = min(image.width(), self._data["canvas_size"]["w"] / 2)
        self.insert_item(kind, {"path": str(Path(filename).resolve()), "custom_name": Path(filename).stem,
                              "x": 50, "y": 50, "width": width, "height": image.height() * width / image.width()})
        return True

    def replace_asset(self, filename):
        kind, item = self.current()
        if kind not in ("image", "signature") or item.get("locked", False):
            return False
        if QImage(str(filename)).isNull():
            return self.fail("Não foi possível abrir a imagem selecionada.")
        self._canvas_layers.invalidate_asset(filename)
        item["path"] = str(Path(filename).resolve())
        self.notify(True)
        return True

    @Slot()
    def replaceAsset(self):
        kind, item = self.current()
        if kind not in ("image", "signature") or item.get("locked", False):
            return
        filename, _ = QFileDialog.getOpenFileName(None, "Substituir imagem", "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.svg)")
        if filename:
            self.replace_asset(filename)

    @Slot(str, "QVariant")
    def setValue(self, key, value):
        kind, item = self.current()
        if item is None or (item.get("locked", kind == "background") and key not in ("locked", "visible")):
            return
        if kind == "background":
            item = self._data.setdefault("bg_props", {})
        numeric = {"x", "y", "w", "h", "rotation", "opacity", "font_size", "line_height", "indent_px", "outline_width"}
        if key in numeric:
            try:
                value = float(str(value).replace(",", "."))
                if not math.isfinite(value):
                    raise ValueError()
                if key in ("w", "h", "font_size", "line_height", "outline_width") and value <= 0:
                    raise ValueError()
                if key == "outline_width" and not 0.1 <= value <= 100:
                    raise ValueError()
                if key == "opacity":
                    value = max(0, min(1, value))
                if key == "font_size":
                    value = max(1, min(999, round(value)))
            except ValueError:
                self.fail("Informe um valor numérico válido.")
                self.changed.emit()
                return
        elif key in ("font_color", "fill_color", "outline_color"):
            if not QColor(str(value)).isValid():
                return
        elif key not in {"html", "font_family", "align", "vertical_align", "keep_proportion", "has_link", "locked", "visible", "custom_name", "shape_type", "outline_enabled", "link_key"}:
            return
        if key.startswith("outline_") and kind not in ("text", "shape"):
            return
        if key in ("shape_type", "fill_color") and kind != "shape":
            return
        if key == "shape_type":
            if value not in ("rectangle", "square", "ellipse", "circle"):
                return
            if value in ("square", "circle"):
                item["height"] = item.get("width", 200)
                item["keep_proportion"] = True
        if key in {"html", "font_family", "font_size", "font_color", "align", "vertical_align", "line_height", "indent_px"} and kind != "text":
            return
        if key in ("has_link", "link_key") and kind not in ("text", "image", "shape"):
            return
        if key == "link_key":
            value = str(value).strip()
            if not value:
                return self.fail("Informe o nome da coluna do link.")
        if key == "keep_proportion" and not value and item.get("shape_type") in ("square", "circle"):
            return
        text_keys = {"font_family", "font_size", "font_color", "align", "vertical_align", "line_height", "indent_px"}
        html_before = item.get("html")
        if self._editing_key and key not in text_keys:
            self.finishTextSession()
        if kind == "text" and key in text_keys and self._editing_key == self._selected:
            self._text_editor.applyFormat(key, value)
            if key != "vertical_align":
                return
        elif kind == "text" and key in text_keys and item.get("rich_text_version") == 1:
            doc = build_document(item, item.get("html", ""))
            cursor = QTextCursor(doc)
            cursor.select(QTextCursor.Document)
            fmt = QTextCharFormat()
            block = QTextBlockFormat()
            if key == "font_family": fmt.setFontFamilies([value])
            elif key == "font_size": fmt.setFontPointSize(value)
            elif key == "font_color": fmt.setForeground(QColor(value))
            elif key == "align": block.setAlignment(ALIGNMENTS.get(value, Qt.AlignLeft))
            elif key == "indent_px": block.setTextIndent(value)
            elif key == "line_height": block.setLineHeight(value*100, QTextBlockFormat.ProportionalHeight)
            cursor.mergeCharFormat(fmt)
            cursor.mergeBlockFormat(block)
            item["html"] = doc.toHtml()
        if kind == "background" and key == "rotation":
            return
        if key == "has_link" and value and not item.get("link_key"):
            item["link_key"] = "Link - " + self.item_view(self._selected, kind, item)["title"]
        if key not in ("w", "h") and item.get(key) == value and item.get("html") == html_before:
            return
        wkey, hkey = ("w", "h") if kind in ("text", "background") else ("width", "height")
        if key in ("w", "h"):
            view = self.item_view(self._selected, kind, item)
            if item.get("keep_proportion", True) or item.get("shape_type") in ("square", "circle"):
                item[hkey if key == "w" else wkey] = value * (view["h"] / view["w"] if key == "w" else view["w"] / view["h"])
            key = wkey if key == "w" else hkey
        item[key] = value
        if key in ("html", "has_link", "link_key"):
            self.sync_fields()
        self.notify(True)

    @Slot(float, float)
    def moveSelected(self, x, y):
        kind, item = self.current()
        if item is None or item.get("locked", kind == "background") or not all(map(math.isfinite, (x,y))):
            return
        if kind == "background":
            item = self._data.setdefault("bg_props", {})
        item.update(x=round(x, 2), y=round(y, 2))
        self.notify(True)

    @Slot(str, float, float)
    def moveItem(self, key, x, y):
        self.finishTextSession()
        self.select(key)
        self.moveSelected(x, y)

    @Slot(str, float, float)
    def resizeItem(self, key, width, height):
        self.finishTextSession()
        self.select(key)
        kind, item = self.current()
        if item is None or item.get("locked", kind == "background"):
            return
        if not all(math.isfinite(v) and v > 0 for v in (width, height)):
            return
        view = self.item_view(key, kind, item)
        if view["keep_proportion"] or item.get("shape_type") in ("square", "circle"):
            height = width * view["h"] / view["w"]
        wkey, hkey = ("w", "h") if kind in ("text", "background") else ("width", "height")
        item.update({wkey: width, hkey: height})
        self.notify(True)

    @Slot(str)
    def formatText(self, style):
        if self._editing_key:
            self._text_editor.applyFormat(style, True)
            return
        kind, item = self.current()
        if kind != "text" or item.get("locked", False):
            return
        doc = build_document(item, item.get("html", ""))
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.Document)
        current = cursor.charFormat()
        fmt = QTextCharFormat()
        if style == "Negrito": fmt.setFontWeight(QFont.Normal if current.fontWeight() >= QFont.Bold else QFont.Bold)
        elif style == "Itálico": fmt.setFontItalic(not current.fontItalic())
        elif style == "Sublinhado": fmt.setFontUnderline(not current.fontUnderline())
        else: return
        cursor.mergeCharFormat(fmt)
        item["rich_text_version"] = 1
        self.setValue("html", doc.toHtml())

    @Slot()
    def deleteSelected(self):
        self.finishTextSession()
        kind, item = self.current()
        if item is None or item.get("locked", kind == "background"):
            return
        if kind == "background":
            self._data["background_path"] = None
        else:
            self._data[self.GROUPS[kind]].remove(item)
            self._data["layer_order"].remove(self._selected)
        self._selected = ""
        self.sync_fields()
        self.notify(True)

    @Slot()
    def duplicateSelected(self):
        kind, item = self.current()
        if kind not in self.GROUPS:
            return
        clone = deepcopy(item)
        clone.update(x=clone.get("x", 0)+20, y=clone.get("y", 0)+20, locked=False)
        clone["custom_name"] = self.item_view(self._selected, kind, item)["title"] + " (cópia)"
        self.insert_item(kind, clone)

    @Slot()
    def renameSelected(self):
        kind, item = self.current()
        if item is None or item.get("locked", False):
            return
        title, ok = QInputDialog.getText(None, "Renomear camada", "Nome:", text=self.item_view(self._selected, kind, item)["title"])
        if ok and title.strip(): self.setValue("custom_name", title.strip())

    @Slot(int, int)
    def moveField(self, source, target):
        values = self._data.get("placeholders", [])
        if 0 <= source < len(values) and 0 <= target < len(values) and source != target:
            values.insert(target, values.pop(source))
            self.notify(True)

    @Slot(str, str)
    def moveLayer(self, source, target):
        self.finishTextSession()
        entries = {key: (kind, item) for key, kind, item in self.entries()}
        if source not in entries or target not in entries or source == target:
            return
        kind, item = entries[source]
        if kind not in self.GROUPS:
            return
        if item.get("locked", False):
            return
        order = self._data["layer_order"]
        src, dst = order.index(source), order.index(target)
        order.insert(dst, order.pop(src))
        for index, (_, _, value) in enumerate(self.entries()):
            value["z_value"] = index
        self._selected = source
        self.notify(True)

    @Slot(bool)
    def addGuide(self, vertical):
        if self._data.get("guidelines_locked", False): return
        self._data.setdefault("guidelines", []).append({"vertical": vertical, "pos": self._data["canvas_size"]["w" if vertical else "h"] / 2, "visible": True})
        self.notify(True)

    @Slot(int, float)
    def moveGuide(self, index, position):
        guides = self._data.get("guidelines", [])
        if not self._data.get("guidelines_locked", False) and 0 <= index < len(guides) and math.isfinite(position):
            if guides[index]['pos'] == position:
                return
            guides[index]["pos"] = position
            self.notify(True)

    @Slot(str, bool)
    def guideOption(self, option, value):
        if option in ("guidelines_visible", "guidelines_locked"):
            self._data[option] = value
            self.notify(True)

    @Slot(int)
    def deleteGuide(self, index):
        guides = self._data.get("guidelines", [])
        if not self._data.get("guidelines_locked", False) and 0 <= index < len(guides):
            guides.pop(index)
            self.notify(True)

    @Slot(int)
    def editGuide(self, index):
        guides = self._data.get("guidelines", [])
        if self._data.get("guidelines_locked", False) or not 0 <= index < len(guides):
            return
        position, ok = QInputDialog.getDouble(None, "Posição da guia", "Posição em pixels:", guides[index]["pos"], -100000, 100000, 2)
        if ok:
            self.moveGuide(index, position)

    @Slot()
    def undo(self):
        if self.transforming:
            self.cancelTransform()
            return
        if self._editing_key:
            self._text_editor.command("undo")
            return
        state = self.history.undo()
        if state is not None:
            self._data = deepcopy(state)
            self._selected = ""
            self.notify()

    @Slot()
    def redo(self):
        if self.transforming:
            self.cancelTransform()
            return
        if self._editing_key:
            self._text_editor.command("redo")
            return
        state = self.history.redo()
        if state is not None:
            self._data = deepcopy(state)
            self._selected = ""
            self.notify()
