"""Ícones de ferramentas seguem o tema; a marca e imagens da arte não mudam."""
from PySide6.QtGui import QIcon, QIconEngine, QPixmap, QPainter
from PySide6.QtCore import Qt
from PySide6.QtSvg import QSvgRenderer
from core.themes import theme_color


class ToolIconEngine(QIconEngine):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.renderer = None
        self.color = None

    def clone(self):
        return ToolIconEngine(self.path)

    def paint(self, painter, rect, mode, state):
        color = theme_color('disabled' if mode == QIcon.Mode.Disabled else 'icon')
        if self.color != color:
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{self.path}</g></svg>'
            self.renderer = QSvgRenderer(svg.encode())
            self.color = color
        self.renderer.render(painter, rect)

    def pixmap(self, size, mode, state):
        pix = QPixmap(size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        self.paint(painter, pix.rect(), mode, state)
        painter.end()
        return pix


def tool_icon(path):
    return QIcon(ToolIconEngine(path))
