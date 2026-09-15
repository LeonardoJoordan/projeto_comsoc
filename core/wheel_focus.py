"""Impede alterações acidentais em seletores durante a rolagem de painéis."""

from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtWidgets import QAbstractScrollArea, QAbstractSpinBox, QComboBox, QLineEdit


class WheelFocusGuard(QObject):
    """Só permite que seletores processem a roda quando possuem foco."""

    def eventFilter(self, watched, event):
        # Spinboxes e comboboxes editáveis também recebem eventos pelo editor
        # interno. O foco, sozinho, não prova que o usuário clicou no campo:
        # o Qt pode atribuí-lo automaticamente ao abrir a janela ou pela roda.
        if isinstance(watched, QLineEdit):
            watched = watched.parentWidget()
        if not isinstance(watched, (QComboBox, QAbstractSpinBox)):
            return False
        kind = event.type()
        if kind == QEvent.Type.Polish:
            watched.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        elif kind == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                watched.setProperty('_wheel_clicked', True)
        elif kind == QEvent.Type.FocusOut:
            popup_open = isinstance(watched, QComboBox) and watched.view().isVisible()
            if not popup_open and event.reason() not in (
                Qt.FocusReason.PopupFocusReason, Qt.FocusReason.ActiveWindowFocusReason,
            ):
                watched.setProperty('_wheel_clicked', False)
        if kind != QEvent.Type.Wheel:
            return False
        if watched.hasFocus() and watched.property('_wheel_clicked'):
            return False

        # O controle está apenas sob o cursor. Aplicar a rolagem ao painel
        # ancestral conserva o comportamento esperado da barra lateral.
        scroll_area = watched.parentWidget()
        while scroll_area is not None and not isinstance(scroll_area, QAbstractScrollArea):
            scroll_area = scroll_area.parentWidget()
        if scroll_area is not None:
            horizontal = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            delta = event.angleDelta().x() if horizontal else event.angleDelta().y()
            bar = scroll_area.horizontalScrollBar() if horizontal else scroll_area.verticalScrollBar()
            if not delta and not event.pixelDelta().isNull():
                delta = event.pixelDelta().x() if horizontal else event.pixelDelta().y()
                step = 1
            else:
                step = max(1, bar.singleStep() * 3) / 120
            if delta:
                bar.setValue(round(bar.value() - delta * step))
        event.accept()
        return True


_guard = None


def install_wheel_focus_guard(app):
    """Instala uma única proteção para todos os seletores da aplicação."""
    global _guard
    if _guard is None:
        _guard = WheelFocusGuard(app)
        app.installEventFilter(_guard)
    return _guard
