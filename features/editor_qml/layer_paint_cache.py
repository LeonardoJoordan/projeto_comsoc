"""Pintura local reutilizável; preparar na GUI e reproduzir na cena Qt Quick.

Usado pelo modelo de camadas do canvas. A posição fica com o consumidor; rotação e
opacidade permanecem nos comandos para conservar as regras do renderer.
"""
from copy import deepcopy
from pathlib import Path

from PySide6.QtGui import QPainter, QPicture, QTransform
from PySide6.QtCore import QRectF
from core.text_layout import build_document, text_geometry, resolve_rich_text
from core.object_style import outline_margin
from core.document_layers import GROUPS
from features.generator.renderer import NativeRenderer


class LayerPaintCache:
    def __init__(self):
        self._entries = {}
        self._assets = {}
        self._renderer = NativeRenderer({"canvas_size": {"w": 1, "h": 1}})
        self.recordings = 0

    def retain(self, keys):
        """Liberar conteúdo de objetos excluídos e imagens não utilizadas."""
        keep = set(keys)
        self._entries = {key: value for key, value in self._entries.items() if key in keep}
        paths = {entry[0][1].get("path") for entry in self._entries.values()}
        self._assets = {path: stamp for path, stamp in self._assets.items() if path in paths}
        self._renderer._image_cache = {path: image for path, image in self._renderer._image_cache.items()
                                       if path in paths}

    def picture(self, key, kind, item, row_rich=None):
        """Retorna QPicture imutável por convenção, com origem na posição do objeto.

        Assets devem chegar com caminho absoluto, como em bridge.render_data().
        O chamador aplica visibilidade e translação X/Y; nunca modifica o retorno.
        Sem valores explícitos, exibe os placeholders usados na prévia do editor.
        """
        local = deepcopy(item)
        for field in ("x", "y", "locked", "custom_name", "layer_id", "z_value",
                      "has_link", "link_key", "object_id", "visible"):
            local.pop(field, None)
        local.update(x=0, y=0, visible=True, object_id=key)
        values = deepcopy(row_rich) if row_rich is not None else None
        path = local.get("path")
        stamp = None
        if path:
            try:
                stat = Path(path).stat()
                stamp = (stat.st_mtime_ns, stat.st_size)
            except OSError:
                pass
            if path not in self._assets or self._assets[path] != stamp:
                self._renderer._image_cache.pop(path, None)
                self._assets[path] = stamp
        signature = (kind, local, values, stamp)
        cached = self._entries.get(key)
        if cached and cached[0] == signature:
            return cached[1]

        template = {"canvas_size": {"w": 1, "h": 1}, "layer_order": [key],
                    GROUPS[kind]: [local]}
        self._renderer.tpl = template
        if values is None:
            from core.text_layout import variables_in_html
            values = {name: "{" + name + "}" for name in variables_in_html(local.get("html", ""))}
        picture = QPicture()
        painter = QPainter(picture)
        try:
            self._renderer._paint_card(painter, values)
        finally:
            painter.end()
        if kind == 'text':
            # QPicture não calcula bounds confiáveis para os glifos de QTextDocument.
            # Reservar a extensão do layout, inclusive transbordamento e contorno.
            resolved = (resolve_rich_text(local, values) if local.get('rich_text_version') == 1
                        else self._renderer.resolve_html(local.get('html', ''), values))
            doc = build_document(local, resolved or '')
            offset, _, _ = text_geometry(doc, local)
            w, h = local.get('w', 300), local.get('h', 100)
            margin = outline_margin(local) + 2
            bounds = QRectF(-margin, offset-margin, w+2*margin, doc.size().height()+2*margin)
            transform = QTransform()
            transform.translate(w/2, h/2)
            transform.rotate(local.get('rotation', 0))
            transform.translate(-w/2, -h/2)
            picture.setBoundingRect(transform.mapRect(bounds).toAlignedRect())
        self._entries[key] = (signature, picture)
        self.recordings += 1
        return picture
