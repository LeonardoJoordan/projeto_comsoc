import zipfile
import os
import shutil
import json
import tempfile
import copy
import time
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                                QSplitter, QPushButton, QApplication, QMessageBox,
                                  QLineEdit, QLabel, QFileDialog, QProgressBar,
                                  QInputDialog, QComboBox, QTableWidgetItem)
from PySide6.QtCore import Qt, QSignalBlocker, QTimer, QThread
from PySide6.QtGui import QPainter, QImage, QIcon, QPageLayout, QPalette, QColor

from features.preview.preview_panel import PreviewPanel
from features.preview.sheet_preview_worker import SheetPreviewWorker
from features.workspace.controls_panel import ControlsPanel
from shared.log_panel import LogPanel
from features.spreadsheet.table_panel import TablePanel
from features.generator.renderer import NativeRenderer
from features.editor.editor_window import EditorWindow
from features.generator.manager import RenderManager
from features.generator.production_plan import build_imposition_plan
from features.workspace.settings_dialogs import ExportConfigDialog, ThemeDialog
from features.generator.preset_warnings import warning_display_name, warning_tooltip
from features.workspace.import_models_dialog import ImportModelsDialog
from features.workspace.export_models_dialog import ExportModelsDialog
from core.template_manager import slugify_model_name
from core.paths import get_models_dir
from core.settings import get_app_settings
from core.font_utils import format_font_list, missing_template_fonts
from core.render_cache import ensure_background_proxy
from core.resources import object_icon_path
from core.output_folders import create_forge_output_dir
from core.i18n import tr
from features.spreadsheet.headers import QUANTITY_HEADER, SIGNATURE_HEADER




class MainWindow(QMainWindow):
    SYSTEM_IMPOSITION_PRESET = "Definição do Modelo"

    def _apply_tooltip(self, widget, text):
            """Aplica tooltip e garante que labels estáticos capturem o evento no motor customizado."""
            if isinstance(widget, QLabel):
                widget.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
            widget.setToolTip(text)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("FORNAX Forge — Geração de material personalizado em lote"))
        self.setMinimumSize(1024, 680)
        self.resize(1280, 720)

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(self.splitter)

        self.current_filename_suffix = "" 
        self.manager = None 

        # --- Painel ESQUERDO ---
        left = QWidget()
        self.left_panel = left
        left.setObjectName("workspaceLeft")
        left.setMinimumWidth(500) # Ajustado para a nova largura mínima
        self.splitter.addWidget(left)

        left_stack = QVBoxLayout(left)
        left_stack.setContentsMargins(0, 0, 0, 0)
        left_stack.setSpacing(10)

        self.preview_panel = PreviewPanel()
        self._preview_mode = "item"
        self._preview_sheet_index = 0
        self._sheet_preview_revision = 0
        self._sheet_preview_worker = None
        self._sheet_preview_workers = set()
        self._sheet_preview_dir = None
        self._sheet_preview_paths = {}
        self._stale_sheet_preview_dirs = set()
        self._preview_refresh_timer = QTimer(self)
        self._preview_refresh_timer.setSingleShot(True)
        self._preview_refresh_timer.setInterval(100)
        self._preview_refresh_timer.timeout.connect(self._refresh_preview_after_data_change)
        self.preview_panel.modeChanged.connect(self._on_preview_mode_changed)
        self.preview_panel.indexRequested.connect(self._on_preview_index_requested)
        self.controls_panel = ControlsPanel()
        self.controls_panel.setFixedWidth(110) # Trava a largura da sidebar
        self.log_panel = LogPanel()

        # Agrupa Preview e Controls lado a lado
        preview_container = QWidget()
        self.preview_container = preview_container
        preview_layout = QHBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(10)
        preview_layout.addWidget(self.controls_panel, 0)
        preview_layout.addWidget(self.preview_panel, 1)

        left_stack.addWidget(preview_container, 5)
        left_stack.addWidget(self.log_panel, 3)

        # --- BARRA DE PROGRESSO ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: transparent; 
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 4px;
            }
        """)
        left_stack.addWidget(self.progress_bar, 0)

        # --- CONTAINER DE CONTROLES DE SAÍDA (Rodapé em Duas Colunas) ---
        footer_container = QWidget()
        self.footer_container = footer_container
        footer_container.setObjectName("outputPanel")
        ly_footer = QHBoxLayout(footer_container)
        ly_footer.setContentsMargins(0, 0, 0, 0)
        ly_footer.setSpacing(15)

        # --- Coluna Esquerda: Gatilho e Caminho ---
        col_left_footer = QVBoxLayout()
        
        # Linha de Saída
        row_out_path = QHBoxLayout()
        row_out_path.addWidget(QLabel("Saída:"))
        self.txt_output_path = QLineEdit()
        self.txt_output_path.setPlaceholderText("Selecione a pasta onde os lotes serão gerados")
        row_out_path.addWidget(self.txt_output_path)
        
        self.btn_sel_out = QPushButton("...")
        self.btn_sel_out.setFixedWidth(40)
        self._apply_tooltip(self.btn_sel_out, 
            "<b>PASTA DE DESTINO</b><br><br>"
            "Define em qual local do computador os arquivos gerados serão salvos.<br><br>"
            "<small >Dica: O sistema criará automaticamente uma subpasta com a data e hora atual dentro do local escolhido para manter seus lotes organizados.</small>")
        self.btn_sel_out.clicked.connect(self._select_output_folder)
        row_out_path.addWidget(self.btn_sel_out)
        col_left_footer.addLayout(row_out_path)

        # Botão Gerar
        self.btn_generate_cards = QPushButton(tr("Gerar material"))
        self.btn_generate_cards.setMinimumHeight(40)
        self.btn_generate_cards.setStyleSheet("font-weight: bold; font-size: 13px;")
        self._apply_tooltip(self.btn_generate_cards, 
            "<b>GERAR MATERIAL</b><br><br>"
            "Inicia o processamento da tabela e a construção dos arquivos finais na pasta de saída.<br><br>"
            "<small >Dica: Faça uma checagem rápida nas colunas de Quantidade e Assinatura antes de iniciar a geração de lotes muito grandes para evitar desperdícios.</small>")
        self.btn_generate_cards.clicked.connect(self._generate_cards_async)
        col_left_footer.addWidget(self.btn_generate_cards)
        
        ly_footer.addLayout(col_left_footer, 1) # Proporção 1

        # --- Coluna Direita: Parâmetros de Saída e Presets ---
        widget_right_footer = QWidget()
        widget_right_footer.setFixedWidth(280) # O tamanho fixo vai no QWidget
        col_right_footer = QVBoxLayout(widget_right_footer)
        col_right_footer.setContentsMargins(0, 0, 0, 0)

        # Linha de Formato e Configs
        row_format_cfg = QHBoxLayout()
        self.cbo_export_format = QComboBox()
        self.cbo_export_format.addItem("PNG", "png")
        self.cbo_export_format.addItem(tr("PDF por item"), "pdf_item")
        self.cbo_export_format.addItem(tr("PDF agrupado"), "pdf_grouped")
        self.cbo_export_format.setFixedWidth(150)
        self._export_mode_tooltips = {
            "png": "<b>PNG</b><br>Gera uma imagem PNG para cada item da tabela.",
            "pdf_item": "<b>PDF por item</b><br>Gera um arquivo PDF separado para cada item da tabela.",
            "pdf_grouped": "<b>PDF agrupado</b><br>Reúne todos os itens gerados em um único arquivo PDF com várias páginas.",
        }
        for index in range(self.cbo_export_format.count()):
            mode = self.cbo_export_format.itemData(index)
            self.cbo_export_format.setItemData(
                index, self._export_mode_tooltips[mode], Qt.ItemDataRole.ToolTipRole
            )
        self._apply_tooltip(self.cbo_export_format, 
            "<b>FORMATO DE SAÍDA</b><br><br>"
            "Escolha o tipo de arquivo final:<br>"
            "• <b>PNG:</b> uma imagem para cada item.<br>"
            "• <b>PDF por item:</b> um PDF separado para cada item.<br>"
            "• <b>PDF agrupado:</b> todos os itens em um único PDF.")
        
        self.btn_config_name = QPushButton("Exportação")
        self.btn_config_name.clicked.connect(self._open_config_dialog)
        self._apply_tooltip(self.btn_config_name, 
            "<b>CONFIGURAÇÕES DE EXPORTAÇÃO</b><br><br>"
            "Acesso aos ajustes de geração dos arquivos:<br>"
            "• <b>Nomenclatura:</b> Define o padrão de nome dos arquivos gerados usando as variáveis da tabela.<br>"
            "• <b>Impressão:</b> Configura o agrupamento de vários cartões em uma folha e ativa marcas de corte.<br><br>"
            "<small >Dica: Na seção de Impressão, o sistema calcula automaticamente quantos cartões cabem na folha assim que você digita as dimensões.</small>")
        
        row_format_cfg.addWidget(self.cbo_export_format)
        row_format_cfg.addWidget(self.btn_config_name)
        col_right_footer.addLayout(row_format_cfg)

        # Linha de Predefinição (O Atalho)
        row_presets_main = QVBoxLayout()
        self.cbo_presets_main = QComboBox()
        self.cbo_presets_main.currentIndexChanged.connect(self._on_main_preset_changed)
        lbl_layout = QLabel("<b>Predefinição de Impressão:</b>")
        self._apply_tooltip(lbl_layout,
            "<b>PREDEFINIÇÃO DE IMPRESSÃO</b><br><br>"
            "Atalho para aplicar rapidamente um conjunto de configurações de impressão salvas:<br><br>"
            "<small >Dica: Para criar ou editar predefinições, acesse <b>Configurações &gt; Impressão</b>.</small>")
        row_presets_main.addWidget(lbl_layout)
        row_presets_main.addWidget(self.cbo_presets_main, 1)
        self._presets_main_base_tooltip = (
            "<b>PREDEFINIÇÃO DE IMPRESSÃO</b><br><br>"
            "Atalho para aplicar rapidamente um conjunto de configurações de impressão salvas:<br><br>"
            "<small >Dica: Para criar ou editar predefinições, acesse <b>Configurações &gt; Impressão</b>.</small>"
        )
        self._apply_tooltip(self.cbo_presets_main, self._presets_main_base_tooltip)
        col_right_footer.addLayout(row_presets_main)

        ly_footer.addWidget(widget_right_footer, 0) # Adiciona o Widget em vez do Layout isolado

        left_stack.addWidget(footer_container, 0)

        # --- Painel DIREITO ---
        self.table_panel = TablePanel()
        self.splitter.addWidget(self.table_panel)

        self.splitter.setSizes([640, 640])
        self.splitter.setCollapsible(0, False)

        self.cached_model_data = None
        self.preview_renderer = None # Persistência do Renderer para o Live Preview
        
        # Garante que um usuário novato não veja uma tela em branco
        self._ensure_starter_pack()

        # O reload já se encarrega de setar o active_model_name e chamar o _on_model_changed
        self._reload_models_from_disk()

        self.preview_panel.cbo_models.currentTextChanged.connect(self._on_model_changed)

        # Sincronização de preferências e visibilidade
        self.cbo_export_format.currentIndexChanged.connect(self._on_export_mode_changed)

        self.table_panel.table.itemSelectionChanged.connect(self._on_table_selection)
        self.table_panel.table.itemChanged.connect(self._on_preview_data_changed)
        self.table_panel.table.model().rowsInserted.connect(self._on_preview_rows_changed)
        self.table_panel.table.model().rowsRemoved.connect(self._on_preview_rows_changed)

        # --- Conexões dos Botões de Controle ---
        self.controls_panel.btn_add_model.clicked.connect(self._on_add_model)
        self.controls_panel.btn_duplicate_model.clicked.connect(self._on_duplicate_model)
        self.controls_panel.btn_remove_model.clicked.connect(self._on_remove_model)
        self.controls_panel.btn_rename_model.clicked.connect(self._on_rename_model) 
        self.controls_panel.btn_config_model.clicked.connect(self._open_model_dialog)
        self.controls_panel.btn_import_models.clicked.connect(self._on_import_models)
        self.controls_panel.btn_export_models.clicked.connect(self._on_export_models)

        self.settings = get_app_settings()
        
        # Restaura a geometria e o estado da janela (posição e tamanho)
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Restaura o estado do divisor (largura das colunas interna)
        splitter_state = self.settings.value("splitterState")
        if splitter_state:
            self.splitter.restoreState(splitter_state)

        last_output = self.settings.value("last_output_dir", "")
        if last_output:
            self.txt_output_path.setText(str(last_output))

        # Inicializa o tema visual salvo (padrão é escuro)
        self._initialize_theme()
        from .frontend import install_frontend
        install_frontend(self)

    def _ensure_starter_pack(self):
        models_dir = get_models_dir()
        
        # Se a pasta já contém algo, o usuário não é novo. Interrompe a criação.
        if any(models_dir.iterdir()):
            return
            
        self.log_panel.append("🌱 Primeiro uso detectado. Preparando Modelo de Exemplo...")
        slug = "modelo_exemplo"
        example_dir = models_dir / slug
        example_dir.mkdir(parents=True, exist_ok=True)
        
        example_data = {
            "name": "Modelo Exemplo",
            "canvas_size": {"w": 1000, "h": 1000},
            "target_w_mm": 100.0,
            "target_h_mm": 100.0,
            "placeholders": ["Nome", "Cargo"],
            "boxes": [
                {
                    "id": "Nome",
                    "html": "<b>{Nome}</b>",
                    "x": 350, "y": 400, "w": 300, "h": 60,
                    "font_family": "Arial", "font_size": 36,
                    "align": "center", "visible": True
                },
                {
                    "id": "Cargo",
                    "html": "<i>{Cargo}</i>",
                    "x": 350, "y": 480, "w": 300, "h": 60,
                    "font_family": "Arial", "font_size": 24,
                    "align": "center", "visible": True
                }
            ]
        }
        with open(example_dir / "template_v3.json", "w", encoding="utf-8") as f:
            json.dump(example_data, f, indent=4, ensure_ascii=False)

    def _initialize_theme(self):
        from core.themes import theme_manager
        theme_manager().initialize(self.settings)

    def closeEvent(self, event):
        """Salva a posição, tamanho e estado do splitter ao fechar o programa."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitterState", self.splitter.saveState())
        self._stop_sheet_preview_worker(wait=True)
        for worker in tuple(self._sheet_preview_workers):
            worker.stop()
            worker.requestInterruption()
            worker.wait()
        for directory in ({self._sheet_preview_dir} | self._stale_sheet_preview_dirs):
            if directory:
                shutil.rmtree(directory, ignore_errors=True)
        super().closeEvent(event)

    def _reload_models_from_disk(self, select_name: str | None = None):
        self.preview_panel.cbo_models.blockSignals(True)
        self.preview_panel.cbo_models.clear()

        models_dir = get_models_dir()
        models_dir.mkdir(parents=True, exist_ok=True)

        found = []
        for folder in sorted(models_dir.iterdir()):
            if not folder.is_dir(): continue
            json_path = folder / "template_v3.json"
            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text(encoding="utf-8"))
                    name = data.get("name", folder.name)
                    found.append(name)
                except Exception:
                    continue

        for name in found:
            self.preview_panel.cbo_models.addItem(name)

        self.preview_panel.cbo_models.blockSignals(False)

        target_index = 0 
        if select_name:
            idx = self.preview_panel.cbo_models.findText(select_name)
            if idx >= 0:
                target_index = idx

        if self.preview_panel.cbo_models.count() > 0:
            self.preview_panel.cbo_models.setCurrentIndex(target_index)
            current_text = self.preview_panel.cbo_models.itemText(target_index)
            self._on_model_changed(current_text)
        else:
            self._on_model_changed("")

    def _on_add_model(self):
        self.editor_window = EditorWindow(self)
        self.editor_window.modelSaved.connect(self._on_editor_saved)
        self.editor_window.show()

    def _on_duplicate_model(self):
        original_name = self.preview_panel.cbo_models.currentText()
        
        if not original_name:
            QMessageBox.warning(self, "Atenção", "Selecione um modelo para duplicar.")
            return

        original_slug = slugify_model_name(original_name)
        original_dir = get_models_dir() / original_slug

        if not original_dir.exists():
            self.log_panel.append("ERRO: Pasta do modelo original não encontrada.")
            return

        counter = 1
        while True:
            suffix = " (Cópia)" if counter == 1 else f" (Cópia {counter})"
            new_name = f"{original_name}{suffix}"
            new_slug = slugify_model_name(new_name)
            new_dir = get_models_dir() / new_slug
            
            if not new_dir.exists():
                break
            counter += 1

        try:
            shutil.copytree(original_dir, new_dir)
            
            json_path = new_dir / "template_v3.json"
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["name"] = new_name
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

            self.log_panel.append(f"Modelo duplicado: '{new_name}'")
            self._reload_models_from_disk(select_name=new_name)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao duplicar modelo:\n{e}")
            if new_dir.exists():
                shutil.rmtree(new_dir, ignore_errors=True)

    def _on_rename_model(self):
        old_name = self.preview_panel.cbo_models.currentText()
        
        if not old_name:
            QMessageBox.warning(self, "Atenção", "Selecione um modelo para renomear.")
            return

        new_name, ok = QInputDialog.getText(self, "Renomear Modelo", "Novo nome:", text=old_name)
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        if new_name == old_name:
            return

        old_slug = slugify_model_name(old_name)
        new_slug = slugify_model_name(new_name)
        
        old_dir = get_models_dir() / old_slug
        new_dir = get_models_dir() / new_slug

        # Se os slugs forem diferentes e o destino já existe, há um conflito real.
        if new_slug != old_slug and new_dir.exists():
            QMessageBox.warning(self, "Erro", f"Já existe um modelo com o slug '{new_slug}'.")
            return

        try:
            # 1. Renomeia a pasta apenas se o slug mudou
            if new_slug != old_slug:
                old_dir.rename(new_dir)
            
            # 2. Define o caminho correto do JSON para atualizar o nome visual
            actual_dir = new_dir if new_slug != old_slug else old_dir
            json_path = actual_dir / "template_v3.json"

            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                data["name"] = new_name # Salva com a capitalização nova
                
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            
            self.log_panel.append(f"Modelo renomeado: '{old_name}' -> '{new_name}'")
            self._reload_models_from_disk(select_name=new_name)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao renomear: {e}")

    def _on_remove_model(self):
        model_name = (self.preview_panel.cbo_models.currentText() or "").strip()
        if not model_name: return

        slug = slugify_model_name(model_name)
        model_dir = get_models_dir() / slug

        if not model_dir.exists(): return

        resp = QMessageBox.question(self, "Confirmar exclusão", f"Excluir '{model_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes: return

        try:
            shutil.rmtree(model_dir)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao excluir: {e}")
            return

        self.log_panel.append(f"Modelo excluído: {model_name}")
        self._reload_models_from_disk()

    def _on_import_models(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar Lote", "", "Pacotes de Modelo ZIP (*.zip)")
        if not file_path: return

        try:
            models_dir = get_models_dir()
            
            # Etapa 1: Espionagem do ZIP (Leitura ultrarrápida de cabeçalhos sem extrair)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Descobre as pastas de modelo dentro do zip
                top_level_folders = set(info.filename.split('/')[0] for info in zip_ref.infolist() if '/' in info.filename)
                
                models_in_zip = {} # Mapeamento (Nome Legível do JSON -> Nome da Pasta no Zip)
                missing_fonts_by_model = {}
                
                for zip_slug in sorted(top_level_folders):
                    json_path = f"{zip_slug}/template_v3.json"
                    try:
                        with zip_ref.open(json_path) as f:
                            data = json.loads(f.read().decode('utf-8'))
                            name = data.get("name", zip_slug)
                            models_in_zip[name] = zip_slug
                            missing_fonts_by_model[name] = missing_template_fonts(data)
                    except KeyError: 
                        # Se o modelo não tiver um JSON válido, usamos o nome bruto da pasta
                        models_in_zip[zip_slug] = zip_slug
                        missing_fonts_by_model[zip_slug] = []
                        
                if not models_in_zip:
                    QMessageBox.warning(self, "Arquivo Inválido", "Este arquivo ZIP não contém modelos compatíveis com o FORNAX Forge.")
                    return
                
                # Etapa 2: Checagem de Conflitos e Abertura da Janela de Decisão
                existing_slugs = set(d.name for d in models_dir.iterdir() if d.is_dir())
                
                dlg = ImportModelsDialog(self, list(models_in_zip.keys()), existing_slugs, missing_fonts_by_model)
                if not dlg.exec():
                    return # O usuário clicou em Cancelar
                    
                decisions = dlg.get_decisions()
                
                # Etapa 3: Extração Cirúrgica via Cache Temporário
                imported_count = 0
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    for model_name, decision in decisions.items():
                        if not decision["import"] or decision["action"] == "ignore":
                            continue # Pula modelos desmarcados ou ignorados
                            
                        zip_slug = models_in_zip[model_name]
                        source_dir = Path(temp_dir) / zip_slug
                        if not source_dir.exists():
                            continue
                            
                        target_slug = slugify_model_name(model_name)
                        target_name = model_name
                        
                        # Tratamento da Rota Escolhida
                        if decision["action"] == "replace":
                            target_dir = models_dir / target_slug
                            if target_dir.exists():
                                shutil.rmtree(target_dir) # Esmaga o modelo velho
                                
                        elif decision["action"] == "rename":
                            # Validação dupla: Se por acaso o usuário marcou "Novo Nome" mas o arquivo 
                            # não era conflito, ele mantém o original. Se for conflito, roda a lógica.
                            if (models_dir / target_slug).exists():
                                counter = 1
                                base_name = f"{model_name} (Nova Importação)"
                                target_name = base_name
                                target_slug = slugify_model_name(target_name)
                                
                                # Garante um nome livre na pasta de modelos (Ex: Nova Importação 2)
                                while (models_dir / target_slug).exists():
                                    counter += 1
                                    target_name = f"{base_name} {counter}"
                                    target_slug = slugify_model_name(target_name)
                            
                            # Entra no modelo temporário e atualiza o JSON dele silenciosamente
                            json_file = source_dir / "template_v3.json"
                            if json_file.exists():
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                data['name'] = target_name
                                with open(json_file, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, indent=4, ensure_ascii=False)
                        
                        # Move a pasta tratada da área de segurança para a pasta oficial
                        target_dir = models_dir / target_slug
                        shutil.move(str(source_dir), str(target_dir))
                        imported_count += 1
            
            # Etapa 4: Finalização e Limpeza Automática do TempDir
            if imported_count > 0:
                self.log_panel.append(f"📥 {imported_count} modelo(s) processado(s) e importado(s) de: {Path(file_path).name}")
                self._reload_models_from_disk()
                QMessageBox.information(self, "Importação Concluída", f"{imported_count} modelo(s) adicionado(s) à sua biblioteca!")
            else:
                self.log_panel.append("⚠️ Processo finalizado: Nenhum modelo novo foi adicionado.")
                
        except Exception as e:
            QMessageBox.critical(self, "Falha Crítica", f"O sistema interceptou um erro na montagem do arquivo ZIP:\n{str(e)}")

    def _on_export_models(self):
        all_models = [self.preview_panel.cbo_models.itemText(i) for i in range(self.preview_panel.cbo_models.count())]
        
        if not all_models:
            QMessageBox.warning(self, "Atenção", "Nenhum modelo disponível para exportar.")
            return
            
        dlg = ExportModelsDialog(self, all_models)
        if not dlg.exec():
            return
            
        selected_models = dlg.get_selected_models()
        if not selected_models:
            QMessageBox.warning(self, "Atenção", "Nenhum modelo foi selecionado para exportação.")
            return
            
        save_path, _ = QFileDialog.getSaveFileName(self, "Exportar Modelos", "Modelos_FORNAX_Forge.zip", "Arquivos ZIP (*.zip)")
        if not save_path: return
        
        try:
            models_dir = get_models_dir()
            
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for model_name in selected_models:
                    slug = slugify_model_name(model_name)
                    model_dir = models_dir / slug
                    if not model_dir.exists(): continue
                    
                    for root, dirs, files in os.walk(model_dir):
                        dirs[:] = [d for d in dirs if d != ".render_cache"]
                        for file in files:
                            file_path = Path(root) / file
                            arcname = Path(slug) / file_path.relative_to(model_dir)
                            zipf.write(file_path, arcname)
            
            self.log_panel.append(f"📤 {len(selected_models)} modelo(s) exportado(s) para: {Path(save_path).name}")
            QMessageBox.information(self, "Sucesso", f"{len(selected_models)} modelo(s) exportado(s) com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Falha ao gerar o arquivo ZIP:\n{e}")

    def _on_model_changed(self, name: str):
        self._preview_generation = getattr(self, "_preview_generation", 0) + 1
        generation = self._preview_generation
        self.preview_renderer = None
        self.cached_model_data = None
        self._preview_mode = "item"
        self._preview_sheet_index = 0
        self._invalidate_sheet_previews()
        self.preview_panel.set_preview_text(f"Prévia do modelo selecionado:\n{name}")
        self.log_panel.append(f"Modelo ativo: {name}")
        self.active_model_name = name
        self.current_filename_suffix = ""

        if not name:
            self._update_table_columns([])
            return

        slug = slugify_model_name(name)
        json_path = get_models_dir() / slug / "template_v3.json"

        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    self.current_filename_suffix = data.get("output_suffix", "")

                    # Recupera o modo novo e também entende as preferências legadas.
                    last_fmt = data.get("last_export_format", "PNG")
                    last_single = data.get("last_single_pdf", False)
                    last_mode = data.get("last_export_mode")
                    if last_mode not in {"png", "pdf_item", "pdf_grouped"}:
                        last_mode = (
                            "png" if last_fmt == "PNG" else
                            ("pdf_grouped" if last_single else "pdf_item")
                        )

                    self.cbo_export_format.blockSignals(True)
                    idx = self.cbo_export_format.findData(last_mode)
                    if idx >= 0:
                        self.cbo_export_format.setCurrentIndex(idx)
                    self.cbo_export_format.blockSignals(False)
                    self._refresh_export_mode_tooltip()

                    model_dir = json_path.parent
                    if data.get("background_path") and not Path(data["background_path"]).is_absolute():
                        data["background_path"] = str(model_dir / data["background_path"])
                    for sig in data.get("signatures", []):
                        if not Path(sig["path"]).is_absolute():
                            sig["path"] = str(model_dir / sig["path"])
                    data["__model_dir"] = str(model_dir)
                    ensure_background_proxy(model_dir, data)

                    placeholders = data.get("placeholders", [])
                    signatures = data.get("signatures", [])
                    self._update_table_columns(placeholders, signatures)
                    
                    self.cached_model_data = data
                    self._refresh_imposition_presets()
                    self._refresh_preview_navigation()

                    missing_fonts = missing_template_fonts(data)
                    if missing_fonts:
                        if len(missing_fonts) == 1:
                            msg = f"Este modelo usa uma fonte não encontrada no sistema: {format_font_list(missing_fonts)}"
                        else:
                            msg = f"Este modelo usa fontes não encontradas no sistema: {format_font_list(missing_fonts)}"
                        self.log_panel.append(f"<b>AVISO:</b> {msg}")
                    
                    try:
                        # Cria o "Chef" na memória (operação ultraleve, sem desenho)
                        self.preview_renderer = NativeRenderer(data)
                        
                        # Carregamento Instantâneo da Thumbnail de Performance ---
                        thumb_path = model_dir / ".render_cache" / "thumbnail_raw.png"
                        
                        if thumb_path.exists():
                            self.preview_panel.set_preview_image(str(thumb_path))
                        else:
                            # --- LEGO: Worker de Preview Assíncrono ---
                            self.preview_panel.set_preview_text(
                                tr("Gerando prévia, aguarde um instante…")
                            )
                            
                            from features.generator.workers import PreviewRenderWorker
                            
                            worker = PreviewRenderWorker(name, data, model_dir)
                            # Anexa à janela para o Garbage Collector não matar a Thread no meio do processo
                            worker.setParent(self) 
                            
                            worker.preview_ready.connect(lambda model, path, revision=generation: self._on_preview_ready(model, path) if revision == self._preview_generation else None)
                            worker.error_occurred.connect(lambda msg: self.log_panel.append(f"Erro preview background: {msg}"))
                            worker.finished.connect(worker.deleteLater) # Autolimpeza imediata ao terminar
                        
                            worker.start()
                            # --- FIM DO LEGO ---

                    except Exception as e:
                        self.log_panel.append(f"Erro ao gerar preview: {e}")
                        self.preview_panel.set_preview_text("Erro ao gerar preview do modelo")
                    self._start_sheet_preview_preload()
            except Exception as e:
                self.log_panel.append(f"Erro ao ler colunas do modelo: {e}")
        else:
            self.log_panel.append("Aviso: template_v3.json não encontrado.")

    # --- LEGO: Recebimento do Preview e Descarte Inteligente ---
    def _on_preview_ready(self, worker_model_name: str, thumb_path: str):
        """Atualiza a UI apenas se o usuário ainda estiver aguardando este modelo específico."""
        if self.active_model_name == worker_model_name:
            self.preview_panel.set_preview_image(thumb_path)
        # Nota: Se os nomes forem diferentes, significa que o usuário já trocou de modelo. 
        # A UI ignora, mas a imagem já ficou salva no disco em background para a próxima vez.
    # --- FIM DO LEGO ---

    def _update_table_columns(self, placeholders, signatures=None):
        self.table_panel.table.clearContents()
        self.table_panel.table.setRowCount(0)
        self.table_panel.table.setColumnCount(0)
        
        headers = [QUANTITY_HEADER] # Coluna 0
        has_sig = bool(signatures)
        
        if has_sig:
            headers.append(SIGNATURE_HEADER) # Coluna 1
        
        headers.extend(placeholders)
            
        self.table_panel.table.setColumnCount(len(headers))
        self.table_panel.table.setHorizontalHeaderLabels(headers)
        if has_sig:
            self.table_panel.table.horizontalHeaderItem(1).setIcon(QIcon(str(object_icon_path("signature"))))
        
        # Ajuste de larguras iniciais
        self.table_panel.table.setColumnWidth(0, 70) # Cópias
        if has_sig:
            self.table_panel.table.setColumnWidth(1, 50) # Assinatura

        self.table_panel.table.setRowCount(1)
        
        # 1. Configura a célula de Quantidade (Index 0)
        qty_item = QTableWidgetItem("1")
        qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_panel.table.setItem(0, 0, qty_item)
        
        # 2. Configura a célula de Assinatura (Index 1), se existir
        if has_sig:
            default_state = True
            for sig in signatures:
                if not sig.get("visible", True):
                    default_state = False
                    break
            
            chk_item = QTableWidgetItem("")
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            chk_item.setCheckState(Qt.CheckState.Checked if default_state else Qt.CheckState.Unchecked)
            chk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_panel.table.setItem(0, 1, chk_item)

    def _on_table_selection(self):
        if not self.cached_model_data: return
        if self._preview_mode == "sheet":
            self._render_current_sheet_preview()
            return
        row = self.table_panel.table.currentRow()
        
        # --- LEGO: Fallback para a Thumbnail Estática se não houver linha selecionada ---
        if row < 0:
            slug = slugify_model_name(self.active_model_name)
            thumb_path = get_models_dir() / slug / ".render_cache" / "thumbnail_raw.png"
            if thumb_path.exists():
                self.preview_panel.set_preview_image(str(thumb_path))
            return
        # --- FIM DO LEGO ---

        try:
            row_rich = self._get_row_data_rich(row)
            # Reutiliza o renderer existente. O cache de QPixmaps estará pronto aqui.
            if not self.preview_renderer:
                self.preview_renderer = NativeRenderer(self.cached_model_data)
            
            pix = self.preview_renderer.render_to_pixmap(row_rich=row_rich, max_side=1600)
            self.preview_panel.set_preview_pixmap(pix)
            visible_rows = self._visible_preview_rows()
            index = visible_rows.index(row) if row in visible_rows else 0
            self.preview_panel.set_navigation(
                "item", index, len(visible_rows),
                sheet_available=self._sheet_preview_available(),
            )
        except Exception as e:
            print(f"Erro no Live Preview: {e}")

    def _visible_preview_rows(self):
        table = self.table_panel.table
        return [row for row in range(table.rowCount()) if not table.isRowHidden(row)]

    def _sheet_preview_available(self):
        return bool(self.cached_model_data and self._resolve_imposition_settings().get("enabled"))

    def _on_preview_mode_changed(self, mode):
        previous_mode = self._preview_mode
        self._preview_mode = mode if mode == "sheet" and self._sheet_preview_available() else "item"
        if self._preview_mode == "sheet":
            if previous_mode == "item":
                self._preview_sheet_index = self._sheet_index_for_table_row(
                    self.table_panel.table.currentRow()
                )
            self._render_current_sheet_preview()
        else:
            if previous_mode == "sheet":
                self._select_first_item_from_sheet(self._preview_sheet_index)
            self._refresh_preview_navigation()
            self._on_table_selection()

    def _sheet_index_for_table_row(self, table_row):
        rows_plain, rows_rich, source_rows = self._scrape_table_data(include_sources=True)
        plan = build_imposition_plan(list(zip(rows_plain, rows_rich)), self._resolve_imposition_settings())
        if not plan.pages or table_row < 0:
            return 0
        try:
            production_index = source_rows.index(table_row)
        except ValueError:
            # Uma linha com quantidade zero não está na produção. Usa a ocorrência
            # válida mais próxima para manter a navegação previsível.
            production_index = next(
                (index for index, source in enumerate(source_rows) if source > table_row),
                max(0, len(source_rows) - 1),
            )
        return min(production_index // plan.capacity, len(plan.pages) - 1)

    def _select_first_item_from_sheet(self, sheet_index):
        rows_plain, rows_rich, source_rows = self._scrape_table_data(include_sources=True)
        plan = build_imposition_plan(list(zip(rows_plain, rows_rich)), self._resolve_imposition_settings())
        if not plan.pages or not source_rows:
            return
        sheet_index = min(max(0, sheet_index), len(plan.pages) - 1)
        production_index = sheet_index * plan.capacity
        table_row = source_rows[min(production_index, len(source_rows) - 1)]
        table = self.table_panel.table
        column = table.currentColumn()
        if column < 0 or column >= table.columnCount():
            column = 0
        table.setCurrentCell(table_row, column)

    def _on_preview_index_requested(self, index):
        if self._preview_mode == "sheet":
            rows_plain, rows_rich = self._scrape_table_data()
            plan = build_imposition_plan(list(zip(rows_plain, rows_rich)), self._resolve_imposition_settings())
            if not plan.pages:
                self._render_current_sheet_preview()
                return
            self._preview_sheet_index = min(max(0, index), len(plan.pages) - 1)
            self._render_current_sheet_preview(plan)
            return

        rows = self._visible_preview_rows()
        if not rows:
            self._refresh_preview_navigation()
            return
        index = min(max(0, index), len(rows) - 1)
        table = self.table_panel.table
        column = table.currentColumn()
        if column < 0 or column >= table.columnCount():
            column = 0
        table.setCurrentCell(rows[index], column)

    def _refresh_preview_navigation(self):
        sheet_available = self._sheet_preview_available()
        if self._preview_mode == "sheet" and sheet_available:
            rows_plain, rows_rich = self._scrape_table_data()
            plan = build_imposition_plan(list(zip(rows_plain, rows_rich)), self._resolve_imposition_settings())
            total = len(plan.pages)
            self._preview_sheet_index = min(self._preview_sheet_index, max(0, total - 1))
            self.preview_panel.set_navigation(
                "sheet", self._preview_sheet_index, total, sheet_available=True
            )
            return

        if not sheet_available:
            self._preview_mode = "item"
        rows = self._visible_preview_rows()
        current = self.table_panel.table.currentRow()
        index = rows.index(current) if current in rows else 0
        self.preview_panel.set_navigation(
            "item", index, len(rows), sheet_available=sheet_available
        )

    def _on_preview_data_changed(self, _item=None):
        self._invalidate_sheet_previews()
        self._preview_refresh_timer.start()

    def _on_preview_rows_changed(self, *_args):
        self._invalidate_sheet_previews()
        self._preview_refresh_timer.start()

    def _refresh_preview_after_data_change(self):
        self._refresh_preview_navigation()
        if self._preview_mode == "sheet":
            self._render_current_sheet_preview()
        else:
            self._on_table_selection()
            self._start_sheet_preview_preload()

    def _invalidate_sheet_previews(self):
        self._sheet_preview_revision += 1
        self._sheet_preview_paths.clear()
        self._stop_sheet_preview_worker()
        if self._sheet_preview_dir:
            self._stale_sheet_preview_dirs.add(self._sheet_preview_dir)
            self._sheet_preview_dir = None

    def _stop_sheet_preview_worker(self, *, wait=False):
        worker = self._sheet_preview_worker
        if worker and worker.isRunning():
            worker.stop()
            worker.requestInterruption()
            if wait:
                worker.wait()
        self._sheet_preview_worker = None

    def _start_sheet_preview_preload(self, plan=None, first_page=None):
        if not self._sheet_preview_available():
            return
        if self._sheet_preview_worker and self._sheet_preview_worker.isRunning():
            return

        if plan is None:
            rows_plain, rows_rich = self._scrape_table_data()
            rows = list(zip(rows_plain, rows_rich))
            plan = build_imposition_plan(rows, self._resolve_imposition_settings())
        else:
            rows = [entry for page in plan.pages for entry in page]
        if not plan.pages:
            return

        first_page = self._preview_sheet_index if first_page is None else first_page
        output_dir = tempfile.mkdtemp(prefix="fornax_sheet_preview_")
        self._sheet_preview_dir = output_dir
        generation = self._sheet_preview_revision
        worker = SheetPreviewWorker(
            copy.deepcopy(self.cached_model_data), rows,
            dict(self._resolve_imposition_settings()), output_dir,
            generation, first_page=first_page, parent=self,
        )
        self._sheet_preview_worker = worker
        self._sheet_preview_workers.add(worker)
        worker.pageReady.connect(self._on_sheet_preview_ready)
        worker.pageFailed.connect(self._on_sheet_preview_failed)
        worker.finished.connect(lambda directory=output_dir, current=worker: self._on_sheet_preview_finished(current, directory))
        worker.finished.connect(worker.deleteLater)
        worker.start(QThread.Priority.LowPriority)

    def _on_sheet_preview_ready(self, page_index, path, generation):
        if generation != self._sheet_preview_revision:
            return
        self._sheet_preview_paths[page_index] = path
        if self._preview_mode == "sheet" and page_index == self._preview_sheet_index:
            self.preview_panel.set_preview_image(path)

    def _on_sheet_preview_failed(self, _page_index, message, generation):
        if generation == self._sheet_preview_revision:
            self.log_panel.append(f"Erro na prévia da folha: {message}")

    def _on_sheet_preview_finished(self, worker, directory):
        self._sheet_preview_workers.discard(worker)
        if self._sheet_preview_worker is worker:
            self._sheet_preview_worker = None
        if directory in self._stale_sheet_preview_dirs:
            shutil.rmtree(directory, ignore_errors=True)
            self._stale_sheet_preview_dirs.discard(directory)

    def _render_current_sheet_preview(self, plan=None):
        if not self._sheet_preview_available():
            self._preview_mode = "item"
            self._on_table_selection()
            return

        if plan is None:
            rows_plain, rows_rich = self._scrape_table_data()
            plan = build_imposition_plan(list(zip(rows_plain, rows_rich)), self._resolve_imposition_settings())
        total = len(plan.pages)
        if not total:
            self.preview_panel.set_preview_text("Não há itens para montar a folha")
            self.preview_panel.set_navigation("sheet", 0, 0, sheet_available=True)
            return

        self._preview_sheet_index = min(max(0, self._preview_sheet_index), total - 1)
        self.preview_panel.set_navigation(
            "sheet", self._preview_sheet_index, total, sheet_available=True
        )
        path = self._sheet_preview_paths.get(self._preview_sheet_index)
        if path and Path(path).exists():
            self.preview_panel.set_preview_image(path)
            return
        self.preview_panel.set_preview_text("Carregando preview")
        self._start_sheet_preview_preload(plan, first_page=self._preview_sheet_index)

    def _open_model_dialog(self):
        current_model_name = self.preview_panel.cbo_models.currentText()
        if not current_model_name:
            QMessageBox.warning(self, "Atenção", "Selecione um modelo na lista antes de configurar.")
            return
            
        self.active_model_name = current_model_name

        slug = slugify_model_name(current_model_name)
        json_path = get_models_dir() / slug / "template_v3.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                missing_fonts = missing_template_fonts(data)
            except Exception:
                missing_fonts = []

            if missing_fonts and not self._confirm_open_model_with_missing_fonts(missing_fonts):
                return

        self.editor_window = EditorWindow(self)
        self.editor_window.modelSaved.connect(self._on_editor_saved)

        if json_path.exists():
            self.editor_window.load_from_json(str(json_path))
        
        self.editor_window.show()

    def _confirm_open_model_with_missing_fonts(self, missing_fonts: list[str]) -> bool:
        font_names = format_font_list(missing_fonts)
        if len(missing_fonts) == 1:
            headline = f"Está faltando a fonte {font_names}."
        else:
            headline = f"Estão faltando as fontes {font_names}."

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Fonte ausente")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(
            f"<b>{headline}</b><br><br>"
            "Se você prosseguir para a edição, a fonte será substituída pela fonte padrão do sistema "
            "e o modelo sofrerá uma mudança visual."
        )

        btn_cancel = msg_box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        btn_open = msg_box.addButton("Abrir mesmo assim", QMessageBox.ButtonRole.AcceptRole)
        msg_box.setDefaultButton(btn_cancel)
        msg_box.exec()

        return msg_box.clickedButton() == btn_open

    def _on_editor_saved(self, model_name, placeholders, file_path, *, previous_name=None):
        table = self.table_panel.table
        old_name = self.preview_panel.cbo_models.currentText()
        target_name = old_name if previous_name and old_name not in (previous_name, model_name) else model_name
        current_row = table.currentRow()
        saved_rows = []
        if old_name == target_name or old_name == previous_name:
            for row in range(table.rowCount()):
                saved_rows.append({table.horizontalHeaderItem(col).text(): table.item(row, col).clone()
                                   for col in range(table.columnCount()) if table.item(row, col)})
        blocker = QSignalBlocker(table)
        # Formata o log conforme o seu novo padrão
        self.log_panel.append(f"<b>Modelo '{model_name}' salvo com sucesso em:</b> {file_path}")
        self.log_panel.append("Atualizando lista...")
        self._reload_models_from_disk(select_name=target_name)
        if saved_rows and self.preview_panel.cbo_models.currentText() == target_name:
            defaults = [table.item(0, col).clone() if table.item(0, col) else None for col in range(table.columnCount())]
            table.setRowCount(len(saved_rows))
            for row, values in enumerate(saved_rows):
                for col in range(table.columnCount()):
                    name = table.horizontalHeaderItem(col).text()
                    item = values.get(name, defaults[col])
                    if item:
                        table.setItem(row, col, item.clone())
            if current_row >= 0:
                table.setCurrentCell(min(current_row, table.rowCount()-1), 0)
        del blocker
        self._on_table_selection()

    def _open_config_dialog(self):
        current_model_name = self.preview_panel.cbo_models.currentText()
        if not current_model_name:
            QMessageBox.warning(self, "Atenção", "Selecione um modelo primeiro.")
            return
            
        self.active_model_name = current_model_name
        cols = self.table_panel.table.columnCount()
        # Adiciona 'modelo' explicitamente como uma variável disponível no diálogo
        vars_available = ["modelo"] + [self.table_panel.table.horizontalHeaderItem(c).text() for c in range(cols)]
        slug = slugify_model_name(self.active_model_name)
        
        current_imposition = None
        model_size = (1000, 1000) 
        model_print_size_mm = (100.0, 100.0)
        has_any_link = False

        if self.cached_model_data:
            sz = self.cached_model_data.get("canvas_size", {})
            model_size = (sz.get("w", 1000), sz.get("h", 1000))
            model_print_size_mm = self._get_model_base_print_size_mm()
            current_imposition = self.cached_model_data.get("imposition_settings") 
            has_any_link = any(box.get("has_link") for box in (self.cached_model_data.get("boxes", []) + self.cached_model_data.get("images", []) + self.cached_model_data.get("shapes", [])))

        dlg = ExportConfigDialog(self, slug, vars_available, self.current_filename_suffix,
                           model_size_px=model_size, 
                           model_print_size_mm=model_print_size_mm,
                           current_imposition=current_imposition)
        
        dlg.set_link_warning_visible(has_any_link)
        
        if dlg.exec():
            new_suffix = dlg.get_pattern()
            new_imposition = dlg.get_imposition_settings() 
            self.current_filename_suffix = new_suffix
            
            json_path = get_models_dir() / slug / "template_v3.json"
            if json_path.exists():
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    data["output_suffix"] = new_suffix
                    data["imposition_settings"] = new_imposition 
                    
                    if self.cached_model_data:
                        self.cached_model_data["output_suffix"] = new_suffix
                        self.cached_model_data["imposition_settings"] = new_imposition

                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                except Exception as e:
                    print(f"Erro ao salvar config: {e}")

            msg_imp = " [Imposição A4 ATIVADA]" if new_imposition["enabled"] else ""
            if self.current_filename_suffix:
                self.log_panel.append(f"Configuração salva: {slug}_{self.current_filename_suffix}.png{msg_imp}")
            else:
                self.log_panel.append(f"Configuração salva: Sequencial automático{msg_imp}")

            self._refresh_imposition_presets()
            self._invalidate_sheet_previews()
            self._refresh_preview_navigation()
            if self._preview_mode == "sheet":
                self._render_current_sheet_preview()
            else:
                self._start_sheet_preview_preload()

    def _open_theme_dialog(self):
        dlg = ThemeDialog(self)
        dlg.exec()

    def _select_output_folder(self):
        start_dir = self.txt_output_path.text() or ""
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Saída", start_dir)
        if folder:
            self.txt_output_path.setText(folder)
            self.settings.setValue("last_output_dir", folder)

    def _update_template_json(self, new_data: dict):
        """Método auxiliar para atualizar metadados no template_v3.json."""
        if not self.active_model_name:
            return
        slug = slugify_model_name(self.active_model_name)
        json_path = get_models_dir() / slug / "template_v3.json"
        if json_path.exists():
            try:
                if self.cached_model_data:
                    self.cached_model_data.update(new_data)
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data.update(new_data)
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao atualizar JSON do modelo: {e}")

    def _current_export_mode(self):
        mode = self.cbo_export_format.currentData()
        export_format = "PNG" if mode == "png" else "PDF"
        return mode, export_format, mode == "pdf_grouped"

    def _refresh_export_mode_tooltip(self):
        mode = self.cbo_export_format.currentData()
        self.cbo_export_format.setToolTip(self._export_mode_tooltips.get(mode, ""))

    def _on_export_mode_changed(self, _index):
        self._refresh_export_mode_tooltip()
        mode, export_format, single_pdf = self._current_export_mode()
        self._update_template_json({
            "last_export_mode": mode,
            "last_export_format": export_format,
            "last_single_pdf": single_pdf,
        })

    def _scrape_table_data(self, *, include_sources=False):
        table = self.table_panel.table
        rows = table.rowCount()
        cols = table.columnCount()
        headers = [table.horizontalHeaderItem(c).text() for c in range(cols)]
        data_plain, data_rich, source_rows = [], [], []

        for r in range(rows):
            row_p, row_r = {}, {}
            # Injeta o slug do modelo atual para permitir substituição dinâmica {modelo}
            current_slug = slugify_model_name(self.active_model_name)
            row_p["modelo"] = current_slug
            row_r["modelo"] = current_slug
            multiplier = 1
            has_content = False
            
            for c in range(cols):
                key = headers[c]
                item = table.item(r, c)
                
                # 1. Trata a nova coluna de Quantidade
                if key == QUANTITY_HEADER:
                    try:
                        val = int(item.text().strip()) if item else 1
                        multiplier = max(0, val) # Impede números negativos
                    except ValueError:
                        multiplier = 1
                    continue

                # 2. Trata a coluna de Assinatura
                if key == SIGNATURE_HEADER:
                    use_sig = (item.checkState() == Qt.CheckState.Checked) if item else True
                    row_p["__use_signature__"] = use_sig
                    row_r["__use_signature__"] = use_sig
                    continue

                # 3. Trata placeholders comuns
                val_plain = item.text().strip() if item else ""
                val_rich = item.data(Qt.ItemDataRole.UserRole) if item else ""
                if not val_rich: val_rich = val_plain
                
                if val_plain: 
                    has_content = True
                
                row_p[key] = val_plain
                row_r[key] = val_rich

            # Validação: Se a linha tiver conteúdo OU o multiplicador for > 0, 
            # nós geramos (isso permite gerar cartões sem placeholders).
            if multiplier > 0:
                for _ in range(multiplier):
                    data_plain.append(row_p.copy())
                    data_rich.append(row_r.copy())
                    source_rows.append(r)
                    
        if include_sources:
            return data_plain, data_rich, source_rows
        return data_plain, data_rich
    
    def _get_row_data_rich(self, row_idx):
        table = self.table_panel.table
        cols = table.columnCount()
        headers = [table.horizontalHeaderItem(c).text() for c in range(cols)]
        
        row_data = {}
        for c in range(cols):
            key = headers[c]
            item = table.item(row_idx, c)
            
            # Ignora a coluna de quantidade no preview técnico do cartão
            if key == QUANTITY_HEADER:
                continue
                
            if key == SIGNATURE_HEADER:
                row_data["__use_signature__"] = (item.checkState() == Qt.CheckState.Checked) if item else True
                continue
                
            val = ""
            if item:
                val = item.data(Qt.ItemDataRole.UserRole)
                if not val: val = item.text()
            row_data[key] = val
        return row_data

    def _get_model_base_print_size_mm(self, model_data: dict = None):
        """Retorna o tamanho físico próprio do modelo, sem presets de impressão."""
        data = model_data or self.cached_model_data or {}

        w = data.get("target_w_mm", 0) or 0
        h = data.get("target_h_mm", 0) or 0
        if w > 0 and h > 0:
            return float(w), float(h)

        canvas = data.get("canvas_size", {})
        canvas_w = canvas.get("w", 1000)
        canvas_h = canvas.get("h", 1000)
        return (canvas_w / 300.0) * 25.4, (canvas_h / 300.0) * 25.4

    def _resolve_imposition_settings(self):
        """Resolve a configuração efetiva sem deixar presets contaminarem o modelo base."""
        base_w, base_h = self._get_model_base_print_size_mm()
        imp = (self.cached_model_data or {}).get("imposition_settings", {}) or {}
        presets = imp.get("presets", {}) or {}
        active_name = imp.get("active_preset_name") or self.SYSTEM_IMPOSITION_PRESET

        if active_name == self.SYSTEM_IMPOSITION_PRESET or active_name not in presets:
            return {
                "enabled": False,
                "target_w_mm": base_w,
                "target_h_mm": base_h,
                "active_preset_name": self.SYSTEM_IMPOSITION_PRESET,
            }

        preset = presets[active_name]
        return {
            "enabled": preset.get("enabled", False),
            "sheet_w_mm": preset.get("sheet_w", 210.0),
            "sheet_h_mm": preset.get("sheet_h", 297.0),
            "crop_marks": preset.get("crop", True),
            "bleed_margin": preset.get("bleed", True),
            "target_w_mm": preset.get("w", base_w),
            "target_h_mm": preset.get("h", base_h),
            "active_preset_name": active_name,
        }

    def _generate_cards_async(self):
        rows_plain, rows_rich = self._scrape_table_data()
        if not rows_plain:
            self.log_panel.append("AVISO: A tabela está vazia. Nada a gerar.")
            return

        current_name = self.preview_panel.cbo_models.currentText()
        if not current_name:
            self.log_panel.append("ERRO: Nenhum modelo selecionado.")
            return
        
        _, export_format, _ = self._current_export_mode()
        has_any_link = False
        if self.cached_model_data:
            has_any_link = any(box.get("has_link") for box in (self.cached_model_data.get("boxes", []) + self.cached_model_data.get("images", []) + self.cached_model_data.get("shapes", [])))

        if export_format == "PNG" and has_any_link:
            resp = QMessageBox.question(
                self, 
                "Aviso: Hiperlinks desativados em PNG",
                "Este modelo possui hiperlinks ativos, mas o formato de saída atual é PNG.\n\n"
                "Os hiperlinks SÓ funcionam em formato PDF. Deseja continuar mesmo assim e gerar as imagens sem links?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if resp == QMessageBox.StandardButton.No:
                self.log_panel.append("🛑 Geração cancelada para alteração de formato.")
                return
            
        slug = slugify_model_name(current_name)
        template_path = get_models_dir() / slug / "template_v3.json"

        if not template_path.exists():
            self.log_panel.append(f"ERRO: Modelo '{self.active_model_name}' não encontrado.")
            return

        with open(template_path, "r", encoding="utf-8") as f:
            tpl_data = json.load(f)
            model_dir = template_path.parent
            if tpl_data.get("background_path") and not Path(tpl_data["background_path"]).is_absolute():
                tpl_data["background_path"] = str(model_dir / tpl_data["background_path"])
            for sig in tpl_data.get("signatures", []):
                if not Path(sig["path"]).is_absolute():
                    sig["path"] = str(model_dir / sig["path"])
            tpl_data["__model_dir"] = str(model_dir)
            ensure_background_proxy(model_dir, tpl_data)

        renderer = NativeRenderer(tpl_data)

        custom_path = self.txt_output_path.text().strip()
        if not custom_path:
            QMessageBox.warning(
                self, tr("Atenção"),
                tr("Por favor, selecione uma pasta de saída antes de gerar o material.")
            )
            self.log_panel.append("🛑 Geração cancelada: Pasta de saída não definida.")
            return

        base_dir = Path(custom_path)
        self.settings.setValue("last_output_dir", custom_path)

        output_dir, _forge_number = create_forge_output_dir(base_dir, self.settings)
        folder_name = output_dir.name
        
        self.log_panel.append(f"📂 Salvando em: {folder_name}")

        self.btn_generate_cards.setEnabled(False)
        self.btn_generate_cards.setText(tr("Gerando… Aguarde"))
        self.progress_bar.setValue(0)
        self.log_panel.append(
            tr("--- Iniciando lote de {count} itens ---").format(count=len(rows_plain))
        )

        # O padrão agora é 100% o que o usuário definiu. 
        # Se estiver vazio, usamos {modelo} como fallback padrão.
        full_pattern = self.current_filename_suffix if self.current_filename_suffix else "{modelo}"

        imposition_cfg = self._resolve_imposition_settings()
        model_w_mm, model_h_mm = self._get_model_base_print_size_mm()
        _, export_format, is_single_pdf = self._current_export_mode()

        self.manager = RenderManager(
            renderer, 
            rows_plain, 
            rows_rich, 
            output_dir, 
            full_pattern,
            imposition_settings=imposition_cfg,
            export_format=export_format,
            single_pdf=is_single_pdf,
            target_w_mm=model_w_mm,
            target_h_mm=model_h_mm
        )
        
        self.manager.progress_updated.connect(self.progress_bar.setValue)
        self.manager.log_updated.connect(self.log_panel.append)
        self.manager.error_occurred.connect(lambda msg: self.log_panel.append(f"[ERRO] {msg}"))
        self.manager.finished_process.connect(self._on_generation_finished)
        
        self.start_time = time.time()
        self.manager.start()

    def _on_generation_finished(self):
        self.btn_generate_cards.setEnabled(True)
        self.btn_generate_cards.setText(tr("Gerar material"))
        end_time = time.time()
        duration = end_time - getattr(self, 'start_time', end_time)
        
        if duration < 60:
            time_str = f"{duration:.1f} segundos"
        else:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            time_str = f"{minutes} min {seconds}s"

        self.log_panel.append("=== Processo Finalizado ===")    
        self.log_panel.append(f"⏱️ Tempo total: {time_str}")
        
    def _refresh_imposition_presets(self):
        """Atualiza a lista de presets rápidos na tela principal baseada no modelo atual."""
        SYSTEM_PRESET = self.SYSTEM_IMPOSITION_PRESET
        
        self.cbo_presets_main.blockSignals(True)
        self.cbo_presets_main.clear()

        # O preset de sistema sempre existe, mesmo sem modelo carregado
        self.cbo_presets_main.addItem(tr("Definição do Modelo"), SYSTEM_PRESET)
        self.cbo_presets_main.setEnabled(True)

        if self.cached_model_data:
            imp_settings = self.cached_model_data.setdefault("imposition_settings", {})
            presets = imp_settings.get("presets", {}) or {}
            active_name = imp_settings.get("active_preset_name", "")
            model_w, model_h = self._get_model_base_print_size_mm()

            user_presets = sorted(k for k in presets.keys() if k != SYSTEM_PRESET)
            for name in user_presets:
                preset = presets.get(name, {}) or {}
                label = warning_display_name(name, preset, model_w, model_h)
                self.cbo_presets_main.addItem(label, name)
                idx = self.cbo_presets_main.count() - 1
                tooltip = warning_tooltip(name, preset, model_w, model_h)
                if tooltip:
                    self.cbo_presets_main.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)

            # Sincroniza a seleção com o preset ativo salvo
            if active_name and active_name != SYSTEM_PRESET:
                idx = self.cbo_presets_main.findData(active_name, Qt.ItemDataRole.UserRole)
                if idx >= 0:
                    self.cbo_presets_main.setCurrentIndex(idx)
                else:
                    self.cbo_presets_main.setCurrentIndex(0)
                    imp_settings["active_preset_name"] = SYSTEM_PRESET
                    imp_settings["enabled"] = False
                    self._update_template_json({"imposition_settings": imp_settings})
            else:
                self.cbo_presets_main.setCurrentIndex(0)
                if active_name != SYSTEM_PRESET:
                    imp_settings["active_preset_name"] = SYSTEM_PRESET
                    imp_settings["enabled"] = False
                    self._update_template_json({"imposition_settings": imp_settings})

        self.cbo_presets_main.blockSignals(False)
        self._refresh_main_preset_tooltip()

    def _on_main_preset_changed(self, index):
        """Atualiza qual predefinição será usada, sem sobrescrever o modelo base."""
        SYSTEM_PRESET = self.SYSTEM_IMPOSITION_PRESET
        if not self.cached_model_data or index < 0: return
        
        name = self._main_preset_name_at(index)
        
        imp = self.cached_model_data.setdefault("imposition_settings", {})

        if name == SYSTEM_PRESET:
            imp["enabled"] = False
            imp["active_preset_name"] = SYSTEM_PRESET
            self._update_template_json({"imposition_settings": imp})
            self.log_panel.append(f"⚡ Layout aplicado: <b>{SYSTEM_PRESET}</b>")
            self._refresh_main_preset_tooltip()
            self._invalidate_sheet_previews()
            self._refresh_preview_navigation()
            if self._preview_mode == "item":
                self._on_table_selection()
            return

        presets = imp.get("presets", {}) or {}
        if name in presets:
            imp["active_preset_name"] = name
            self._update_template_json({"imposition_settings": imp})
            self.log_panel.append(f"⚡ Layout aplicado: <b>{name}</b>")
        self._refresh_main_preset_tooltip()
        self._invalidate_sheet_previews()
        self._refresh_preview_navigation()
        if self._preview_mode == "sheet":
            self._render_current_sheet_preview()
        else:
            self._start_sheet_preview_preload()

    def _main_preset_name_at(self, index):
        name = self.cbo_presets_main.itemData(index, Qt.ItemDataRole.UserRole)
        return name if name else self.cbo_presets_main.itemText(index)

    def _refresh_main_preset_tooltip(self):
        if not self.cached_model_data:
            self.cbo_presets_main.setToolTip(self._presets_main_base_tooltip)
            return

        name = self._main_preset_name_at(self.cbo_presets_main.currentIndex())
        imp_settings = self.cached_model_data.get("imposition_settings", {}) or {}
        preset = (imp_settings.get("presets", {}) or {}).get(name, {})
        model_w, model_h = self._get_model_base_print_size_mm()
        tooltip = warning_tooltip(name, preset, model_w, model_h)
        self.cbo_presets_main.setToolTip(tooltip or self._presets_main_base_tooltip)
    

   
