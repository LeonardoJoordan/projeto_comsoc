from PySide6.QtWidgets import (QDialog, QVBoxLayout, QCheckBox, QListWidget,
                               QListWidgetItem, QDialogButtonBox)
from PySide6.QtCore import Qt

class ExportModelsDialog(QDialog):
    def __init__(self, parent=None, models=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar Modelos")
        self.resize(350, 400)
        
        layout = QVBoxLayout(self)
        
        self.chk_master = QCheckBox("Selecionar / Desmarcar Todos")
        self.chk_master.setChecked(False)
        self.chk_master.stateChanged.connect(self._on_master_toggled)
        layout.addWidget(self.chk_master)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        for model_name in (models or []):
            item = QListWidgetItem(model_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
            
        self.list_widget.itemChanged.connect(self._on_item_changed)
            
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self._updating = False

    def get_selected_models(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

    def _on_master_toggled(self, state):
        if self._updating: return
        self._updating = True
        check_state = Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(check_state)
        self._updating = False

    def _on_item_changed(self, item):
        if self._updating: return
        self._updating = True
        all_checked = True
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).checkState() == Qt.CheckState.Unchecked:
                all_checked = False
                break
        
        self.chk_master.setCheckState(Qt.CheckState.Checked if all_checked else Qt.CheckState.Unchecked)
        self._updating = False   