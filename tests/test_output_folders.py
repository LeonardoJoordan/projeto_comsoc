from pathlib import Path

from PySide6.QtCore import QSettings

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
