"""Destaques reutilizáveis para os tutoriais interativos."""

from __future__ import annotations

import math

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QRegion
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.i18n import tr
from core.themes import theme_color, themed_style
from core.dialog_buttons import ACCEPT_STYLE, CANCEL_STYLE


class Spotlight(QWidget):
    """Escurece a janela e mantém um alvo visualmente destacado."""

    def __init__(self, host: QWidget):
        super().__init__(host)
        self._host = host
        self._target_rect = QRect()
        self._phase = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()
        self._pulse = QTimer(self)
        self._pulse.setInterval(35)
        self._pulse.timeout.connect(self._advance_pulse)

    def set_target_rect(self, rect: QRect):
        self._target_rect = QRect(rect)
        if self._target_rect.isValid():
            # O recorte físico garante que o controle destacado receba o
            # mouse diretamente, inclusive em backends onde uma camada
            # transparente ainda pode capturar o evento.
            hole = self._target_rect.adjusted(-3, -3, 3, 3)
            self.setMask(QRegion(self.rect()).subtracted(QRegion(hole)))
        else:
            self.clearMask()
        self.update()

    def start(self):
        self.setGeometry(self._host.rect())
        self.set_target_rect(self._target_rect)
        self.show()
        self.raise_()
        self._pulse.start()

    def stop(self):
        self._pulse.stop()
        self.hide()

    def _advance_pulse(self):
        self._phase = (self._phase + 0.13) % (math.pi * 2)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        full = QPainterPath()
        full.addRect(self.rect())
        if self._target_rect.isValid():
            hole = QPainterPath()
            hole.addRoundedRect(self._target_rect, 8, 8)
            full = full.subtracted(hole)
        painter.fillPath(full, QColor(0, 0, 0, 158))

        if self._target_rect.isValid():
            pulse = (math.sin(self._phase) + 1.0) / 2.0
            color = QColor(theme_color("accent"))
            color.setAlpha(150 + int(105 * pulse))
            painter.setPen(QPen(color, 2.0 + pulse))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self._target_rect, 8, 8)


