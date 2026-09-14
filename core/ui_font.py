"""Fonte incorporada usada exclusivamente pela interface do aplicativo."""

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from core.resources import PROJECT_ROOT


UI_FONT_FAMILY = "Inter"


def install_ui_font(app: QApplication) -> str:
    font_dir = PROJECT_ROOT / "assets" / "fonts" / "ui"
    files = (
        font_dir / "Inter-VariableFont_opsz,wght.ttf",
        font_dir / "Inter-Italic-VariableFont_opsz,wght.ttf",
    )
    families = []
    for path in files:
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id >= 0:
            families.extend(QFontDatabase.applicationFontFamilies(font_id))

    family = UI_FONT_FAMILY if UI_FONT_FAMILY in families else (families[0] if families else "")
    if family:
        font = app.font()
        font.setFamily(family)
        app.setFont(font)
    return family
