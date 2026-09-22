import os
from pathlib import Path

from PySide6.QtCore import QSettings
from core import paths, settings


def test_application_preferences_use_test_ini_and_preserve_migration():
    root = Path(os.environ['FORNAX_TEST_ROOT'])
    current = settings.get_app_settings()
    legacy = settings.QSettings(settings.LEGACY_SETTINGS_ORGANIZATION,
                                settings.LEGACY_SETTINGS_APPLICATION)
    for store in (current, legacy):
        assert store.format() == QSettings.Format.IniFormat
        assert Path(store.fileName()).resolve().is_relative_to(root)
        assert not store.fallbacksEnabled()
    assert current.value(settings.MIGRATION_MARKER, False, type=bool)


def test_application_files_and_temporary_storage_are_isolated():
    root = Path(os.environ['FORNAX_TEST_ROOT'])
    for directory in (paths.get_app_data_dir(), paths.get_legacy_app_data_dir(),
                      paths.get_models_dir(), paths.get_logs_dir(), paths.get_temp_dir()):
        assert directory.resolve().is_relative_to(root)
