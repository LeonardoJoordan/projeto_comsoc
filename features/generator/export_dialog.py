from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QFrame, QGridLayout, 
                               QDialogButtonBox, QCheckBox, QGroupBox, QDoubleSpinBox,
                               QWidget, QRadioButton, QButtonGroup, QTabWidget,
                               QComboBox, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt
from .imposition import SheetAssembler

class ConfigDialog(QDialog):
    def __init__(self, parent, model_slug: str, available_vars: list[str], 
                 current_pattern: str = "", model_size_px: tuple[int, int] = (1000, 1000),
                 model_print_size_mm: tuple[float, float] = None,
                 current_imposition: dict = None, is_dark: bool = True):
        super().__init__(parent)
        self.setWindowTitle("Configurações Gerais")
        self.resize(550, 450)
        
        self.model_slug = model_slug
        self.result_pattern = current_pattern
        self.model_w, self.model_h = model_size_px
        fallback_w_mm = (self.model_w / 300.0) * 25.4
        fallback_h_mm = (self.model_h / 300.0) * 25.4
        if model_print_size_mm and model_print_size_mm[0] > 0 and model_print_size_mm[1] > 0:
            self.model_print_w_mm, self.model_print_h_mm = model_print_size_mm
        else:
            self.model_print_w_mm, self.model_print_h_mm = fallback_w_mm, fallback_h_mm
        self.ratio = self.model_print_w_mm / self.model_print_h_mm if self.model_print_h_mm > 0 else 1.0
        
        self.imposition_settings = current_imposition or {
            "enabled": False, "sheet_w_mm": 210.0, "sheet_h_mm": 297.0,
            "crop_marks": True, "bleed_margin": True, "target_w_mm": 0, "target_h_mm": 0,
            "presets": {}, "active_preset_name": ""
        }
        self._original_enabled = self.imposition_settings.get("enabled", False)
        self.presets = self.imposition_settings.get("presets", {}) or {}
        self.active_preset_name = self.imposition_settings.get("active_preset_name", "") or self.SYSTEM_PRESET_NAME
        if self.active_preset_name not in self.presets:
            self.active_preset_name = self.SYSTEM_PRESET_NAME
        initial_print = self._settings_for_active_preset()
        self.current_is_dark = is_dark

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- ABA 1: Nomenclatura ---
        tab_naming = QWidget()
        ly_naming = QVBoxLayout(tab_naming)
        ly_naming.setSpacing(15)
        ly_naming.setContentsMargins(15, 15, 15, 15)
        
        lbl_patern_title = QLabel("<b>Padrão de Nomenclatura:</b>")
        lbl_patern_title.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        lbl_patern_title.setToolTip(
            "<b>PADRÃO DE NOME</b><br><br>"
            "Define como cada ficheiro gerado será batizado automaticamente pelo sistema.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Utilize as tags (ex: {Nome}) para que cada ficheiro saia com o nome do destinatário, facilitando a identificação e entrega do material.</small>"
        )
        ly_naming.addWidget(lbl_patern_title)
        ly_preview = QHBoxLayout()
        
        self.txt_pattern = QLineEdit()
        self.txt_pattern.setPlaceholderText("Ex: {modelo}_{nome}")
        self.txt_pattern.setText(current_pattern)
        self.txt_pattern.setMinimumHeight(34)
        
        lbl_ext = QLabel(".png")
        lbl_ext.setStyleSheet("font-size: 14px; opacity: 0.7;") 

        ly_preview.addWidget(self.txt_pattern)
        ly_preview.addWidget(lbl_ext)
        ly_naming.addLayout(ly_preview)

        lbl_vars_title = QLabel("Variáveis disponíveis:")
        lbl_vars_title.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        lbl_vars_title.setToolTip(
            "<b>VARIÁVEIS DINÂMICAS</b><br><br>"
            "Estes são os campos detetados no seu modelo. Ao clicar neles, a 'tag' é inserida no nome do ficheiro.<br><br>"
            "<b>Exemplo:</b> Se definir como <i>Cartão de {Nome}</i>, o sistema gerará:<br>"
            "• Cartão de Leonardo.pdf<br>"
            "• Cartão de Lilia.pdf<br><br>"
            "<small style='color: #A0A0A0;'>O sistema utiliza o dado exato que estiver preenchido na tabela para cada linha.</small>"
        )
        ly_naming.addWidget(lbl_vars_title)
        grid_vars = QGridLayout()
        col, row = 0, 0
        if not available_vars:
            ly_naming.addWidget(QLabel("<i>(Nenhuma coluna encontrada)</i>"))
        else:
            for var in available_vars:
                btn = QPushButton(f"{{{var}}}")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setMinimumHeight(30)
                btn.setToolTip(
                    "<b>INSERIR VARIÁVEL</b><br><br>"
                    "Clique para adicionar esta tag ao padrão de nome. Durante a geração, o sistema substituirá o texto entre chaves pelo dado real da tabela."
                )
                btn.clicked.connect(lambda checked, v=var: self._insert_variable(v))
                grid_vars.addWidget(btn, row, col)
                col += 1
                if col > 3: col, row = 0, row + 1
            ly_naming.addLayout(grid_vars)
        ly_naming.addStretch()
        self.tabs.addTab(tab_naming, "Nomenclatura")

        # Banner de Aviso para Hiperlinks
        self.lbl_link_warning = QLabel("⚠️ Hiperlinks ativos detetados. Use PDF (Arquivo Individual) para os manter.")
        self.lbl_link_warning.setStyleSheet("color: #e67e22; font-weight: bold; padding: 5px; border: 1px solid #e67e22; border-radius: 4px;")
        self.lbl_link_warning.setVisible(False)
        ly_naming.insertWidget(0, self.lbl_link_warning)

        # --- ABA 2: Impressão e Imposição ---
        tab_print = QWidget()
        ly_print = QVBoxLayout(tab_print)
        ly_print.setSpacing(10)

        # --- PRESETS UI (No topo da aba de Impressão) ---
        ly_presets_v = QVBoxLayout()
        ly_combo_row = QHBoxLayout()
        self.cmb_presets = QComboBox()
        self.cmb_presets.currentIndexChanged.connect(self._on_preset_selected)
        lbl_preset = QLabel("<b>Predefinição:</b>")
        lbl_preset.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        lbl_preset.setToolTip(
            "<b>PREDEFINIÇÃO DE LAYOUT</b><br><br>"
            "Atalho para carregar e salvar conjuntos completos de configurações de impressão:<br>"
            "• <b>Salvar Novo:</b> Cria uma predefinição com as configurações atuais da tela.<br>"
            "• <b>Atualizar:</b> Sobrescreve a predefinição selecionada com as configurações atuais.<br>"
            "• <b>Apagar:</b> Remove permanentemente a predefinição selecionada.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Configure folha, imposição e marcas de corte como desejar e clique em <b>Salvar Novo</b> para guardar o conjunto. Ele ficará disponível como atalho na tela principal do programa.</small>")
        ly_combo_row.addWidget(lbl_preset)
        self.cmb_presets.setToolTip(
            "<b>PREDEFINIÇÃO DE LAYOUT</b><br><br>"
            "Atalho para carregar e salvar conjuntos completos de configurações de impressão:<br>"
            "• <b>Salvar Novo:</b> Cria uma predefinição com as configurações atuais da tela.<br>"
            "• <b>Atualizar:</b> Sobrescreve a predefinição selecionada com as configurações atuais.<br>"
            "• <b>Apagar:</b> Remove permanentemente a predefinição selecionada.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Configure folha, imposição e marcas de corte como desejar e clique em <b>Salvar Novo</b> para guardar o conjunto. Ele ficará disponível como atalho na tela principal do programa.</small>")
        ly_combo_row.addWidget(self.cmb_presets, 1)
        
        ly_buttons_row = QHBoxLayout()
        self.btn_new_preset = QPushButton("Criar Nova Predefinição")
        self.btn_new_preset.clicked.connect(self._save_new_preset)
        self.btn_rename_preset = QPushButton("Renomear")
        self.btn_rename_preset.clicked.connect(self._rename_preset)
        self.btn_del_preset = QPushButton("Excluir")
        self.btn_del_preset.clicked.connect(self._delete_preset)
        
        ly_buttons_row.addWidget(self.btn_new_preset)
        ly_buttons_row.addStretch()
        ly_buttons_row.addWidget(self.btn_rename_preset)
        ly_buttons_row.addWidget(self.btn_del_preset)
        
        ly_presets_v.addLayout(ly_combo_row)
        ly_presets_v.addLayout(ly_buttons_row)
        ly_print.addLayout(ly_presets_v)
        ly_print.addSpacing(10) # Respiro visual
        
        self.chk_imposition = QCheckBox("Habilitar múltiplos itens por página")
        self.chk_imposition.setChecked(initial_print["enabled"])
        self.chk_imposition.setToolTip(
            "<b>MÚLTIPLOS ITENS POR PÁGINA (AGRUPAMENTO)</b><br><br>"
            "Organiza automaticamente vários exemplares do seu modelo dentro da mesma folha de saída.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Além de economizar papel, este recurso otimiza o corte manual. Os itens são alinhados para que você possa usar régua e estilete e destacar vários cartões com poucos cortes retos, sem rebarbas.</small>"
        )
        self.chk_imposition.toggled.connect(self._toggle_imposition_ui)
        ly_print.addWidget(self.chk_imposition)

        # Label de aviso dinâmico (abaixo do checkbox)
        self.lbl_imposition_hint = QLabel()
        self.lbl_imposition_hint.setWordWrap(True)
        self.lbl_imposition_hint.setStyleSheet("color: gray; font-style: italic; padding-left: 4px;")
        ly_print.addWidget(self.lbl_imposition_hint)

        self.container_imposition = QWidget()
        self.container_imposition.setVisible(self.chk_imposition.isChecked())
        ly_imp = QVBoxLayout(self.container_imposition)
        ly_imp.setContentsMargins(10, 0, 0, 0)

        # Folha de Saída agora está dentro do container de imposição
        lbl_sheet_title = QLabel("Folha de saída (Largura x Altura):")
        lbl_sheet_title.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        lbl_sheet_title.setToolTip(
            "<b>FOLHA DE SAÍDA (DOCUMENTO FINAL)</b><br><br>"
            "Define o tamanho real do papel que será colocado na impressora (ex: A4, A3 ou formatos personalizados).<br><br>"
            "<small style='color: #A0A0A0;'>Importante: Esta configuração dita a área útil de trabalho. Uma folha maior (A3) permite agrupar muito mais exemplares no mesmo documento do que uma folha A4.</small>"
        )
        ly_imp.addWidget(lbl_sheet_title)
        ly_sheet = QHBoxLayout()
        self.spin_sheet_w_mm = QDoubleSpinBox()
        self.spin_sheet_w_mm.setRange(50, 2000)
        self.spin_sheet_w_mm.setSuffix(" mm")
        self.spin_sheet_w_mm.setDecimals(2)
        self.spin_sheet_w_mm.setValue(initial_print["sheet_w"])
        self.spin_sheet_h_mm = QDoubleSpinBox()
        self.spin_sheet_h_mm.setRange(50, 2000)
        self.spin_sheet_h_mm.setSuffix(" mm")
        self.spin_sheet_h_mm.setDecimals(2)
        self.spin_sheet_h_mm.setValue(initial_print["sheet_h"])
        ly_sheet.addWidget(self.spin_sheet_w_mm)
        ly_sheet.addWidget(QLabel("x"))
        ly_sheet.addWidget(self.spin_sheet_h_mm)
        ly_sheet.addStretch()
        ly_imp.addLayout(ly_sheet)

        ly_imp.addSpacing(6)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        ly_imp.addWidget(sep)
        
        lbl_model_dims_title = QLabel("Dimensões do modelo na folha (Largura x Altura):")
        lbl_model_dims_title.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        lbl_model_dims_title.setToolTip(
            "<b>DIMENSÕES REAIS DO MODELO</b><br><br>"
            "Define o tamanho exato (em milímetros) que o seu cartão/documento terá impresso na folha.<br><br>"
            "<small style='color: #A0A0A0;'>Dica Smart: Essencial para materiais que precisam encaixar em suportes físicos, como displays de acrílico, crachás ou etiquetas. Meça o suporte com uma régua e digite os valores exatos aqui para um ajuste milimétrico.</small>"
        )
        ly_imp.addWidget(lbl_model_dims_title)
        self.spin_w_mm = QDoubleSpinBox()
        self.spin_w_mm.setRange(10, 2000)
        self.spin_w_mm.setSuffix(" mm")
        self.spin_w_mm.setDecimals(2)

        self.spin_h_mm = QDoubleSpinBox()
        self.spin_h_mm.setRange(10, 2000)
        self.spin_h_mm.setSuffix(" mm")
        self.spin_h_mm.setDecimals(2)

        self.spin_w_mm.setValue(initial_print["w"])
        self.spin_h_mm.setValue(initial_print["h"])

        self.spin_w_mm.valueChanged.connect(self._on_width_changed)
        self.spin_h_mm.valueChanged.connect(self._on_height_changed)

        ly_model_dims = QHBoxLayout()
        ly_model_dims.addWidget(self.spin_w_mm)
        ly_model_dims.addWidget(QLabel("x"))
        ly_model_dims.addWidget(self.spin_h_mm)
        ly_model_dims.addStretch()
        ly_imp.addLayout(ly_model_dims)

        self.lbl_capacity = QLabel("Calculando capacidade...")
        self.lbl_capacity.setStyleSheet("font-weight: bold; color: #2ecc71;")
        ly_imp.addWidget(self.lbl_capacity)

        self.chk_crop_marks = QCheckBox("Habilitar marcas de corte")
        self.chk_crop_marks.setChecked(initial_print["crop"])
        self.chk_crop_marks.setToolTip(
            "<b>MARCAS DE CORTE</b><br><br>"
            "Adiciona pequenas guias visuais nos cantos de cada item na folha impressa.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Estas marcas indicam o caminho exato para a lâmina do estilete ou da guilhotina, garantindo um acabamento profissional e uniforme em todo o lote.</small>"
        )
        ly_imp.addWidget(self.chk_crop_marks)
        self.chk_bleed = QCheckBox("Habilitar margem de sangria")
        self.chk_bleed.setChecked(initial_print["bleed"])
        self.chk_bleed.setToolTip(
            "<b>MARGEM DE SANGRIA</b><br><br>"
            "Reserva um espaço extra (5mm) ao redor dos itens na folha.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Ative para garantir que artes com fundo contínuo não criem filetes brancos durante o corte manual.</small>"
        )
        ly_imp.addWidget(self.chk_bleed)
        
        # Carrega a UI com os dados em memória
        self._load_presets_ui()
        
        ly_print.addWidget(self.container_imposition)
        ly_print.addStretch()
        self.tabs.addTab(tab_print, "Impressão")

        # --- ABA 3: Tema do Sistema ---
        tab_theme = QWidget()
        ly_theme = QVBoxLayout(tab_theme)
        ly_theme.setSpacing(10)
        
        lbl_theme_title = QLabel("<b>Preferências do Sistema (Global)</b>")
        lbl_theme_title.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        lbl_theme_title.setToolTip(
            "<b>PREFERÊNCIA VISUAL</b><br><br>"
            "Alterna a aparência de todo o software entre o Modo Claro e o Modo Escuro.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: O Modo Escuro (Mint-Y) é ideal para reduzir o cansaço visual durante longas jornadas de trabalho.</small>"
        )
        ly_theme.addWidget(lbl_theme_title)
        self.radio_light = QRadioButton("☀️ Tema Claro")
        self.radio_dark = QRadioButton("🌙 Tema Escuro")

        
        self.theme_group = QButtonGroup(self)
        self.theme_group.addButton(self.radio_light)
        self.theme_group.addButton(self.radio_dark)
        
        if self.current_is_dark: self.radio_dark.setChecked(True)
        else: self.radio_light.setChecked(True)
            
        ly_theme.addWidget(self.radio_dark)
        ly_theme.addWidget(self.radio_light)
        ly_theme.addStretch()
        self.tabs.addTab(tab_theme, "Tema do Sistema")

        # Conexões de Cálculo
        self.spin_sheet_w_mm.valueChanged.connect(self._update_capacity_preview)
        self.spin_sheet_h_mm.valueChanged.connect(self._update_capacity_preview)
        self.spin_w_mm.valueChanged.connect(self._update_capacity_preview)
        self.spin_h_mm.valueChanged.connect(self._update_capacity_preview)
        self.chk_crop_marks.toggled.connect(self._update_capacity_preview)
        self.chk_bleed.toggled.connect(self._update_capacity_preview)
        self.chk_imposition.toggled.connect(self._update_capacity_preview)

        # Botões
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)
        main_layout.addWidget(self.buttonBox)

        self._toggle_imposition_ui(self.chk_imposition.isChecked())
        self._update_capacity_preview()
    def get_pattern(self):
        return self.result_pattern
    
    def get_imposition_settings(self):
        return {
            "enabled": self.chk_imposition.isChecked(),
            "sheet_w_mm": self.spin_sheet_w_mm.value(),
            "sheet_h_mm": self.spin_sheet_h_mm.value(),
            "crop_marks": self.chk_crop_marks.isChecked(),
            "bleed_margin": self.chk_bleed.isChecked(),
            "target_w_mm": self.spin_w_mm.value(),
            "target_h_mm": self.spin_h_mm.value(),
            "presets": self.presets,
            "active_preset_name": self.active_preset_name
        }

    def _settings_for_active_preset(self):
        """Retorna os valores iniciais da UI sem contaminar a definição do modelo."""
        base = {
            "enabled": False,
            "sheet_w": 210.0,
            "sheet_h": 297.0,
            "w": self.model_print_w_mm,
            "h": self.model_print_h_mm,
            "crop": True,
            "bleed": True,
        }

        if self.active_preset_name == self.SYSTEM_PRESET_NAME:
            return base

        preset = self.presets.get(self.active_preset_name)
        if not preset:
            self.active_preset_name = self.SYSTEM_PRESET_NAME
            return base

        return {
            "enabled": preset.get("enabled", False),
            "sheet_w": preset.get("sheet_w", base["sheet_w"]),
            "sheet_h": preset.get("sheet_h", base["sheet_h"]),
            "w": preset.get("w", base["w"]) or base["w"],
            "h": preset.get("h", base["h"]) or base["h"],
            "crop": preset.get("crop", True),
            "bleed": preset.get("bleed", True),
        }

    def _set_model_print_size_controls(self):
        self.spin_w_mm.blockSignals(True)
        self.spin_h_mm.blockSignals(True)
        self.spin_w_mm.setValue(self.model_print_w_mm)
        self.spin_h_mm.setValue(self.model_print_h_mm)
        self.spin_w_mm.blockSignals(False)
        self.spin_h_mm.blockSignals(False)

    def _update_capacity_preview(self):
        """Calcula dinamicamente quantos itens cabem e valida se o modelo cabe na folha."""
        if not self.chk_imposition.isChecked():
            self.lbl_capacity.setText("Imposição desativada (1 item por arquivo)")
            self.lbl_capacity.setStyleSheet("color: gray;")
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            return

        sw = self.spin_sheet_w_mm.value()
        sh = self.spin_sheet_h_mm.value()
        tw = self.spin_w_mm.value()
        th = self.spin_h_mm.value()
        marks = self.chk_crop_marks.isChecked()
        bleed = self.chk_bleed.isChecked()

        # Instancia o assembler (o mesmo motor que gera as imagens)
        assembler = SheetAssembler(tw, th, sw, sh, marks, bleed)
        
        ok_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)

        if assembler.capacity > 0:
            self.lbl_capacity.setText(f"✅ Capacidade: {assembler.capacity} itens por página ({assembler.cols}x{assembler.rows})")
            self.lbl_capacity.setStyleSheet("font-weight: bold; color: #2ecc71;")
            ok_button.setEnabled(True)
        else:
            self.lbl_capacity.setText("❌ Modelo muito grande para a página!")
            self.lbl_capacity.setStyleSheet("font-weight: bold; color: #e74c3c;")
            ok_button.setEnabled(False)

    def _on_accept(self):
        # Auto-save inteligente das configurações
        if self.active_preset_name == self.SYSTEM_PRESET_NAME:
            # Se ativou imposição no preset de sistema, assumimos que algo foi customizado
            if self.chk_imposition.isChecked():
                name, ok = QInputDialog.getText(self, "Configurações Personalizadas", "Você alterou as configurações padrão.\nDê um nome para salvar esta predefinição:", QLineEdit.EchoMode.Normal, "Personalizada")
                
                # Se o usuário cancelar ou deixar em branco, aplica o nome padrão de fallback
                new_name = name.strip() if (ok and name.strip()) else "Personalizada"
                if new_name == self.SYSTEM_PRESET_NAME:
                    new_name = "Personalizada"
                
                # Previne colisão silenciosa caso a pessoa apenas feche a janela ou confirme o padrão
                final_name = new_name
                counter = 2
                while final_name in self.presets:
                    final_name = f"{new_name} {counter}"
                    counter += 1
                    
                self.presets[final_name] = self._get_current_settings()
                self.active_preset_name = final_name
        else:
            # Se já está em um preset do usuário, salva silenciosamente (auto-save fluido)
            self.presets[self.active_preset_name] = self._get_current_settings()

        self.result_pattern = self.txt_pattern.text().strip()
        self.accept()

    SYSTEM_PRESET_NAME = "Definição do Modelo"

    def _load_presets_ui(self):
        self.cmb_presets.blockSignals(True)
        self.cmb_presets.clear()
        
        self.cmb_presets.addItem(self.SYSTEM_PRESET_NAME)

        user_presets = sorted(k for k in self.presets.keys() if k != self.SYSTEM_PRESET_NAME)
        for name in user_presets:
            self.cmb_presets.addItem(name)

        if self.active_preset_name and self.active_preset_name in self.presets:
            idx = self.cmb_presets.findText(self.active_preset_name)
            if idx >= 0:
                self.cmb_presets.setCurrentIndex(idx)
            else:
                self.cmb_presets.setCurrentIndex(0)
                self.active_preset_name = self.SYSTEM_PRESET_NAME
        else:
            self.cmb_presets.setCurrentIndex(0)
            self.active_preset_name = self.SYSTEM_PRESET_NAME

        is_system = (self.active_preset_name == self.SYSTEM_PRESET_NAME)
        self.btn_rename_preset.setEnabled(not is_system)
        self.btn_del_preset.setEnabled(not is_system)

        self.cmb_presets.blockSignals(False)

    def _on_preset_selected(self, index):
        if index < 0: return
        name = self.cmb_presets.itemText(index)

        if name == self.SYSTEM_PRESET_NAME:
            self.chk_imposition.setChecked(False)
            self.spin_sheet_w_mm.setValue(210.0)
            self.spin_sheet_h_mm.setValue(297.0)
            self._set_model_print_size_controls()
            self.chk_crop_marks.setChecked(True)
            self.chk_bleed.setChecked(True)
            self.active_preset_name = self.SYSTEM_PRESET_NAME
            self.btn_rename_preset.setEnabled(False)
            self.btn_del_preset.setEnabled(False)
        else:
            data = self.presets.get(name)
            if not data: return
            
            self.spin_sheet_w_mm.setValue(data.get("sheet_w", 210.0))
            self.spin_sheet_h_mm.setValue(data.get("sheet_h", 297.0))
            self.chk_imposition.setChecked(data.get("enabled", False))
            self.spin_w_mm.setValue(data.get("w", 0))
            self.spin_h_mm.setValue(data.get("h", 0))
            self.chk_crop_marks.setChecked(data.get("crop", True))
            self.chk_bleed.setChecked(data.get("bleed", True))
            
            self.active_preset_name = name
            self.btn_rename_preset.setEnabled(True)
            self.btn_del_preset.setEnabled(True)

    def _get_current_settings(self):
        """Coleta as configurações atuais da tela."""
        return {
            "sheet_w": self.spin_sheet_w_mm.value(),
            "sheet_h": self.spin_sheet_h_mm.value(),
            "enabled": self.chk_imposition.isChecked(),
            "w": self.spin_w_mm.value(),
            "h": self.spin_h_mm.value(),
            "crop": self.chk_crop_marks.isChecked(),
            "bleed": self.chk_bleed.isChecked()
        }

    def _save_new_preset(self, default_name=""):
        # Se chamado pelo clique do botão, default_name será um booleano (checked state)
        if isinstance(default_name, bool):
            default_name = ""
            
        name, ok = QInputDialog.getText(self, "Nova Predefinição", "Nome da predefinição:", QLineEdit.EchoMode.Normal, default_name)
        if ok and name.strip():
            name = name.strip()
            if name == self.SYSTEM_PRESET_NAME:
                QMessageBox.warning(self, "Nome reservado", f"O nome '{self.SYSTEM_PRESET_NAME}' é reservado pelo sistema.")
                return False
            
            if name in self.presets:
                reply = QMessageBox.question(self, "Sobrescrever", f"A predefinição '{name}' já existe. Deseja sobrescrevê-la?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return self._save_new_preset(name) # Repete o prompt para o usuário tentar outro nome
                    
            self.presets[name] = self._get_current_settings()
            self.active_preset_name = name
            self._load_presets_ui()
            return True
        return False

    def _delete_preset(self):
        if not self.active_preset_name or self.active_preset_name == self.SYSTEM_PRESET_NAME: return
        
        reply = QMessageBox.question(self, "Excluir Predefinição", f"Tem certeza que deseja excluir '{self.active_preset_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.presets[self.active_preset_name]
            self.active_preset_name = self.SYSTEM_PRESET_NAME
            self._load_presets_ui()

    def _rename_preset(self):
        if not self.active_preset_name or self.active_preset_name == self.SYSTEM_PRESET_NAME: return

        new_name, ok = QInputDialog.getText(self, "Renomear Predefinição", "Novo nome:", QLineEdit.EchoMode.Normal, self.active_preset_name)
        if ok and new_name.strip():
            new_name = new_name.strip()
            if new_name == self.active_preset_name: return
            if new_name == self.SYSTEM_PRESET_NAME:
                QMessageBox.warning(self, "Nome reservado", f"O nome '{self.SYSTEM_PRESET_NAME}' é reservado pelo sistema.")
                return
            if new_name in self.presets:
                QMessageBox.warning(self, "Nome já existe", f"Já existe uma predefinição com o nome '{new_name}'.")
                return

            self.presets[new_name] = self.presets.pop(self.active_preset_name)
            self.active_preset_name = new_name
            self._load_presets_ui()

    def _toggle_imposition_ui(self, enabled):
        self.container_imposition.setVisible(enabled)
        if enabled:
            if self.active_preset_name == self.SYSTEM_PRESET_NAME:
                self._set_model_print_size_controls()
            self.lbl_imposition_hint.setText("⚙️ Configure a folha e as dimensões do modelo para um resultado preciso.")
            self.lbl_imposition_hint.setStyleSheet("color: #e67e22; font-style: italic; padding-left: 4px;")
        else:
            self.lbl_imposition_hint.setText("ℹ️ O arquivo gerado terá as dimensões exatas do modelo original (1 item por arquivo).")
            self.lbl_imposition_hint.setStyleSheet("color: gray; font-style: italic; padding-left: 4px;")

    def _insert_variable(self, var_name):
        self.txt_pattern.insert(f"{{{var_name}}}")
        self.txt_pattern.setFocus()

    def _on_width_changed(self, new_w):
        self.spin_h_mm.blockSignals(True)
        self.spin_h_mm.setValue(new_w / self.ratio)
        self.spin_h_mm.blockSignals(False)

    def _on_height_changed(self, new_h):
        self.spin_w_mm.blockSignals(True)
        self.spin_w_mm.setValue(new_h * self.ratio)
        self.spin_w_mm.blockSignals(False)

    def set_link_warning_visible(self, visible):
        self.lbl_link_warning.setVisible(visible)
    
    