class TutorialCard(QFrame):
    backRequested = Signal()
    nextRequested = Signal()
    skipRequested = Signal()

    def __init__(self, host: QWidget):
        super().__init__(host)
        self._host = host
        self._drag_offset = None
        self._manually_positioned = False
        self.setObjectName("tutorialCard")
        self.setMinimumWidth(330)
        self.setMaximumWidth(410)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(9)
        self.progress = QLabel()
        self.progress.setObjectName("tutorialProgress")
        self.title = QLabel()
        self.title.setObjectName("tutorialTitle")
        self.body = QLabel()
        self.body.setObjectName("tutorialBody")
        self.body.setWordWrap(True)
        for label in (self.progress, self.title, self.body):
            label.installEventFilter(self)
        layout.addWidget(self.progress)
        layout.addWidget(self.title)
        layout.addWidget(self.body)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.skip = QPushButton(tr("Pular tutorial"))
        self.back = QPushButton(tr("Voltar"))
        self.next = QPushButton(tr("Continuar"))
        self.next.setObjectName("primary")
        self.skip.clicked.connect(self.skipRequested)
        self.back.clicked.connect(self.backRequested)
        self.next.clicked.connect(self.nextRequested)
        buttons.addWidget(self.skip)
        buttons.addStretch(1)
        buttons.addWidget(self.back)
        buttons.addWidget(self.next)
        layout.addLayout(buttons)

        themed_style(self, """
            QFrame#tutorialCard {
                background: @panel@; border: 1px solid @accent@;
                border-radius: 10px;
            }
            QLabel#tutorialProgress { color: @accent@; font-size: 10px; font-weight: 600; }
            QLabel#tutorialTitle { color: @text@; font-size: 15px; font-weight: 700; }
            QLabel#tutorialBody { color: @muted@; font-size: 12px; }
        """)
        themed_style(self.next, ACCEPT_STYLE)
        themed_style(self.skip, CANCEL_STYLE)
        themed_style(self.back, """
            QPushButton {
                background: @button@; color: @text@; border: 1px solid @border@;
                border-radius: 5px; padding: 0 14px; text-align: center;
                font-weight: 600;
            }
            QPushButton:hover { background: @hover@; border-color: @border_strong@; }
            QPushButton:pressed { background: @selection@; border-color: @accent@; }
        """)
        self.equalize_buttons()

    def reset_manual_position(self):
        self._manually_positioned = False
        self._drag_offset = None

    def _begin_drag(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self._manually_positioned = True
        return True

    def _drag(self, event):
        if self._drag_offset is None or not event.buttons() & Qt.MouseButton.LeftButton:
            return False
        desired_global = event.globalPosition().toPoint() - self._drag_offset
        desired = self._host.mapFromGlobal(desired_global)
        margin = 8
        desired.setX(max(margin, min(desired.x(), self._host.width() - self.width() - margin)))
        desired.setY(max(margin, min(desired.y(), self._host.height() - self.height() - margin)))
        self.move(desired)
        return True

    def _end_drag(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self._drag_offset is None:
            return False
        self._drag_offset = None
        return True

    def mousePressEvent(self, event):
        if self._begin_drag(event):
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag(event):
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._end_drag(event):
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def eventFilter(self, watched, event):
        if watched in (self.progress, self.title, self.body):
            if event.type() == QEvent.Type.MouseButtonPress and self._begin_drag(event):
                return True
            if event.type() == QEvent.Type.MouseMove and self._drag(event):
                return True
            if event.type() == QEvent.Type.MouseButtonRelease and self._end_drag(event):
                return True
        return super().eventFilter(watched, event)

    def equalize_buttons(self):
        buttons = (self.skip, self.back, self.next)
        width = max(96, *(button.sizeHint().width() for button in buttons))
        height = max(30, *(button.sizeHint().height() for button in buttons))
        for button in buttons:
            button.setFixedSize(width, height)


class CoachMark(QObject):
    """Controla o destaque e o cartão de uma etapa em uma janela."""

    def __init__(self, host: QWidget):
        super().__init__(host)
        self.host = host
        self.target = None
        self.target_rect_provider = None
        self.spotlight = Spotlight(host)
        self.card = TutorialCard(host)
        self.card.hide()
        host.installEventFilter(self)

    def show_step(
        self,
        *,
        target: QWidget | None,
        title: str,
        body: str,
        current: int,
        total: int,
        can_go_back: bool,
        next_text: str,
        wait_for_action: bool = False,
        target_rect_provider=None,
    ):
        if self.target is not None:
            self.target.removeEventFilter(self)
        self.target = target
        self.target_rect_provider = target_rect_provider
        if target is not None:
            target.installEventFilter(self)
        self.card.progress.setText(tr("ETAPA {atual} DE {total}").format(atual=current, total=total))
        self.card.title.setText(title)
        self.card.body.setText(body)
        self.card.back.setVisible(can_go_back)
        self.card.next.setVisible(not wait_for_action)
        self.card.next.setText(next_text)
        self.card.equalize_buttons()
        self.card.reset_manual_position()
        self.spotlight.start()
        self.card.adjustSize()
        self.card.show()
        self.reposition()
        self.card.raise_()

    def reposition(self):
        self.spotlight.setGeometry(self.host.rect())
        target_rect = QRect()
        if self.target_rect_provider is not None:
            try:
                provided = self.target_rect_provider()
                if provided is not None:
                    target_rect = QRect(provided)
            except (RuntimeError, TypeError):
                target_rect = QRect()
        elif self.target is not None and self.target.isVisible():
            top_left = self.target.mapTo(self.host, QPoint(0, 0))
            target_rect = QRect(top_left, self.target.size()).adjusted(-7, -7, 7, 7)
        self.spotlight.set_target_rect(target_rect)

        if self.card._manually_positioned:
            x = max(8, min(self.card.x(), self.host.width() - self.card.width() - 8))
            y = max(8, min(self.card.y(), self.host.height() - self.card.height() - 8))
            self.card.move(x, y)
            return

        margin = 18
        card_size = self.card.sizeHint()
        if target_rect.isValid():
            right_x = target_rect.right() + 18
            left_x = target_rect.left() - card_size.width() - 18
            bottom_y = target_rect.bottom() + 18
            top_y = target_rect.top() - card_size.height() - 18
            if right_x + card_size.width() <= self.host.width() - margin:
                x, y = right_x, target_rect.center().y() - card_size.height() // 2
            elif left_x >= margin:
                x, y = left_x, target_rect.center().y() - card_size.height() // 2
            elif bottom_y + card_size.height() <= self.host.height() - margin:
                x, y = target_rect.center().x() - card_size.width() // 2, bottom_y
            elif top_y >= margin:
                x, y = target_rect.center().x() - card_size.width() // 2, top_y
            else:
                x, y = target_rect.center().x() - card_size.width() // 2, margin
            x = max(margin, min(x, self.host.width() - card_size.width() - margin))
            y = max(margin, min(y, self.host.height() - card_size.height() - margin))
        else:
            x = max(margin, (self.host.width() - card_size.width()) // 2)
            y = max(margin, (self.host.height() - card_size.height()) // 2)
        self.card.move(x, y)

    def close(self):
        if self.target is not None:
            self.target.removeEventFilter(self)
            self.target = None
        self.target_rect_provider = None
        self.host.removeEventFilter(self)
        self.spotlight.stop()
        self.spotlight.deleteLater()
        self.card.hide()
        self.card.deleteLater()
        self.deleteLater()

    def eventFilter(self, watched, event):
        if event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Move,
            QEvent.Type.Show,
            QEvent.Type.LayoutRequest,
        ):
            QTimer.singleShot(0, self.reposition)
        return False
