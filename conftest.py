"""Isolate application storage before pytest imports any test modules."""
from pathlib import Path
import tempfile
import pytest

from tests.isolated_environment import activate


def pytest_configure(config):
    evidence = Path(__file__).parent / 'build' / 'security'
    evidence.mkdir(parents=True, exist_ok=True)
    root = tempfile.mkdtemp(prefix='windows-tests-data-', dir=evidence)
    config._fornax_test_root = activate(root)
    from PySide6.QtWidgets import QApplication
    from core.ui_font import install_ui_font
    config._fornax_qapp = QApplication.instance() or QApplication([])
    config._fornax_qapp.setStyle('Fusion')
    install_ui_font(config._fornax_qapp)


def pytest_report_header(config):
    return f'FORNAX isolated storage: {config._fornax_test_root}'


@pytest.fixture(autouse=True)
def dispose_test_windows():
    # Most legacy unittest cases do not use qtbot. A closed QWidget can still
    # be retained by Qt/callbacks, affecting later theme/layout tests.
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    from shiboken6 import isValid
    app = QApplication.instance()
    previous = set(app.topLevelWidgets()) if app else set()
    yield
    app = QApplication.instance()
    if app:
        for widget in app.topLevelWidgets():
            if widget not in previous and isValid(widget):
                widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
