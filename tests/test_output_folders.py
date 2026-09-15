from pathlib import Path

from PySide6.QtCore import QSettings

from PySide6.QtWidgets import QApplication

from core.i18n import initialize_i18n, set_preferred_locale
from core.output_folders import FORGE_COUNTER_KEY, create_forge_output_dir


def _settings(path: Path):
    return QSettings(str(path), QSettings.Format.IniFormat)


def test_forge_counter_is_global_continuous_and_has_no_leading_zero(tmp_path):
    settings = _settings(tmp_path / "settings.ini")
    first_root = tmp_path / "primeiro-destino"
    second_root = tmp_path / "outro-destino"

    first, first_number = create_forge_output_dir(first_root, settings)
    second, second_number = create_forge_output_dir(second_root, settings)

    assert first_number == 1
    assert first.name == "FORNAX - Forja nº 1"
    assert second_number == 2
    assert second.name == "FORNAX - Forja nº 2"
    assert settings.value(FORGE_COUNTER_KEY, type=int) == 2


def test_existing_forge_advances_a_stale_counter_without_overwriting(tmp_path):
    settings = _settings(tmp_path / "settings.ini")
    base = tmp_path / "saída"
    base.mkdir()
    existing = base / "FORNAX - Forja nº 12"
    existing.mkdir()

    created, number = create_forge_output_dir(base, settings)

    assert existing.is_dir()
    assert number == 13
    assert created.name == "FORNAX - Forja nº 13"


def test_forge_folder_name_follows_the_selected_language(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = _settings(tmp_path / "settings.ini")
    base = tmp_path / "saída"

    set_preferred_locale(settings, "en_US")
    initialize_i18n(app, settings)
    english, english_number = create_forge_output_dir(base, settings)

    set_preferred_locale(settings, "es_ES")
    initialize_i18n(app, settings)
    spanish, spanish_number = create_forge_output_dir(base, settings)

    assert english_number == 1
    assert english.name == "FORNAX - Forge No. 1"
    assert spanish_number == 2
    assert spanish.name == "FORNAX - Forja n.º 2"

    set_preferred_locale(settings, "pt_BR")
    initialize_i18n(app, settings)


def test_stale_counter_recognizes_folders_created_in_other_languages(tmp_path):
    settings = _settings(tmp_path / "settings.ini")
    base = tmp_path / "saída"
    base.mkdir()
    (base / "FORNAX - Forge No. 8").mkdir()
    (base / "FORNAX - Forja n.º 12").mkdir()

    created, number = create_forge_output_dir(base, settings)

    assert number == 13
    assert created.name == "FORNAX - Forja nº 13"
