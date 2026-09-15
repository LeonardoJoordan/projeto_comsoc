import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from core.i18n import initialize_i18n, set_preferred_locale, tr


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
