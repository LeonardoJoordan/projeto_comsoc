import os
import platform
import shutil
from pathlib import Path


APP_ID = "com.leobelisario.FornaxForge"
LEGACY_APP_ID = "com.leobelisario.ProjetoComSoc"
WINDOWS_APP_DIR = "FornaxForge"
LEGACY_WINDOWS_APP_DIR = "ProjetoComSoc"


def _data_home() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("APPDATA") or Path.home())
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def get_legacy_app_data_dir() -> Path:
    """Retorna a antiga pasta de dados sem criá-la ou modificá-la."""
    name = LEGACY_WINDOWS_APP_DIR if platform.system() == "Windows" else LEGACY_APP_ID
    return _data_home() / name


def _copy_missing(source: Path, destination: Path) -> None:
    """Copia somente entradas ausentes, preservando origem e conflitos."""
    if not source.is_dir() or source.resolve() == destination.resolve():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            _copy_missing(item, target)
        elif not target.exists():
            shutil.copy2(item, target)


def get_app_data_dir() -> Path:
    """Retorna os dados do FORNAX e importa, por cópia, dados antigos ausentes."""
    name = WINDOWS_APP_DIR if platform.system() == "Windows" else APP_ID
    app_dir = _data_home() / name
    app_dir.mkdir(parents=True, exist_ok=True)
    _copy_missing(get_legacy_app_data_dir(), app_dir)
    return app_dir

def get_logs_dir() -> Path:
    logs_dir = get_app_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def get_models_dir() -> Path:
    models_dir = get_app_data_dir() / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir
