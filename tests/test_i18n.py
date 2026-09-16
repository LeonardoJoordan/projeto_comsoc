import os
import ast
import re
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from core.i18n import initialize_i18n, set_preferred_locale, tr


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = re.compile(r"\{[^{}]+\}")


def _translated_sources(locale):
    root = ET.parse(PROJECT_ROOT / "assets" / "translations" / f"fornax_{locale}.ts").getroot()
    return {
        message.findtext("source", ""): message.findtext("translation", "")
        for message in root.findall(".//message")
    }


def _interface_sources():
    sources = set()
    for directory in (PROJECT_ROOT / "core", PROJECT_ROOT / "features"):
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "tr"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    continue
                sources.add(node.args[0].value)
    return sources


def test_english_catalog_loads_and_portuguese_remains_the_source(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)

    set_preferred_locale(settings, "en_US")
    assert initialize_i18n(app, settings) == "en_US"
    assert tr("Programa") == "Application"
    assert tr("Dados para o modelo") == "Template data"

    set_preferred_locale(settings, "pt_BR")
    assert initialize_i18n(app, settings) == "pt_BR"
    assert tr("Programa") == "Programa"


def test_spanish_catalog_loads(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)

    set_preferred_locale(settings, "es_ES")
    assert initialize_i18n(app, settings) == "es_ES"
    assert tr("Programa") == "Programa"
    assert tr("Dados para o modelo") == "Datos para la plantilla"
    assert tr("Folha de impressão") == "Hoja de impresión"

    set_preferred_locale(settings, "pt_BR")
    assert initialize_i18n(app, settings) == "pt_BR"


def test_catalogs_cover_interface_texts_and_preserve_placeholders():
    sources = _interface_sources()
    for locale in ("en_US", "es_ES"):
        catalog = _translated_sources(locale)
        missing = sorted(source for source in sources if not catalog.get(source))
        assert not missing, f"Textos ausentes em {locale}: {missing}"
        for source in sources:
            assert sorted(PLACEHOLDER.findall(source)) == sorted(
                PLACEHOLDER.findall(catalog[source])
            ), f"Placeholders incompatíveis em {locale}: {source!r}"
