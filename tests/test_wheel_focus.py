import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QApplication, QComboBox, QFontComboBox, QDoubleSpinBox, QScrollArea, QWidget
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
    guard = install_wheel_focus_guard(app)
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
    press = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress, QPointF(10, 15), QPointF(10, 15),
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    guard.eventFilter(combo, press)
    _wheel(combo)
    assert value() != initial
    # Perder o foco por causa do popup não desarma o seletor; somente um clique
    # externo deve devolver a roda ao painel.
    combo.clearFocus()
    previous = value()
    _wheel(combo, 120)
    assert value() != previous

    guard.eventFilter(content, press)
    previous = value()
    _wheel(combo)
    assert value() == previous
    area.close()
