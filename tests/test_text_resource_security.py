import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QTextDocument

from core.html_utils import sanitize_text_html
from core.text_layout import build_document


def _text_box():
    return {
        "html": "<p>Texto</p>",
        "font_family": "Inter",
        "font_size": 16,
        "font_color": "#000000",
        "w": 300,
        "h": 100,
        "rich_text_version": 1,
    }


def test_text_document_does_not_load_an_external_image(tmp_path):
    image = tmp_path / "private.png"
    image.write_bytes(b"not needed: the resource must never be opened")
    url = QUrl.fromLocalFile(str(image))

    document = build_document(_text_box(), f'<p>Permitido</p><img src="{url.toString()}">')

    assert document.toPlainText().strip() == "Permitido"
    assert document.resource(QTextDocument.ResourceType.ImageResource, url) is None


def test_text_sanitizer_keeps_supported_rich_formatting():
    html = '<p><b>Negrito</b> <i>itálico</i> <u>sublinhado</u><img src="x.png"></p>'

    cleaned = sanitize_text_html(html)
    document = build_document(_text_box(), cleaned)

    assert "img" not in cleaned.lower()
    assert document.toPlainText().strip() == "Negrito itálico sublinhado"
    assert "font-weight" in document.toHtml().lower()
