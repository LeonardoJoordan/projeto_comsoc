import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.resources import object_icon_path, state_icon_path
from core.ui_font import install_ui_font


def test_bundled_inter_font_is_registered_and_applied():
    app = QApplication.instance() or QApplication([])

    assert install_ui_font(app) == "Inter"
    assert app.font().family() == "Inter"


def test_object_icons_are_valid_svg_icons():
    app = QApplication.instance() or QApplication([])

    for name in ("text", "shapes", "image", "signature", "quantity"):
        path = object_icon_path(name)
        assert path.is_file()
        assert not QIcon(str(path)).pixmap(24, 24).isNull()


def test_guide_icons_are_valid_svg_icons():
    app = QApplication.instance() or QApplication([])

    for name in ("guide", "h.guide", "v.guide", "l.guide", "lock", "unlock", "eye"):
        path = state_icon_path(name)
        assert path.is_file()
        assert not QIcon(str(path)).pixmap(24, 24).isNull()
