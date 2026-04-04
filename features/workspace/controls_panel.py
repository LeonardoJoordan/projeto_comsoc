from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton

class ControlsPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addStretch() # Adiciona mola no topo para empurrar os botões para o centro

        self.btn_add_model = QPushButton("➕ Novo")
        self.btn_duplicate_model = QPushButton("📑 Duplicar")
        self.btn_remove_model = QPushButton("🗑️ Remover")
        self.btn_rename_model = QPushButton("✏️ Renomear")
        self.btn_config_model = QPushButton("⚙️ Configurar")
        
        self.btn_import_models = QPushButton("📥 Importar")
        self.btn_export_models = QPushButton("📤 Exportar")

        layout.addWidget(self.btn_add_model)
        layout.addWidget(self.btn_duplicate_model)
        layout.addWidget(self.btn_remove_model)
        layout.addWidget(self.btn_rename_model) 
        layout.addWidget(self.btn_config_model)
        
        layout.addSpacing(15) # Separação visual para Import/Export
        layout.addWidget(self.btn_import_models)
        layout.addWidget(self.btn_export_models)
        
        layout.addStretch()