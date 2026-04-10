from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
                               QTableWidget, QTableWidgetItem, QDialogButtonBox, 
                               QRadioButton, QWidget, QHeaderView, QLabel, QButtonGroup, QPushButton)
from PySide6.QtCore import Qt
from core.template_manager import slugify_model_name

class ImportModelsDialog(QDialog):
    def __init__(self, parent, zip_models, existing_slugs):
        super().__init__(parent)
        self.setWindowTitle("Importação de Lote")
        self.resize(750, 500)
        
        self.zip_models = zip_models
        self.existing_slugs = existing_slugs
        self.decisions = {}
        
        layout = QVBoxLayout(self)
        
        # --- Topo: Controles em Lote ---
        top_layout = QHBoxLayout()
        self.chk_master = QCheckBox("Selecionar / Desmarcar Todos")
        self.chk_master.setChecked(True)
        self.chk_master.stateChanged.connect(self._on_master_toggled)
        top_layout.addWidget(self.chk_master)
        
        top_layout.addStretch()
        
        lbl_global = QLabel("<b>Ação Global para Conflitos:</b>")
        btn_all_replace = QPushButton("Substituir Todos")
        btn_all_rename = QPushButton("Novo Nome Todos")
        
        btn_all_replace.clicked.connect(lambda: self._apply_global_conflict("replace"))
        btn_all_rename.clicked.connect(lambda: self._apply_global_conflict("rename"))
        
        top_layout.addWidget(lbl_global)
        top_layout.addWidget(btn_all_replace)
        top_layout.addWidget(btn_all_rename)
        
        layout.addLayout(top_layout)
        
        # --- Tabela Central ---
        self.table = QTableWidget(len(zip_models), 4)
        self.table.setHorizontalHeaderLabels(["Importar", "Modelo no ZIP", "Status", "Resolução de Conflito"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.button_groups = {} 
        self.checkboxes = {} 
        self._updating = False
        
        self._populate_table()
        
        # --- Rodapé: Botões ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_decisions(self):
        results = {}
        for row, model_name in enumerate(self.zip_models):
            is_checked = self.checkboxes[row].isChecked()
            action = "new"
            if row in self.button_groups:
                checked_id = self.button_groups[row].checkedId()
                if checked_id == 1: action = "replace"
                elif checked_id == 2: action = "rename"
            
            results[model_name] = {
                "import": is_checked,
                "action": action
            }
        return results

    def _populate_table(self):
        for row, model_name in enumerate(self.zip_models):
            # 1. Coluna Importar (Checkbox)
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk = QCheckBox()
            chk.setChecked(True)
            chk.stateChanged.connect(self._on_item_changed)
            chk_layout.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_widget)
            self.checkboxes[row] = chk
            
            # 2. Coluna Nome do Modelo
            self.table.setItem(row, 1, QTableWidgetItem(model_name))
            
            # 3. Colunas Status e Resolução
            slug = slugify_model_name(model_name)
            is_conflict = slug in self.existing_slugs
            
            if is_conflict:
                item_status = QTableWidgetItem("⚠️ Já Existe")
                item_status.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 2, item_status)
                
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 0, 5, 0) 
                action_layout.setSpacing(15) 
                
                rb_replace = QRadioButton("Substituir")
                rb_rename = QRadioButton("Novo Nome")
                rb_rename.setChecked(True) 
                
                bg = QButtonGroup(action_widget)
                bg.addButton(rb_replace, 1)
                bg.addButton(rb_rename, 2) # ID reajustado
                self.button_groups[row] = bg
                
                action_layout.addWidget(rb_replace)
                action_layout.addWidget(rb_rename)
                self.table.setCellWidget(row, 3, action_widget)

                # BÔNUS UX: Desativa a coluna de conflito se desmarcar a importação
                chk.stateChanged.connect(lambda state, aw=action_widget: aw.setEnabled(state == Qt.CheckState.Checked.value))
            else:
                item_status = QTableWidgetItem("✨ Novo")
                item_status.setForeground(Qt.GlobalColor.darkGreen)
                self.table.setItem(row, 2, item_status)
                
                item_empty = QTableWidgetItem("-")
                item_empty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, item_empty)
        
        # Trava as colunas de controle no tamanho exato do seu conteúdo
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    def _apply_global_conflict(self, action):
        idx = {"replace": 1, "rename": 2}[action]
        for bg in self.button_groups.values():
            bg.button(idx).setChecked(True)

    def _on_master_toggled(self, state):
        if self._updating: return
        self._updating = True
        is_checked = self.chk_master.isChecked()
        for chk in self.checkboxes.values():
            chk.setChecked(is_checked)
        self._updating = False

    def _on_item_changed(self):
        if self._updating: return
        self._updating = True
        all_checked = all(chk.isChecked() for chk in self.checkboxes.values())
        self.chk_master.setChecked(all_checked)
        self._updating = False 