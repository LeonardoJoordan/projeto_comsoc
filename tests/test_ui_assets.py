import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Permite executar este arquivo diretamente, além de usá-lo via pytest.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from core.resources import (
    action_icon_path, align_icon_path, navigation_icon_path, object_icon_path,
    state_icon_path,
)
from core.ui_font import install_ui_font


def test_bundled_inter_font_is_registered_and_applied():
    app = QApplication.instance() or QApplication([])

    assert install_ui_font(app) == "Inter 18pt"
    assert app.font().family() == "Inter 18pt"
    styles = QFontDatabase.styles("Inter 18pt")
    assert "Bold" in styles
    assert "ExtraBold" in styles


def test_object_icons_are_valid_svg_icons():
    app = QApplication.instance() or QApplication([])

    for name in (
        "text", "shapes", "image", "signature", "quantity",
        "square", "circle", "line",
    ):
        path = object_icon_path(name)
        assert path.is_file()
        assert not QIcon(str(path)).pixmap(24, 24).isNull()


def test_guide_icons_are_valid_svg_icons():
    app = QApplication.instance() or QApplication([])

    for name in (
        "guide", "h.guide", "v.guide", "l.guide", "lock", "unlock", "eye",
        "opacity",
    ):
        path = state_icon_path(name)
        assert path.is_file()
        assert not QIcon(str(path)).pixmap(24, 24).isNull()


def test_action_icons_are_valid_svg_icons():
    app = QApplication.instance() or QApplication([])

    for name in (
        "link", "lock ratio", "unlock ratio", "rotate-left", "rotate-right",
        "undo", "redo", "delete", "duplicate", "edit", "expand-content",
        "more", "more-vertical", "group",
    ):
        path = action_icon_path(name)
        assert path.is_file()
        assert not QIcon(str(path)).pixmap(24, 24).isNull()


def test_alignment_icons_are_valid_svg_icons():
    app = QApplication.instance() or QApplication([])

    for name in (
        "bot-alignment", "center-align", "justify", "left-align", "line-space",
        "mid-alignment", "paragraph", "right-align", "top-alignment",
        "bold", "italic", "underline", "straight_edge", "curved_edge",
        "sup_esq", "sup_dir", "inf_esq", "inf_dir",
    ):
        path = align_icon_path(name)
        assert path.is_file()
        assert not QIcon(str(path)).pixmap(24, 24).isNull()


def test_navigation_icons_are_valid_svg_icons():
    app = QApplication.instance() or QApplication([])

    for name in (
        "chevron-down", "chevron-up", "double-chevron-left",
        "double-chevron-right", "left-arrow", "right-arrow", "layer-child",
        "spin-up", "spin-down", "combo-down",
    ):
        path = navigation_icon_path(name)
        assert path.is_file()
        assert not QIcon(str(path)).pixmap(24, 24).isNull()


if __name__ == "__main__":
    checks = (
        test_bundled_inter_font_is_registered_and_applied,
        test_object_icons_are_valid_svg_icons,
        test_guide_icons_are_valid_svg_icons,
        test_action_icons_are_valid_svg_icons,
        test_alignment_icons_are_valid_svg_icons,
        test_navigation_icons_are_valid_svg_icons,
    )
    for check in checks:
        check()
        print(f"OK: {check.__name__}")
