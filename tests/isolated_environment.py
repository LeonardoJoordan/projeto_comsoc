"""Storage isolation for pytest and its explicit crash-test subprocess."""
import os
from pathlib import Path
import tempfile


def activate(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.environ['FORNAX_TEST_ROOT'] = str(root)
    for variable, directory in (
        ('APPDATA', 'data'), ('LOCALAPPDATA', 'local'),
        ('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'),
        ('XDG_CACHE_HOME', 'cache'), ('TMP', 'tmp'), ('TEMP', 'tmp'),
        ('TMPDIR', 'tmp'),
    ):
        path = root / directory
        path.mkdir(exist_ok=True)
        os.environ[variable] = str(path)
    tempfile.tempdir = str(root / 'tmp')

    from PySide6.QtCore import QSettings
    from core import paths, settings

    original_data_home = paths._data_home

    def isolated_data_home():
        if paths.platform.system() == 'Darwin':
            return root / 'data'
        return original_data_home()

    paths._data_home = isolated_data_home

    def isolated_settings(organization, application):
        # The (organization, application) constructor ignores defaultFormat
        # on Windows. Use the explicit filename overload, never the registry.
        path = root / 'config' / organization / f'{application}.ini'
        path.parent.mkdir(parents=True, exist_ok=True)
        result = QSettings(str(path), QSettings.Format.IniFormat)
        result.setFallbacksEnabled(False)
        return result

    settings.QSettings = isolated_settings
    return root
