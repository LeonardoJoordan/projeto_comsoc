import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication, QComboBox, QFontComboBox, QDoubleSpinBox, QScrollArea, QWidget
from PySide6.QtTest import QTest
import pytest

from core.wheel_focus import install_wheel_focus_guard


def _wheel(target, delta=-120):
    event = QWheelEvent(
        QPointF(5, 5), QPointF(5, 5), QPoint(), QPoint(0, delta),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )
    QApplication.sendEvent(target, event)


@pytest.mark.parametrize('control_type', [QComboBox, QFontComboBox, QDoubleSpinBox])
def test_wheel_requires_click_even_with_automatic_focus(control_type):
    app = QApplication.instance() or QApplication([])
    install_wheel_focus_guard(app)
    area = QScrollArea()
    content = QWidget()
    content.setMinimumHeight(1000)
    combo = control_type(content)
    if isinstance(combo, QComboBox):
        combo.clear()
        combo.addItems(["Primeira", "Segunda", "Terceira"])
        combo.setCurrentIndex(1)
        value = combo.currentIndex
    else:
        combo.setValue(20)
        value = combo.value
    combo.resize(160, 30)
    area.setWidget(content)
    area.resize(200, 200)
    area.show()
    app.processEvents()

    combo.setFocus(Qt.FocusReason.OtherFocusReason)
    initial = value()
    _wheel(combo)
    assert value() == initial
    assert area.verticalScrollBar().value() > 0

    area.verticalScrollBar().setValue(0)
    QTest.mouseClick(combo, Qt.MouseButton.LeftButton, pos=QPoint(10, 15))
    if isinstance(combo, QComboBox):
        combo.hidePopup()
    area.activateWindow()
    app.processEvents()
    combo.setFocus(Qt.FocusReason.MouseFocusReason)
    _wheel(combo)
    assert value() != initial
    combo.clearFocus()
    previous = value()
    _wheel(combo)
    assert value() == previous
    area.close()
