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
        self.btn_add_model.setToolTip(
            "<b>NOVO MODELO</b><br><br>"
            "Cria um documento em branco a partir do zero no Editor Visual.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Para economizar tempo, considere duplicar um modelo existente que já tenha o formato desejado.</small>"
        )
        self.btn_duplicate_model = QPushButton("📑 Duplicar")
        self.btn_duplicate_model.setMinimumHeight(40)
        self.btn_duplicate_model.setToolTip(
            "<b>DUPLICAR MODELO</b><br><br>"
            "Cria uma cópia exata do modelo selecionado, preservando a arte e todas as configurações.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Ideal para criar variações de um mesmo documento (ex: versão Comandante e versão Subcomandante).</small>"
        )
        self.btn_remove_model = QPushButton("🗑️ Remover")
        self.btn_remove_model.setMinimumHeight(40)
        self.btn_remove_model.setToolTip(
            "<b>REMOVER MODELO</b><br><br>"
            "Exclui permanentemente o modelo selecionado e os seus arquivos do sistema.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Utilize a função 'Exportar' para criar um backup seguro antes de apagar documentos importantes.</small>"
        )
        self.btn_rename_model = QPushButton("✏️ Renomear")
        self.btn_rename_model.setMinimumHeight(40)
        self.btn_rename_model.setToolTip(
            "<b>RENOMEAR MODELO</b><br><br>"
            "Altera o nome de identificação do modelo na sua lista principal."
        )
        self.btn_config_model = QPushButton("📝 Editar")
        self.btn_config_model.setMinimumHeight(40)
        self.btn_config_model.setToolTip(
            "<b>EDITAR MODELO</b><br><br>"
            "Abre o Editor Visual para modificar o design gráfico, adicionar elementos e configurar o documento.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: É dentro do editor que você cria as variáveis entre chaves (ex: {Nome}) que se transformarão nas colunas desta tabela.</small>"
        )
        
        self.btn_import_models = QPushButton("📥 Importar")
        self.btn_import_models.setMinimumHeight(40)
        self.btn_import_models.setToolTip(
            "<b>IMPORTAR MODELOS</b><br><br>"
            "Carrega pacotes de modelos (.zip) recebidos de outros computadores ou seções para dentro do seu sistema."
        )
        self.btn_export_models = QPushButton("📤 Exportar")
        self.btn_export_models.setMinimumHeight(40)
        self.btn_export_models.setToolTip(
            "<b>EXPORTAR MODELOS</b><br><br>"
            "Gera um pacote compactado (.zip) contendo a arte, fontes e configurações dos seus modelos para backup ou compartilhamento com terceiros."
        )

        layout.addWidget(self.btn_add_model)
        layout.addWidget(self.btn_duplicate_model)
        layout.addWidget(self.btn_remove_model)
        layout.addWidget(self.btn_rename_model) 
        layout.addWidget(self.btn_config_model)
        
        layout.addSpacing(35) # Separação visual para Import/Export
        layout.addWidget(self.btn_import_models)
        layout.addWidget(self.btn_export_models)
        
        layout.addStretch()