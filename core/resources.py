"""Localização centralizada dos recursos distribuídos com o aplicativo."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"


def app_icon_path(size: int = 256) -> Path:
    """Retorna o PNG do aplicativo mais adequado ao tamanho solicitado."""
    available = (32, 48, 64, 128, 256, 512, 1024)
    selected = min(available, key=lambda candidate: (abs(candidate - size), candidate < size))
    return ICONS_DIR / f"fornax-forge_{selected}.png"


def windows_icon_path() -> Path:
    return ICONS_DIR / "fornax-forge.ico"
