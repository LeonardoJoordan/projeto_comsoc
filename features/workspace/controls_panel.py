from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton

class ControlsPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addStretch() # Adiciona mola no topo para empurrar os botões para o centro

        self.btn_add_model = QPushButton("➕ Novo")
        self.btn_add_model.setMinimumHeight(40)
        self.btn_duplicate_model = QPushButton("📑 Duplicar")
        self.btn_duplicate_model.setMinimumHeight(40)
        self.btn_remove_model = QPushButton("🗑️ Remover")
        self.btn_remove_model.setMinimumHeight(40)
        self.btn_rename_model = QPushButton("✏️ Renomear")
        self.btn_rename_model.setMinimumHeight(40)
        self.btn_config_model = QPushButton("⚙️ Configurar")
        self.btn_config_model.setMinimumHeight(40)
        
        self.btn_import_models = QPushButton("📥 Importar")
        self.btn_import_models.setMinimumHeight(40)
        self.btn_export_models = QPushButton("📤 Exportar")
        self.btn_export_models.setMinimumHeight(40)

        layout.addWidget(self.btn_add_model)
        layout.addWidget(self.btn_duplicate_model)
        layout.addWidget(self.btn_remove_model)
        layout.addWidget(self.btn_rename_model) 
        layout.addWidget(self.btn_config_model)
        
        layout.addSpacing(35) # Separação visual para Import/Export
        layout.addWidget(self.btn_import_models)
        layout.addWidget(self.btn_export_models)
        
        layout.addStretch()