from core.themes import themed_style, theme_color, theme_manager
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QComboBox, QPushButton, QSpinBox)
from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtGui import QPixmap, QResizeEvent, QImageReader
from pathlib import Path

class ResizingLabel(QLabel):
    """QLabel que redimensiona a imagem interna automaticamente mantendo proporção."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(200)
        self._pixmap = None

    def set_image_path(self, path: str):
        image_path = Path(path) if path else None
        if not image_path or not image_path.exists():
            self._pixmap = None
            self.setText("Sem imagem")
            return

        reader = QImageReader(str(image_path))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            self._pixmap = None
            self.setText("Erro na prévia")
            return

        self._pixmap = QPixmap.fromImage(image)
        self._update_view()

    def set_pixmap_direct(self, pixmap: QPixmap):
        if not pixmap or pixmap.isNull():
            self._pixmap = None
            self.setText("Erro na prévia")
        else:
            self._pixmap = pixmap
            self._update_view()

    def set_message(self, text: str):
        self._pixmap = None
        self.setText(text)

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
    modeChanged = Signal(str)
    indexRequested = Signal(int)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("Selecione o modelo")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        themed_style(title, "font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        self.cbo_models = QComboBox()
        self.cbo_models.setMinimumHeight(34)
        layout.addWidget(self.cbo_models)

        self.preview = ResizingLabel()
        self.preview.setText("Nenhum modelo selecionado")
        self.preview.setFrameShape(QFrame.Shape.StyledPanel)
        themed_style(self.preview, "background-color: @canvas@; border-radius: 10px;")
        layout.addWidget(self.preview, 1)

        navigation_stack = QVBoxLayout()
        navigation_stack.setContentsMargins(0, 0, 0, 0)
        navigation_stack.setSpacing(4)

        page_navigation = QHBoxLayout()
        page_navigation.setContentsMargins(0, 0, 0, 0)
        page_navigation.setSpacing(5)
        page_navigation.addStretch(1)

        self.btn_previous = QPushButton("‹")
        self.btn_previous.setObjectName("previewPrevious")
        self.btn_previous.setFixedSize(24, 22)
        self.btn_previous.setToolTip("Registro anterior")
        page_navigation.addWidget(self.btn_previous)

        self.lbl_navigation_kind = QLabel("Registro")
        self.lbl_navigation_kind.setObjectName("previewNavigationLabel")
        self.lbl_navigation_kind.setFixedWidth(50)
        self.lbl_navigation_kind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_navigation.addWidget(self.lbl_navigation_kind)

        self.spin_navigation = QSpinBox()
        self.spin_navigation.setObjectName("previewNavigationIndex")
        self.spin_navigation.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_navigation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_navigation.setFixedSize(52, 22)
        self.spin_navigation.setRange(1, 1)
        self.spin_navigation.valueChanged.connect(lambda value: self.indexRequested.emit(value - 1))
        page_navigation.addWidget(self.spin_navigation)

        self.lbl_navigation_total = QLabel("de 0")
        self.lbl_navigation_total.setObjectName("previewNavigationLabel")
        self.lbl_navigation_total.setFixedWidth(50)
        self.lbl_navigation_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_navigation.addWidget(self.lbl_navigation_total)

        self.btn_next = QPushButton("›")
        self.btn_next.setObjectName("previewNext")
        self.btn_next.setFixedSize(24, 22)
        self.btn_next.setToolTip("Próximo registro")
        page_navigation.addWidget(self.btn_next)
        page_navigation.addStretch(1)
        navigation_stack.addLayout(page_navigation)

        mode_navigation = QHBoxLayout()
        mode_navigation.setContentsMargins(0, 0, 0, 0)
        mode_navigation.addStretch(1)
        self.cbo_preview_mode = QComboBox()
        self.cbo_preview_mode.setObjectName("previewMode")
        self.cbo_preview_mode.addItem("Item", "item")
        self.cbo_preview_mode.setFixedSize(166, 22)
        self.cbo_preview_mode.currentIndexChanged.connect(self._emit_mode)
        mode_navigation.addWidget(self.cbo_preview_mode)
        mode_navigation.addStretch(1)
        navigation_stack.addLayout(mode_navigation)
        layout.addLayout(navigation_stack)

        self.btn_previous.clicked.connect(lambda: self.indexRequested.emit(self.spin_navigation.value() - 2))
        self.btn_next.clicked.connect(lambda: self.indexRequested.emit(self.spin_navigation.value()))
        self.set_navigation("item", 0, 0, sheet_available=False)

    def _emit_mode(self):
        self.modeChanged.emit(self.cbo_preview_mode.currentData() or "item")

    def set_navigation(self, mode: str, index: int, total: int, *, sheet_available: bool):
        current_mode = self.cbo_preview_mode.currentData()
        with QSignalBlocker(self.cbo_preview_mode):
            self.cbo_preview_mode.clear()
            self.cbo_preview_mode.addItem("Item", "item")
            if sheet_available:
                self.cbo_preview_mode.addItem("Folha de impressão", "sheet")
            wanted = mode if mode == "item" or sheet_available else "item"
            selected = self.cbo_preview_mode.findData(wanted)
            self.cbo_preview_mode.setCurrentIndex(max(0, selected))

        total = max(0, total)
        index = min(max(0, index), max(0, total - 1))
        with QSignalBlocker(self.spin_navigation):
            self.spin_navigation.setRange(1, max(1, total))
            self.spin_navigation.setValue(index + 1)
        self.lbl_navigation_kind.setText("Folha" if wanted == "sheet" else "Item")
        self.lbl_navigation_total.setText(f"de {total}")
        enabled = total > 0
        self.spin_navigation.setEnabled(enabled)
        self.btn_previous.setEnabled(enabled and index > 0)
        self.btn_next.setEnabled(enabled and index + 1 < total)
        if current_mode != wanted:
            self.cbo_preview_mode.setToolTip(
                "Visualize um item ou a folha final conforme a predefinição de impressão."
            )

    def set_preview_text(self, text: str):
        self.preview.set_message(text)

    def set_preview_image(self, path: str):
        self.preview.set_image_path(path)

    def set_preview_pixmap(self, pixmap: QPixmap):
        self.preview.set_pixmap_direct(pixmap)
