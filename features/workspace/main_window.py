import zipfile
import os
import shutil
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                                QSplitter, QPushButton, QApplication, QMessageBox,
                                  QLineEdit, QLabel, QFileDialog, QProgressBar,
                                  QInputDialog, QComboBox, QCheckBox, QTableWidgetItem)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QPainter, QImage, QPageLayout, QPalette, QColor

from features.preview.preview_panel import PreviewPanel
from features.workspace.controls_panel import ControlsPanel
from shared.log_panel import LogPanel
from features.spreadsheet.table_panel import TablePanel
from features.generator.renderer import NativeRenderer
from features.editor.editor_window import EditorWindow
from features.generator.manager import RenderManager
from features.generator.export_dialog import ConfigDialog
from features.workspace.import_models_dialog import ImportModelsDialog
from features.workspace.export_models_dialog import ExportModelsDialog
from core.template_manager import slugify_model_name
from core.paths import get_models_dir




class MainWindow(QMainWindow):
    def _apply_tooltip(self, widget, text):
            """Aplica tooltip e garante que labels estáticos capturem o evento no motor customizado."""
            if isinstance(widget, QLabel):
                widget.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
            widget.setToolTip(text)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto COMSOC - Construtor Otimizado de Material Social Oficial e Cerimonial")
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
        left.setMinimumWidth(500) # Ajustado para a nova largura mínima
        self.splitter.addWidget(left)

        left_stack = QVBoxLayout(left)
        left_stack.setContentsMargins(0, 0, 0, 0)
        left_stack.setSpacing(10)

        self.preview_panel = PreviewPanel()
        self.controls_panel = ControlsPanel()
        self.controls_panel.setFixedWidth(110) # Trava a largura da sidebar
        self.log_panel = LogPanel()

        # Agrupa Preview e Controls lado a lado
        preview_container = QWidget()
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

        # --- Seletor de Pasta ---
        grp_out = QWidget()
        ly_out = QHBoxLayout(grp_out)
        ly_out.setContentsMargins(0, 0, 0, 0)
        ly_out.setSpacing(5)

        ly_out.addWidget(QLabel("Saída:"))
        
        self.txt_output_path = QLineEdit()
        self.txt_output_path.setPlaceholderText("Padrão: Documentos/ProjetoComSoc_Saida/modelo")
        ly_out.addWidget(self.txt_output_path)

        self.btn_sel_out = QPushButton("...")
        self.btn_sel_out.setFixedWidth(40)
        self._apply_tooltip(self.btn_sel_out, 
            "<b>PASTA DE DESTINO</b><br><br>"
            "Define em qual local do computador os arquivos gerados serão salvos.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: O sistema criará automaticamente uma subpasta com a data e hora atual dentro do local escolhido para manter seus lotes organizados.</small>")
        self.btn_sel_out.clicked.connect(self._select_output_folder)
        ly_out.addWidget(self.btn_sel_out)

        self.cbo_export_format = QComboBox()
        self.cbo_export_format.addItems(["PNG", "PDF"])
        self.cbo_export_format.setFixedWidth(60)
        self._apply_tooltip(self.cbo_export_format, 
            "<b>FORMATO DE SAÍDA</b><br><br>"
            "Escolha o tipo de arquivo final:<br>"
            "• <b>PNG:</b> Ideal para imagens estáticas de alta qualidade.<br>"
            "• <b>PDF:</b> Formato padrão para documentos e impressões, permitindo o uso de links interativos.")
        ly_out.addWidget(self.cbo_export_format)

        self.chk_single_pdf = QCheckBox("Arquivo Único")
        self._apply_tooltip(self.chk_single_pdf, 
            "<b>ARQUIVO ÚNICO (PDF)</b><br><br>"
            "Agrupa todo o lote gerado em um único documento de múltiplas páginas, em vez de criar arquivos separados.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Ideal para impressões em massa. Você abre apenas um arquivo e envia todas as páginas para a impressora de uma só vez, economizando tempo.</small>")
        self.chk_single_pdf.setVisible(False)
        ly_out.addWidget(self.chk_single_pdf)

        self.btn_config_name = QPushButton("Configurações")
        self.btn_config_name.setFixedWidth(100)
        self._apply_tooltip(self.btn_config_name, 
            "<b>CONFIGURAÇÕES GERAIS</b><br><br>"
            "Acesso aos ajustes avançados do projeto e do sistema:<br>"
            "• <b>Nomenclatura:</b> Define o padrão de nome dos arquivos gerados usando as variáveis da tabela.<br>"
            "• <b>Impressão:</b> Configura o agrupamento de vários cartões em uma folha e ativa marcas de corte.<br>"
            "• <b>Tema:</b> Alterna a interface do programa entre os modos Claro e Escuro.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Na aba de Impressão, o sistema calcula automaticamente quantos cartões cabem na folha assim que você digita as dimensões.</small>")
        self.btn_config_name.clicked.connect(self._open_config_dialog)
        ly_out.addWidget(self.btn_config_name)

        left_stack.addWidget(grp_out, 0)

        self.btn_generate_cards = QPushButton("Gerar Material")
        self.btn_generate_cards.setMinimumHeight(44)
        self._apply_tooltip(self.btn_generate_cards, 
            "<b>GERAR MATERIAL</b><br><br>"
            "Inicia o processamento da tabela e a construção dos arquivos finais na pasta de saída.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Faça uma checagem rápida nas colunas de Quantidade e Assinatura antes de iniciar a geração de lotes muito grandes para evitar desperdícios.</small>")
        self.btn_generate_cards.clicked.connect(self._generate_cards_async)
        left_stack.addWidget(self.btn_generate_cards, 0)

        # --- Painel DIREITO ---
        self.table_panel = TablePanel()
        self.splitter.addWidget(self.table_panel)

        self.splitter.setSizes([640, 640])
        self.splitter.setCollapsible(0, False)

        self.cached_model_data = None
        
        # Garante que um usuário novato não veja uma tela em branco
        self._ensure_starter_pack()

        # O reload já se encarrega de setar o active_model_name e chamar o _on_model_changed
        self._reload_models_from_disk()

        self.preview_panel.cbo_models.currentTextChanged.connect(self._on_model_changed)

        # Sincronização de preferências e visibilidade
        self.cbo_export_format.currentTextChanged.connect(self._toggle_single_pdf_option)
        self.cbo_export_format.currentTextChanged.connect(self._save_export_format_pref)
        self.chk_single_pdf.toggled.connect(self._save_single_pdf_pref)

        self.table_panel.table.itemSelectionChanged.connect(self._on_table_selection)

        # --- Conexões dos Botões de Controle ---
        self.controls_panel.btn_add_model.clicked.connect(self._on_add_model)
        self.controls_panel.btn_duplicate_model.clicked.connect(self._on_duplicate_model)
        self.controls_panel.btn_remove_model.clicked.connect(self._on_remove_model)
        self.controls_panel.btn_rename_model.clicked.connect(self._on_rename_model) 
        self.controls_panel.btn_config_model.clicked.connect(self._open_model_dialog)
        self.controls_panel.btn_import_models.clicked.connect(self._on_import_models)
        self.controls_panel.btn_export_models.clicked.connect(self._on_export_models)

        self.settings = QSettings("Projeto ComSoc", "MainApp")
        
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
        is_dark = self.settings.value("dark_mode", True, type=bool)
        self._apply_theme(is_dark)

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

    def _apply_theme(self, is_dark: bool):
        app = QApplication.instance()
        if not app: return
        
        app.setStyle("Fusion")
        
        if is_dark:
            palette = QPalette()
            # Cores exatas extraídas do Mint-Y-Dark
            bg_color = QColor("#2e2e33")
            text_color = QColor("#DADADA")
            alt_base_color = QColor("#222226")
            button_color = QColor("#333338")
            highlight_color = QColor("#35A854")
            
            palette.setColor(QPalette.ColorRole.Window, bg_color)
            palette.setColor(QPalette.ColorRole.WindowText, text_color)
            palette.setColor(QPalette.ColorRole.Base, bg_color)
            palette.setColor(QPalette.ColorRole.AlternateBase, alt_base_color)
            palette.setColor(QPalette.ColorRole.ToolTipBase, bg_color)
            palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
            palette.setColor(QPalette.ColorRole.Text, text_color)
            palette.setColor(QPalette.ColorRole.Button, button_color)
            palette.setColor(QPalette.ColorRole.ButtonText, text_color)
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#5294E2"))
            palette.setColor(QPalette.ColorRole.Highlight, highlight_color)
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
            
            # Textos e botões desabilitados
            disabled_color = QColor(255, 255, 255, 107)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color)

            app.setPalette(palette)
            # Reforço global para bordas finas (Fusion costuma ignorar na paleta)
            app.setStyleSheet("QTableWidget, QLineEdit, QTextEdit { border: 1px solid #202023; }")
        else:
            palette = QPalette()
            # Paleta Clara Fixa (Independente de SO)
            window_color = QColor("#F5F5F5")
            text_color = QColor("#1A1A1A")
            base_color = QColor("#FFFFFF")
            btn_color = QColor("#E0E0E0")
            highlight_green = QColor("#35A854")

            palette.setColor(QPalette.ColorRole.Window, window_color)
            palette.setColor(QPalette.ColorRole.WindowText, text_color)
            palette.setColor(QPalette.ColorRole.Base, base_color)
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#EBEBEB"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, base_color)
            palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
            palette.setColor(QPalette.ColorRole.Text, text_color)
            palette.setColor(QPalette.ColorRole.Button, btn_color)
            palette.setColor(QPalette.ColorRole.ButtonText, text_color)
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#0000EE"))
            palette.setColor(QPalette.ColorRole.Highlight, highlight_green)
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))

            # Estados desabilitados para o modo claro
            disabled_text = QColor(0, 0, 0, 110)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text)

            app.setPalette(palette)
            # Bordas sutis para manter profundidade visual no modo claro
            app.setStyleSheet("QTableWidget, QLineEdit, QTextEdit { border: 1px solid #C0C0C0; }")
            
        if hasattr(self, 'settings'):
            self.settings.setValue("dark_mode", is_dark)

    def closeEvent(self, event):
        """Salva a posição, tamanho e estado do splitter ao fechar o programa."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitterState", self.splitter.saveState())
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
                
                for zip_slug in top_level_folders:
                    json_path = f"{zip_slug}/template_v3.json"
                    try:
                        with zip_ref.open(json_path) as f:
                            data = json.loads(f.read().decode('utf-8'))
                            name = data.get("name", zip_slug)
                            models_in_zip[name] = zip_slug
                    except KeyError: 
                        # Se o modelo não tiver um JSON válido, usamos o nome bruto da pasta
                        models_in_zip[zip_slug] = zip_slug
                        
                if not models_in_zip:
                    QMessageBox.warning(self, "Arquivo Inválido", "Este arquivo ZIP não contém modelos compatíveis com o Projeto ComSoc.")
                    return
                
                # Etapa 2: Checagem de Conflitos e Abertura da Janela de Decisão
                existing_slugs = set(d.name for d in models_dir.iterdir() if d.is_dir())
                
                dlg = ImportModelsDialog(self, list(models_in_zip.keys()), existing_slugs)
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
            
        save_path, _ = QFileDialog.getSaveFileName(self, "Exportar Modelos", "Modelos_ProjetoComSoc.zip", "Arquivos ZIP (*.zip)")
        if not save_path: return
        
        try:
            models_dir = get_models_dir()
            
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for model_name in selected_models:
                    slug = slugify_model_name(model_name)
                    model_dir = models_dir / slug
                    if not model_dir.exists(): continue
                    
                    for root, _, files in os.walk(model_dir):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = Path(slug) / file_path.relative_to(model_dir)
                            zipf.write(file_path, arcname)
            
            self.log_panel.append(f"📤 {len(selected_models)} modelo(s) exportado(s) para: {Path(save_path).name}")
            QMessageBox.information(self, "Sucesso", f"{len(selected_models)} modelo(s) exportado(s) com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Falha ao gerar o arquivo ZIP:\n{e}")

    def _on_model_changed(self, name: str):
        self.preview_panel.set_preview_text(f"Prévia do modelo selecionado:\n{name}")
        self.log_panel.append(f"Modelo ativo: {name}")
        self.active_model_name = name
        self.current_filename_suffix = ""

        if not name: return

        slug = slugify_model_name(name)
        json_path = get_models_dir() / slug / "template_v3.json"

        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    self.current_filename_suffix = data.get("output_suffix", "")

                    # Recupera preferências salvas (Formato e Checkbox)
                    last_fmt = data.get("last_export_format", "PNG")
                    last_single = data.get("last_single_pdf", False)

                    # Bloqueia sinais para evitar salvamento redundante durante o carregamento
                    self.cbo_export_format.blockSignals(True)
                    self.chk_single_pdf.blockSignals(True)
                    
                    idx = self.cbo_export_format.findText(last_fmt)
                    if idx >= 0:
                        self.cbo_export_format.setCurrentIndex(idx)
                    
                    self.chk_single_pdf.setChecked(last_single)
                    self._toggle_single_pdf_option(last_fmt)
                    
                    self.cbo_export_format.blockSignals(False)
                    self.chk_single_pdf.blockSignals(False)

                    model_dir = json_path.parent
                    if data.get("background_path") and not Path(data["background_path"]).is_absolute():
                        data["background_path"] = str(model_dir / data["background_path"])
                    for sig in data.get("signatures", []):
                        if not Path(sig["path"]).is_absolute():
                            sig["path"] = str(model_dir / sig["path"])

                    placeholders = data.get("placeholders", [])
                    signatures = data.get("signatures", [])
                    self._update_table_columns(placeholders, signatures)
                    
                    self.cached_model_data = data
                    
                    try:
                        renderer = NativeRenderer(data)
                        preview_pix = renderer.render_to_pixmap(row_rich=None)
                        self.preview_panel.set_preview_pixmap(preview_pix)
                    except Exception as e:
                        self.log_panel.append(f"Erro ao gerar preview: {e}")
                        self.preview_panel.set_preview_text("Erro ao gerar preview do modelo")
            except Exception as e:
                self.log_panel.append(f"Erro ao ler colunas do modelo: {e}")
        else:
            self.log_panel.append("Aviso: template_v3.json não encontrado.")

    def _update_table_columns(self, placeholders, signatures=None):
        self.table_panel.table.clearContents()
        self.table_panel.table.setRowCount(0)
        self.table_panel.table.setColumnCount(0)
        
        headers = ["🔢 Qtd"] # Coluna 0
        has_sig = bool(signatures)
        
        if has_sig:
            headers.append("✍️ Ass.") # Coluna 1
        
        headers.extend(placeholders)
            
        self.table_panel.table.setColumnCount(len(headers))
        self.table_panel.table.setHorizontalHeaderLabels(headers)
        
        # Ajuste de larguras iniciais
        self.table_panel.table.setColumnWidth(0, 50) # Qtd
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
        row = self.table_panel.table.currentRow()
        if row < 0: return

        try:
            row_rich = self._get_row_data_rich(row)
            renderer = NativeRenderer(self.cached_model_data)
            pix = renderer.render_to_pixmap(row_rich=row_rich)
            self.preview_panel.set_preview_pixmap(pix)
        except Exception as e:
            print(f"Erro no Live Preview: {e}")

    def _open_model_dialog(self):
        current_model_name = self.preview_panel.cbo_models.currentText()
        if not current_model_name:
            QMessageBox.warning(self, "Atenção", "Selecione um modelo na lista antes de configurar.")
            return
            
        self.active_model_name = current_model_name

        self.editor_window = EditorWindow(self)
        self.editor_window.modelSaved.connect(self._on_editor_saved)

        slug = slugify_model_name(current_model_name)
        json_path = get_models_dir() / slug / "template_v3.json"

        if json_path.exists():
            self.editor_window.load_from_json(str(json_path))
        
        self.editor_window.show()

    def _on_editor_saved(self, model_name, placeholders, file_path):
        # Formata o log conforme o seu novo padrão
        self.log_panel.append(f"<b>Modelo '{model_name}' salvo com sucesso em:</b> {file_path}")
        self.log_panel.append("Atualizando lista...")
        self._reload_models_from_disk(select_name=model_name)

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
        has_any_link = False

        if self.cached_model_data:
            sz = self.cached_model_data.get("canvas_size", {})
            model_size = (sz.get("w", 1000), sz.get("h", 1000))
            current_imposition = self.cached_model_data.get("imposition_settings") 
            has_any_link = any(box.get("has_link") for box in (self.cached_model_data.get("boxes", []) + self.cached_model_data.get("images", [])))

        # Lê o tema atual e envia para a janela de configurações
        is_dark_now = self.settings.value("dark_mode", True, type=bool)
        
        dlg = ConfigDialog(self, slug, vars_available, self.current_filename_suffix, 
                           model_size_px=model_size, 
                           current_imposition=current_imposition,
                           is_dark=is_dark_now)
        
        dlg.set_link_warning_visible(has_any_link)
        
        if dlg.exec():
            # 1. Verifica e aplica o tema IMEDIATAMENTE caso o usuário tenha alterado
            new_is_dark = dlg.radio_dark.isChecked()
            if new_is_dark != is_dark_now:
                self._apply_theme(new_is_dark)

            # 2. Continua salvando as configurações de Nomenclatura e Imposição
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

    def _save_export_format_pref(self, fmt):
        """Salva a escolha do formato (PNG/PDF) no JSON do modelo."""
        self._update_template_json({"last_export_format": fmt})

    def _save_single_pdf_pref(self, checked):
        """Salva o estado da checkbox de Arquivo Único no JSON do modelo."""
        self._update_template_json({"last_single_pdf": checked})

    def _toggle_single_pdf_option(self, fmt):
        """Gerencia a visibilidade do checkbox de PDF único."""
        is_pdf = (fmt == "PDF")
        self.chk_single_pdf.setVisible(is_pdf)
        if not is_pdf:
            self.chk_single_pdf.setChecked(False)

    def _scrape_table_data(self):
        table = self.table_panel.table
        rows = table.rowCount()
        cols = table.columnCount()
        headers = [table.horizontalHeaderItem(c).text() for c in range(cols)]
        data_plain, data_rich = [], []

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
                if key == "🔢 Qtd":
                    try:
                        val = int(item.text().strip()) if item else 1
                        multiplier = max(0, val) # Impede números negativos
                    except ValueError:
                        multiplier = 1
                    continue

                # 2. Trata a coluna de Assinatura
                if key == "✍️ Ass.":
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
            if key == "🔢 Qtd":
                continue
                
            if key == "✍️ Ass.":
                row_data["__use_signature__"] = (item.checkState() == Qt.CheckState.Checked) if item else True
                continue
                
            val = ""
            if item:
                val = item.data(Qt.ItemDataRole.UserRole)
                if not val: val = item.text()
            row_data[key] = val
        return row_data

    def _generate_cards_async(self):
        rows_plain, rows_rich = self._scrape_table_data()
        if not rows_plain:
            self.log_panel.append("AVISO: A tabela está vazia. Nada a gerar.")
            return

        current_name = self.preview_panel.cbo_models.currentText()
        if not current_name:
            self.log_panel.append("ERRO: Nenhum modelo selecionado.")
            return
        
        export_format = self.cbo_export_format.currentText()
        has_any_link = False
        if self.cached_model_data:
            has_any_link = any(box.get("has_link") for box in (self.cached_model_data.get("boxes", []) + self.cached_model_data.get("images", [])))

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

        renderer = NativeRenderer(tpl_data)

        custom_path = self.txt_output_path.text().strip()
        if not custom_path:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma pasta de saída antes de gerar o material.")
            self.log_panel.append("🛑 Geração cancelada: Pasta de saída não definida.")
            return

        base_dir = Path(custom_path)
        self.settings.setValue("last_output_dir", custom_path)

        timestamp = datetime.now().strftime("%y.%m.%d_%H.%M.%S")
        folder_name = f"Lote_{timestamp}"
        
        output_dir = base_dir / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_panel.append(f"📂 Salvando em: {folder_name}")

        self.btn_generate_cards.setEnabled(False)
        self.btn_generate_cards.setText("Gerando... (Aguarde)")
        self.progress_bar.setValue(0)
        self.log_panel.append(f"--- Iniciando lote de {len(rows_plain)} itens ---")

        # O padrão agora é 100% o que o usuário definiu. 
        # Se estiver vazio, usamos {modelo} como fallback padrão.
        full_pattern = self.current_filename_suffix if self.current_filename_suffix else "{modelo}"

        imposition_cfg = self.cached_model_data.get("imposition_settings", None)
        export_format = self.cbo_export_format.currentText()
        is_single_pdf = self.chk_single_pdf.isChecked() and export_format == "PDF"

        self.manager = RenderManager(
            renderer, 
            rows_plain, 
            rows_rich, 
            output_dir, 
            full_pattern,
            imposition_settings=imposition_cfg,
            export_format=export_format,
            single_pdf=is_single_pdf,
            target_w_mm=self.cached_model_data.get("target_w_mm", 100.0),
            target_h_mm=self.cached_model_data.get("target_h_mm", 150.0)
        )
        
        self.manager.progress_updated.connect(self.progress_bar.setValue)
        self.manager.log_updated.connect(self.log_panel.append)
        self.manager.error_occurred.connect(lambda msg: self.log_panel.append(f"[ERRO] {msg}"))
        self.manager.finished_process.connect(self._on_generation_finished)
        
        self.start_time = time.time()
        self.manager.start()

    def _on_generation_finished(self):
        self.btn_generate_cards.setEnabled(True)
        self.btn_generate_cards.setText("Gerar Material")
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
        

    

   