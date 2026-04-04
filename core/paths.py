import os
import platform
from pathlib import Path

def get_app_data_dir() -> Path:
    """Retorna o diretório base de dados do usuário conforme o SO."""
    system = platform.system()
    app_name = "ProjetoComSoc"
    
    if system == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return Path(base) / app_name
    elif system == "Darwin":
        return Path(os.path.expanduser("~")) / "Library" / "Application Support" / app_name
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
        return Path(base) / app_name

def get_logs_dir() -> Path:
    """Retorna e garante a existência da pasta de logs."""
    logs_dir = get_app_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def get_models_dir() -> Path:
    """Retorna e garante a existência da pasta de modelos."""
    models_dir = get_app_data_dir() / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir
