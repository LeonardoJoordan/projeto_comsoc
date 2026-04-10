from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QComboBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QResizeEvent
from pathlib import Path

class ResizingLabel(QLabel):
    """QLabel que redimensiona a imagem interna automaticamente mantendo proporção."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(200)
        self._pixmap = None

    def set_image_path(self, path: str):
        if not path or not Path(path).exists():
            self.setText("Sem imagem")
            self._pixmap = None
            return
        
        self._pixmap = QPixmap(path)
        self._update_view()

    def set_pixmap_direct(self, pixmap: QPixmap):
        if not pixmap or pixmap.isNull():
            self.setText("Erro na prévia")
            self._pixmap = None
        else:
            self._pixmap = pixmap
            self._update_view()

    def resizeEvent(self, event: QResizeEvent):
        self._update_view()
        super().resizeEvent(event)

    def _update_view(self):
        if self._pixmap and not self._pixmap.isNull():
            w = self.width()
            h = self.height()
            scaled = self._pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            super().setPixmap(scaled)
        elif not self.text():
            self.setText("Sem prévia")

    
class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("Selecione o modelo")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        self.cbo_models = QComboBox()
        self.cbo_models.setMinimumHeight(34)
        layout.addWidget(self.cbo_models)

        self.preview = ResizingLabel()
        self.preview.setText("Nenhum modelo selecionado")
        self.preview.setFrameShape(QFrame.Shape.StyledPanel)
        self.preview.setStyleSheet("background-color: #2a2a2a; border-radius: 10px;")
        layout.addWidget(self.preview, 1)

    def set_preview_text(self, text: str):
        self.preview.setText(text)

    def set_preview_image(self, path: str):
        self.preview.set_image_path(path)

    def set_preview_pixmap(self, pixmap: QPixmap):
        self.preview.set_pixmap_direct(pixmap)