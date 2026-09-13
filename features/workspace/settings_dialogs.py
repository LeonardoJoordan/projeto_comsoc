"""Diálogos de exportação e preferências da interface."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)

from features.generator.export_dialog import ConfigDialog as ExportConfigDialog


class ThemeDialog(QDialog):
    def __init__(self, parent=None, is_dark=True):
        super().__init__(parent)
        self.setWindowTitle("Tema da interface")
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        title = QLabel("Tema da interface")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)
        layout.addWidget(QLabel("Escolha a aparência utilizada no workspace."))

        self.radio_dark = QRadioButton("Tema escuro")
        self.radio_light = QRadioButton("Tema claro")
        self.theme_group = QButtonGroup(self)
        self.theme_group.addButton(self.radio_dark)
        self.theme_group.addButton(self.radio_light)
        self.radio_dark.setChecked(bool(is_dark))
        self.radio_light.setChecked(not bool(is_dark))
        layout.addWidget(self.radio_dark)
        layout.addWidget(self.radio_light)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def is_dark_theme(self):
        return self.radio_dark.isChecked()
