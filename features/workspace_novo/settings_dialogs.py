"""Diálogos de preferências exclusivos da interface de transição."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from features.generator.export_dialog import ConfigDialog as LegacyConfigDialog


class ExportConfigDialog(LegacyConfigDialog):
    """Apresenta nomenclatura e impressão em um fluxo vertical único."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Configurações de exportação")
        self.resize(640, 760)

        naming_page = self.tabs.widget(0)
        print_page = self.tabs.widget(1)
        theme_page = self.tabs.widget(2)

        for page in (naming_page, print_page):
            page_layout = page.layout()
            if page_layout and page_layout.count():
                last_item = page_layout.itemAt(page_layout.count() - 1)
                if last_item and last_item.spacerItem():
                    page_layout.takeAt(page_layout.count() - 1)

        while self.tabs.count():
            self.tabs.removeTab(0)
        theme_page.deleteLater()

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(12)

        naming_group = QGroupBox("Nomenclatura")
        naming_layout = QVBoxLayout(naming_group)
        naming_layout.setContentsMargins(8, 10, 8, 8)
        naming_layout.addWidget(naming_page)
        naming_page.show()
        content_layout.addWidget(naming_group)

        print_group = QGroupBox("Impressão")
        print_layout = QVBoxLayout(print_group)
        print_layout.setContentsMargins(8, 10, 8, 8)
        print_layout.addWidget(print_page)
        print_page.show()
        content_layout.addWidget(print_group)
        content_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)

        main_layout = self.layout()
        main_layout.removeWidget(self.tabs)
        self.tabs.hide()
        self.tabs.deleteLater()
        main_layout.insertWidget(0, scroll, 1)

        self._export_scroll = scroll
        self._export_content = content


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
