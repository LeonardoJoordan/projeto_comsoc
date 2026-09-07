"""Adaptador do frontend QML para o formato v3 e serviços existentes.

Não importa o editor Widgets. Nenhuma regra nova é adicionada ao renderer.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil

from PySide6.QtCore import QObject, Property, Signal, Slot, QSaveFile, QIODevice, QTimer
from PySide6.QtGui import QColor, QImage, QTextDocument, QTextCursor, QTextCharFormat, QFont
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from core.history_manager import HistoryManager
from core.paths import get_models_dir
from core.template_manager import slugify_model_name
from features.generator.renderer import NativeRenderer


class PreviewProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self.image = QImage(1, 1, QImage.Format_ARGB32)
        self.image.fill(QColor("white"))

    def requestImage(self, _id, size, requested_size):
        size.setWidth(self.image.width())
        size.setHeight(self.image.height())
        return self.image


class EditorBridge(QObject):
    changed = Signal()
    previewChanged = Signal()
    error = Signal(str)
    GROUPS = {"text": "boxes", "image": "images", "signature": "signatures"}

    def __init__(self, provider=None):
        super().__init__()
        self.provider = provider or PreviewProvider()
        self.history = HistoryManager(60)
        self._path = None
        self._disk_hash = None
        self._selected = ""
        self._revision = 0
        self._message = ""
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self.render)
        self._data = self.blank()
        self._saved = deepcopy(self._data)
        self.history.push(deepcopy(self._data))

    @staticmethod
    def blank():
        return {"name": "Novo modelo", "canvas_size": {"w": 1000, "h": 700},
                "target_w_mm": 264.58, "target_h_mm": 185.21,
                "boxes": [], "images": [], "signatures": [], "placeholders": [],
                "background_path": None, "guidelines": []}

    def fail(self, message):
        self._message = str(message)
        self.changed.emit()
        self.error.emit(self._message)
        return False

    def entries(self):
        # Bottom to top: actual paint order of NativeRenderer.
        result = []
        if self._data.get("background_path"):
            result.append(("background:0", "background", self._data.get("bg_props", {})))
        for kind, group in (("image", "images"), ("text", "boxes"), ("signature", "signatures")):
            result.extend((f"{kind}:{i}", kind, item) for i, item in enumerate(self._data.get(group, [])))
        return result

    def current(self):
        return next(((kind, item) for key, kind, item in self.entries() if key == self._selected), ("", None))

    def item_view(self, key, kind, item):
        doc = QTextDocument()
        doc.setHtml(item.get("html", html.escape(item.get("id", "Texto")) if kind == "text" else ""))
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        fmt = cursor.charFormat()
        title = item.get("custom_name") or (doc.toPlainText()[:45] if kind == "text" else Path(item.get("path") or self._data.get("background_path") or kind).stem)
        width_key, height_key = ("w", "h") if kind in ("text", "background") else ("width", "height")
        canvas = self._data["canvas_size"]
        return {**item, "key": key, "type": kind, "title": title or "Texto",
                "kind": "T" if kind == "text" else ("✍" if kind == "signature" else "▧"),
                "detail": "Texto" if kind == "text" else ("Assinatura" if kind == "signature" else "Imagem"),
                "x": float(item.get("x", 0)), "y": float(item.get("y", 0)),
                "w": float(item.get(width_key, canvas["w"] if kind == "background" else 300)),
                "h": float(item.get(height_key, canvas["h"] if kind == "background" else 100)),
                "rotation": float(item.get("rotation", 0)) if kind != "background" else 0,
                "opacity": float(item.get("opacity", 1)), "visible": item.get("visible", True),
                "locked": item.get("locked", kind == "background"),
                "keep_proportion": item.get("keep_proportion", True),
                "html": item.get("html", "<p>" + html.escape(doc.toPlainText()) + "</p>"),
                "font_family": item.get("font_family", "Arial"), "font_size": item.get("font_size", 16),
                "font_color": item.get("font_color", "#000000"), "align": item.get("align", "left"),
                "vertical_align": item.get("vertical_align", "top"),
                "line_height": item.get("line_height", 1.15), "indent_px": item.get("indent_px", 0),
                "has_link": item.get("has_link", False), "bold": fmt.fontWeight() >= QFont.Bold,
                "italic": fmt.fontItalic(), "underline": fmt.fontUnderline()}

    @Property("QVariantMap", notify=changed)
    def state(self):
        layers = [self.item_view(*entry) for entry in self.entries()]
        selected = next((item for item in layers if item["key"] == self._selected), {})
        return {"name": self._data.get("name", "Modelo"), "path": str(self._path or ""),
                "dirty": self._data != self._saved, "selected": selected, "layers": list(reversed(layers)),
                "paintLayers": layers, "width": self._data["canvas_size"]["w"], "height": self._data["canvas_size"]["h"],
                "fields": self._data.get("placeholders", []), "guides": self._data.get("guidelines", []),
                "guidesVisible": self._data.get("guidelines_visible", True),
                "guidesLocked": self._data.get("guidelines_locked", False),
                "canUndo": self.history.can_undo(), "canRedo": self.history.can_redo(), "message": self._message}

    @Property(str, notify=previewChanged)
    def previewUrl(self):
        return f"image://model/{self._revision}"

    def notify(self, commit=False):
        if commit:
            self.history.push(deepcopy(self._data))
        self.changed.emit()
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
            for variable in re.findall(r"\{([a-zA-Z0-9_]+)\}", item["html"]):
                if variable not in result.setdefault("placeholders", []):
                    result["placeholders"].append(variable)
        return result

    @Slot()
    def render(self):
        try:
            self.provider.image = NativeRenderer(self.render_data()).render_to_pixmap(max_side=1600).toImage()
            self._revision += 1
            self.previewChanged.emit()
        except Exception as exc:
            self.fail(f"Não foi possível gerar a prévia: {exc}")

    @Slot(str, result=bool)
    def load(self, filename):
        try:
            path = Path(filename).expanduser().resolve()
            raw = path.read_bytes()
            data = json.loads(raw)
            size = data["canvas_size"]
            if not all(isinstance(size[k], (int, float)) and math.isfinite(size[k]) and 0 < size[k] <= 100000 for k in ("w", "h")):
                raise ValueError("Dimensões inválidas no modelo")
            for group in ("boxes", "images", "signatures", "guidelines"):
                if not isinstance(data.get(group, []), list) or not all(isinstance(item, dict) for item in data.get(group, [])):
                    raise ValueError(f"Lista inválida: {group}")
            self._data, self._path = data, path
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
        if self._data == self._saved:
            return True
        answer = QMessageBox.question(None, "Alterações não salvas", "Salvar as alterações antes de continuar?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
        return self.save() if answer == QMessageBox.Save else answer == QMessageBox.Discard

    @Slot(result=bool)
    def canClose(self):
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
        if not self._path:
            return self.saveAs()
        return self.save_to(self._path)

    @Slot(result=bool)
    def saveAs(self):
        name, ok = QInputDialog.getText(None, "Salvar modelo como", "Nome do modelo:", text=self._data.get("name", "Modelo"))
        if not ok or not name.strip():
            return False
        suggested = get_models_dir() / slugify_model_name(name) / "template_v3.json"
        path, _ = QFileDialog.getSaveFileName(None, "Salvar modelo como", str(suggested), "Modelo COMSOC (*.json)")
        if not path:
            return False
        return self.save_to(Path(path), name.strip())

    def save_to(self, filename, name=None):
        """Gravação atômica; conserva chaves desconhecidas e caminhos relativos."""
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
            if not same_directory:
                self.history.clear()
            self.history.push(deepcopy(data))
            self._message = "Modelo salvo"
            self.render()
            try:
                cache = path.parent / ".render_cache"
                cache.mkdir(exist_ok=True)
                self.provider.image.save(str(cache / "thumbnail_raw.png"), "PNG")
            except OSError:
                self._message = "Modelo salvo; não foi possível atualizar a miniatura."
            self.changed.emit()
            return True
        except Exception as exc:
            return self.fail(f"Não foi possível salvar o modelo: {exc}")

    @Slot(str)
    def select(self, key):
        self._selected = key if any(k == key for k, _, _ in self.entries()) else ""
        self.changed.emit()

    def sync_fields(self):
        found = []
        for key, kind, item in self.entries():
            if kind == "text":
                for var in re.findall(r"\{([a-zA-Z0-9_]+)\}", item.get("html", "")):
                    if var not in found:
                        found.append(var)
            if kind in ("text", "image") and item.get("has_link") and item.get("link_key"):
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
        elif kind in ("image", "signature"):
            filename, _ = QFileDialog.getOpenFileName(None, "Adicionar imagem" if kind == "image" else "Adicionar assinatura", "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.svg)")
            if filename:
                self.add_asset(kind, filename)

    def insert_item(self, kind, item):
        group = self.GROUPS[kind]
        items = self._data.setdefault(group, [])
        layer_ids = [entry.get("layer_id", 0) or 0 for _, _, entry in self.entries()]
        item["layer_id"] = max(layer_ids, default=0) + 1
        item.setdefault("z_value", {"image": 100, "text": 200, "signature": 250}[kind] + len(items))
        items.append(item)
        self._selected = f"{kind}:{len(items)-1}"
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

    @Slot(str, "QVariant")
    def setValue(self, key, value):
        kind, item = self.current()
        if item is None or (item.get("locked", kind == "background") and key not in ("locked", "visible")):
            return
        if kind == "background":
            item = self._data.setdefault("bg_props", {})
        numeric = {"x", "y", "w", "h", "rotation", "opacity", "font_size", "line_height", "indent_px"}
        if key in numeric:
            try:
                value = float(str(value).replace(",", "."))
                if not math.isfinite(value):
                    raise ValueError()
                if key in ("w", "h", "font_size", "line_height") and value <= 0:
                    raise ValueError()
                if key == "opacity":
                    value = max(0, min(1, value))
                if key == "font_size":
                    value = max(1, min(999, round(value)))
            except ValueError:
                self.fail("Informe um valor numérico válido.")
                self.changed.emit()
                return
        elif key == "font_color":
            if not QColor(str(value)).isValid():
                return
        elif key not in {"html", "font_family", "align", "vertical_align", "keep_proportion", "has_link", "locked", "visible", "custom_name"}:
            return
        if key in {"html", "font_family", "font_size", "font_color", "align", "vertical_align", "line_height", "indent_px"} and kind != "text":
            return
        if key == "has_link" and kind not in ("text", "image"):
            return
        if kind == "background" and key == "rotation":
            return
        if key == "has_link" and value and not item.get("link_key"):
            item["link_key"] = "Link - " + self.item_view(self._selected, kind, item)["title"]
        if key not in ("w", "h") and item.get(key) == value:
            return
        wkey, hkey = ("w", "h") if kind in ("text", "background") else ("width", "height")
        if key in ("w", "h"):
            view = self.item_view(self._selected, kind, item)
            if item.get("keep_proportion", True):
                item[hkey if key == "w" else wkey] = value * (view["h"] / view["w"] if key == "w" else view["w"] / view["h"])
            key = wkey if key == "w" else hkey
        item[key] = value
        if key in ("html", "has_link"):
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
        self._selected = key
        self.moveSelected(x, y)

    @Slot(str, float, float)
    def resizeItem(self, key, width, height):
        self._selected = key
        kind, item = self.current()
        if item is None or item.get("locked", kind == "background"):
            return
        if not all(math.isfinite(v) and v > 0 for v in (width, height)):
            return
        view = self.item_view(key, kind, item)
        if view["keep_proportion"]:
            height = width * view["h"] / view["w"]
        wkey, hkey = ("w", "h") if kind in ("text", "background") else ("width", "height")
        item.update({wkey: width, hkey: height})
        self.notify(True)

    @Slot(str)
    def formatText(self, style):
        kind, item = self.current()
        if kind != "text" or item.get("locked", False):
            return
        doc = QTextDocument()
        doc.setHtml(item.get("html", ""))
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.Document)
        current = cursor.charFormat()
        fmt = QTextCharFormat()
        if style == "Negrito": fmt.setFontWeight(QFont.Normal if current.fontWeight() >= QFont.Bold else QFont.Bold)
        elif style == "Itálico": fmt.setFontItalic(not current.fontItalic())
        elif style == "Sublinhado": fmt.setFontUnderline(not current.fontUnderline())
        else: return
        cursor.mergeCharFormat(fmt)
        self.setValue("html", doc.toHtml())

    @Slot()
    def deleteSelected(self):
        kind, item = self.current()
        if item is None or item.get("locked", kind == "background"):
            return
        if kind == "background":
            self._data["background_path"] = None
        else:
            del self._data[self.GROUPS[kind]][int(self._selected.split(":")[1])]
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
        if item is None:
            return
        title, ok = QInputDialog.getText(None, "Renomear camada", "Nome:", text=self.item_view(self._selected, kind, item)["title"])
        if ok and title.strip(): self.setValue("custom_name", title.strip())

    @Slot(int, int)
    def moveField(self, source, target):
        values = self._data.get("placeholders", [])
        if 0 <= source < len(values) and 0 <= target < len(values) and source != target:
            values.insert(target, values.pop(source))
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
            guides[index]["pos"] = position
            self.notify(True)

    @Slot(str, bool)
    def guideOption(self, option, value):
        if option in ("guidelines_visible", "guidelines_locked"):
            self._data[option] = value
            self.notify(True)

    @Slot()
    def undo(self):
        state = self.history.undo()
        if state is not None:
            self._data = deepcopy(state)
            self._selected = ""
            self.notify()

    @Slot()
    def redo(self):
        state = self.history.redo()
        if state is not None:
            self._data = deepcopy(state)
            self._selected = ""
            self.notify()
