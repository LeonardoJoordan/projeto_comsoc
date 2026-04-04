from pathlib import Path
import shutil
import json
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                                QSplitter, QPushButton, QApplication, QMessageBox,
                                  QLineEdit, QLabel, QFileDialog, QProgressBar,
                                  QInputDialog, QComboBox, QCheckBox)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QPainter, QImage, QPageLayout
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

# --- Importações da Nova Arquitetura ---
from features.preview.preview_panel import PreviewPanel
from features.workspace.controls_panel import ControlsPanel
from shared.log_panel import LogPanel
from features.spreadsheet.table_panel import TablePanel
from features.generator.renderer import NativeRenderer
from features.editor.editor_window import EditorWindow
from features.generator.manager import RenderManager
from features.generator.export_dialog import NamingDialog
from core.template_manager import slugify_model_name

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto ComSoc - Construtor Otimizado")
        self.resize(1300, 750)

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        self.current_filename_suffix = "" 
        self.manager = None 

        # --- Painel ESQUERDO ---
        left = QWidget()
        left.setMinimumWidth(620)
        splitter.addWidget(left)

        left_stack = QVBoxLayout(left)
        left_stack.setContentsMargins(0, 0, 0, 0)
        left_stack.setSpacing(10)

        self.preview_panel = PreviewPanel()
        self.controls_panel = ControlsPanel()
        self.log_panel = LogPanel()

        left_stack.addWidget(self.preview_panel, 5)
        left_stack.addWidget(self.controls_panel, 0)
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
        self.txt_output_path.setPlaceholderText("Padrão: ./output/nome_do_modelo")
        ly_out.addWidget(self.txt_output_path)

        self.btn_sel_out = QPushButton("...")
        self.btn_sel_out.setFixedWidth(40)
        self.btn_sel_out.setToolTip("Selecionar pasta de destino")
        self.btn_sel_out.clicked.connect(self._select_output_folder)
        ly_out.addWidget(self.btn_sel_out)

        self.cbo_export_format = QComboBox()
        self.cbo_export_format.addItems(["PNG", "PDF"])
        self.cbo_export_format.setFixedWidth(60)
        self.cbo_export_format.setToolTip("Formato de saída da geração")
        ly_out.addWidget(self.cbo_export_format)

        self.chk_single_pdf = QCheckBox("Arquivo Único")
        self.chk_single_pdf.setToolTip("Agrupa todos os cartões num único arquivo PDF.")
        self.chk_single_pdf.setVisible(False)
        ly_out.addWidget(self.chk_single_pdf)

        self.btn_config_name = QPushButton("⚙️")
        self.btn_config_name.setFixedWidth(40)
        self.btn_config_name.setToolTip("Configurar padrão de nome dos arquivos e impressão")
        self.btn_config_name.clicked.connect(self._open_naming_dialog)
        ly_out.addWidget(self.btn_config_name)

        left_stack.addWidget(grp_out, 0)

        self.btn_generate_cards = QPushButton("Gerar Material")
        self.btn_generate_cards.setMinimumHeight(44)
        self.btn_generate_cards.clicked.connect(self._generate_cards_async)
        left_stack.addWidget(self.btn_generate_cards, 0)

        # --- Painel DIREITO ---
        self.table_panel = TablePanel()
        splitter.addWidget(self.table_panel)

        splitter.setSizes([620, 820])
        splitter.setCollapsible(0, False)

        self.cached_model_data = None
        
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

        self.settings = QSettings("Projeto ComSoc", "MainApp")
        last_output = self.settings.value("last_output_dir", "")
        if last_output:
            self.txt_output_path.setText(str(last_output))

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
        
        old_dir = Path("models") / old_slug
        new_dir = Path("models") / new_slug

        if new_dir.exists():
            QMessageBox.warning(self, "Erro", f"Já existe um modelo com o slug '{new_slug}'.")
            return

        try:
            old_dir.rename(new_dir)
            
            json_path = new_dir / "template_v3.json"
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                data["name"] = new_name
                
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            
            self.log_panel.append(f"Modelo renomeado: '{old_name}' -> '{new_name}'")
            self._reload_models_from_disk(select_name=new_name)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao renomear: {e}")

    def _on_duplicate_model(self):
        original_name = self.preview_panel.cbo_models.currentText()
        
        if not original_name:
            QMessageBox.warning(self, "Atenção", "Selecione um modelo para duplicar.")
            return

        original_slug = slugify_model_name(original_name)
        original_dir = Path("models") / original_slug

        if not original_dir.exists():
            self.log_panel.append("ERRO: Pasta do modelo original não encontrada.")
            return

        counter = 1
        while True:
            suffix = " (Cópia)" if counter == 1 else f" (Cópia {counter})"
            new_name = f"{original_name}{suffix}"
            new_slug = slugify_model_name(new_name)
            new_dir = Path("models") / new_slug
            
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

    def _open_naming_dialog(self):
        current_model_name = self.preview_panel.cbo_models.currentText()
        if not current_model_name:
            QMessageBox.warning(self, "Atenção", "Selecione um modelo primeiro.")
            return
            
        self.active_model_name = current_model_name
        cols = self.table_panel.table.columnCount()
        vars_available = [self.table_panel.table.horizontalHeaderItem(c).text() for c in range(cols)]
        slug = slugify_model_name(self.active_model_name)
        
        current_imposition = None
        model_size = (1000, 1000) 

        if self.cached_model_data:
            sz = self.cached_model_data.get("canvas_size", {})
            model_size = (sz.get("w", 1000), sz.get("h", 1000))
            current_imposition = self.cached_model_data.get("imposition_settings") 

        dlg = NamingDialog(self, slug, vars_available, self.current_filename_suffix, 
                           model_size_px=model_size, 
                           current_imposition=current_imposition)
        
        if dlg.exec():
            new_suffix = dlg.get_pattern()
            new_imposition = dlg.get_imposition_settings() 
            self.current_filename_suffix = new_suffix
            
            json_path = Path("models") / slug / "template_v3.json"
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

    def _generate_cards_async(self):
        rows_plain, rows_rich = self._scrape_table_data()
        if not rows_plain:
            self.log_panel.append("AVISO: A tabela está vazia. Nada a gerar.")
            return

        current_name = self.preview_panel.cbo_models.currentText()
        if not current_name:
            self.log_panel.append("ERRO: Nenhum modelo selecionado.")
            return
            
        slug = slugify_model_name(current_name)
        template_path = Path("models") / slug / "template_v3.json"

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
        if custom_path:
            base_dir = Path(custom_path)
            self.settings.setValue("last_output_dir", custom_path)
        else:
            base_dir = Path("output") / slug

        timestamp = datetime.now().strftime("%y.%m.%d_%H.%M.%S")
        folder_name = f"Lote_{timestamp}"
        
        output_dir = base_dir / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_panel.append(f"📂 Salvando em: {folder_name}")

        self.btn_generate_cards.setEnabled(False)
        self.btn_generate_cards.setText("Gerando... (Aguarde)")
        self.progress_bar.setValue(0)
        self.log_panel.append(f"--- Iniciando lote de {len(rows_plain)} itens ---")

        if self.current_filename_suffix:
            full_pattern = f"{slug}_{self.current_filename_suffix}"
        else:
            full_pattern = slug

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
        self.manager.finished_process.connect(self._handle_printing_queue)
        
        self.manager.start()

    def _on_generation_finished(self):
        self.btn_generate_cards.setEnabled(True)
        self.btn_generate_cards.setText("Gerar Material")
        self.log_panel.append("=== Processo Finalizado ===")

    def _on_model_changed(self, name: str):
        self.preview_panel.set_preview_text(f"Prévia do modelo selecionado:\n{name}")
        self.log_panel.append(f"Modelo ativo: {name}")
        self.active_model_name = name
        self.current_filename_suffix = ""

        if not name: return

        slug = slugify_model_name(name)
        json_path = Path("models") / slug / "template_v3.json"

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

    def _on_editor_saved(self, model_name, placeholders):
        self.log_panel.append(f"Modelo '{model_name}' salvo. Atualizando lista...")
        self._reload_models_from_disk(select_name=model_name)
    
    def _update_table_columns(self, placeholders, signatures=None):
        self.table_panel.table.clearContents()
        self.table_panel.table.setRowCount(0)
        self.table_panel.table.setColumnCount(0)
        
        if not placeholders: return
        
        has_sig = bool(signatures)
        headers = []
        if has_sig:
            headers.append("✍️ Ass.")
        headers.extend(placeholders)
            
        self.table_panel.table.setColumnCount(len(headers))
        self.table_panel.table.setHorizontalHeaderLabels(headers)
        self.table_panel.table.setRowCount(1)

        if has_sig:
            from PySide6.QtWidgets import QTableWidgetItem
            self.table_panel.table.setColumnWidth(0, 50) # Coluna estreita para a checkbox
            default_state = True
            for sig in signatures:
                if not sig.get("visible", True):
                    default_state = False
                    break
            
            chk_item = QTableWidgetItem("")
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            chk_item.setCheckState(Qt.CheckState.Checked if default_state else Qt.CheckState.Unchecked)
            chk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Tentativa de alinhamento central
            self.table_panel.table.setItem(0, 0, chk_item)

    def _open_model_dialog(self):
        current_model_name = self.preview_panel.cbo_models.currentText()
        if not current_model_name:
            QMessageBox.warning(self, "Atenção", "Selecione um modelo na lista antes de configurar.")
            return
            
        self.active_model_name = current_model_name

        self.editor_window = EditorWindow(self)
        self.editor_window.modelSaved.connect(self._on_editor_saved)

        slug = slugify_model_name(current_model_name)
        json_path = Path("models") / slug / "template_v3.json"

        if json_path.exists():
            self.editor_window.load_from_json(str(json_path))
        
        self.editor_window.show()

    def _reload_models_from_disk(self, select_name: str | None = None):
        self.preview_panel.cbo_models.blockSignals(True)
        self.preview_panel.cbo_models.clear()

        models_dir = Path("models")
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

    def _on_remove_model(self):
        model_name = (self.preview_panel.cbo_models.currentText() or "").strip()
        if not model_name: return

        slug = slugify_model_name(model_name)
        model_dir = Path("models") / slug

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

    def _get_row_data_rich(self, row_idx):
        table = self.table_panel.table
        cols = table.columnCount()
        headers = [table.horizontalHeaderItem(c).text() for c in range(cols)]
        
        row_data = {}
        for c in range(cols):
            key = headers[c]
            item = table.item(row_idx, c)
            
            if key == "✍️ Ass.":
                row_data["__use_signature__"] = (item.checkState() == Qt.CheckState.Checked) if item else True
                continue
                
            val = ""
            if item:
                val = item.data(Qt.ItemDataRole.UserRole)
                if not val: val = item.text()
            row_data[key] = val
        return row_data

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
    
    def _scrape_table_data(self):
        table = self.table_panel.table
        rows = table.rowCount()
        cols = table.columnCount()
        headers = [table.horizontalHeaderItem(c).text() for c in range(cols)]
        data_plain, data_rich = [], []

        for r in range(rows):
            row_p, row_r = {}, {}
            is_empty = True
            for c in range(cols):
                key = headers[c]
                item = table.item(r, c)
                
                if key == "✍️ Ass.":
                    use_sig = (item.checkState() == Qt.CheckState.Checked) if item else True
                    row_p["__use_signature__"] = use_sig
                    row_r["__use_signature__"] = use_sig
                    continue

                val_plain = item.text().strip() if item else ""
                val_rich = item.data(Qt.ItemDataRole.UserRole) if item else ""
                if not val_rich: val_rich = val_plain
                
                if val_plain: is_empty = False
                row_p[key] = val_plain
                row_r[key] = val_rich

            if not is_empty:
                data_plain.append(row_p)
                data_rich.append(row_r)
        return data_plain, data_rich
    
    def _toggle_single_pdf_option(self, fmt):
        """Gerencia a visibilidade do checkbox de PDF único."""
        is_pdf = (fmt == "PDF")
        self.chk_single_pdf.setVisible(is_pdf)
        if not is_pdf:
            self.chk_single_pdf.setChecked(False)

    def _save_export_format_pref(self, fmt):
        """Salva a escolha do formato (PNG/PDF) no JSON do modelo."""
        self._update_template_json({"last_export_format": fmt})

    def _save_single_pdf_pref(self, checked):
        """Salva o estado da checkbox de Arquivo Único no JSON do modelo."""
        self._update_template_json({"last_single_pdf": checked})

    def _update_template_json(self, new_data: dict):
        """Método auxiliar para atualizar metadados no template_v3.json."""
        if not self.active_model_name:
            return
        slug = slugify_model_name(self.active_model_name)
        json_path = Path("models") / slug / "template_v3.json"
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
    
    def _select_output_folder(self):
        start_dir = self.txt_output_path.text() or ""
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Saída", start_dir)
        if folder:
            self.txt_output_path.setText(folder)
            self.settings.setValue("last_output_dir", folder)

    def _handle_printing_queue(self):
        if not self.cached_model_data: return
        
        imp_settings = self.cached_model_data.get("imposition_settings", {})
        should_print = imp_settings.get("print_after_generation", False)
        
        if not should_print:
            return

        files_to_print = getattr(self.manager, "generated_files", [])
        if not files_to_print:
            self.log_panel.append("⚠️ Nenhum arquivo gerado para impressão.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        if files_to_print:
            first_img_path = self.manager.output_dir / files_to_print[0]
            if first_img_path.exists():
                img_check = QImage(str(first_img_path))
                if not img_check.isNull():
                    if img_check.width() > img_check.height():
                        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
                    else:
                        printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        printer.setFullPage(True)
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            self.log_panel.append("🖨️ Impressão cancelada pelo usuário.")
            return

        self.log_panel.append(f"🖨️ Enviando {len(files_to_print)} páginas para a impressora...")
        
        painter = QPainter()
        if not painter.begin(printer):
            self.log_panel.append("❌ Erro ao iniciar comunicação com a impressora.")
            return

        try:
            output_dir = self.manager.output_dir
            for i, filename in enumerate(files_to_print):
                if i > 0:
                    printer.newPage()
                
                full_path = output_dir / filename
                if not full_path.exists():
                    continue
                
                img = QImage(str(full_path))
                if img.isNull():
                    continue

                paper_rect = printer.paperRect(QPrinter.Unit.DevicePixel)
                painter.drawImage(paper_rect, img)
                
            self.log_panel.append("✅ Envio para impressão concluído!")
            
        except Exception as e:
            self.log_panel.append(f"❌ Erro durante impressão: {e}")
        finally:
            painter.end()