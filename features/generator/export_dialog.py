from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QFrame, QGridLayout, 
                               QDialogButtonBox, QCheckBox, QGroupBox, QDoubleSpinBox,
                               QWidget, QRadioButton, QButtonGroup, QTabWidget)
from PySide6.QtCore import Qt
from .imposition import SheetAssembler

class ConfigDialog(QDialog):
    def __init__(self, parent, model_slug: str, available_vars: list[str], 
                 current_pattern: str = "", model_size_px: tuple[int, int] = (1000, 1000),
                 current_imposition: dict = None, is_dark: bool = True):
        super().__init__(parent)
        self.setWindowTitle("Configurações Gerais")
        self.resize(550, 450)
        
        self.model_slug = model_slug
        self.result_pattern = current_pattern
        self.model_w, self.model_h = model_size_px
        self.ratio = self.model_w / self.model_h if self.model_h > 0 else 1.0
        
        self.imposition_settings = current_imposition or {
            "enabled": False, "sheet_w_mm": 210.0, "sheet_h_mm": 297.0,
            "crop_marks": True, "bleed_margin": True, "target_w_mm": 0, "target_h_mm": 0
        }
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
        
        lbl_sheet_title = QLabel("<b>Folha de saída (Largura x Altura):</b>")
        lbl_sheet_title.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        lbl_sheet_title.setToolTip(
            "<b>FOLHA DE SAÍDA (DOCUMENTO FINAL)</b><br><br>"
            "Define o tamanho real do papel que será colocado na impressora (ex: A4, A3 ou formatos personalizados).<br><br>"
            "<small style='color: #A0A0A0;'>Importante: Esta configuração dita a área útil de trabalho. Uma folha maior (A3) permite agrupar muito mais exemplares no mesmo documento do que uma folha A4.</small>"
        )
        ly_print.addWidget(lbl_sheet_title)
        ly_sheet = QHBoxLayout()
        self.spin_sheet_w_mm = QDoubleSpinBox()
        self.spin_sheet_w_mm.setRange(50, 2000)
        self.spin_sheet_w_mm.setSuffix(" mm")
        self.spin_sheet_w_mm.setDecimals(1)
        self.spin_sheet_w_mm.setValue(self.imposition_settings.get("sheet_w_mm", 210.0))
        
        self.spin_sheet_h_mm = QDoubleSpinBox()
        self.spin_sheet_h_mm.setRange(50, 2000)
        self.spin_sheet_h_mm.setSuffix(" mm")
        self.spin_sheet_h_mm.setDecimals(1)
        self.spin_sheet_h_mm.setValue(self.imposition_settings.get("sheet_h_mm", 297.0))
        
        ly_sheet.addWidget(self.spin_sheet_w_mm)
        ly_sheet.addWidget(QLabel("x"))
        ly_sheet.addWidget(self.spin_sheet_h_mm)
        ly_sheet.addStretch()
        ly_print.addLayout(ly_sheet)

        self.chk_imposition = QCheckBox("Habilitar múltiplos itens por página")
        self.chk_imposition.setChecked(self.imposition_settings.get("enabled", False))
        self.chk_imposition.setToolTip(
            "<b>MÚLTIPLOS ITENS POR PÁGINA (AGRUPAMENTO)</b><br><br>"
            "Organiza automaticamente vários exemplares do seu modelo dentro da mesma folha de saída.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Além de economizar papel, este recurso otimiza o corte manual. Os itens são alinhados para que você possa usar régua e estilete e destacar vários cartões com poucos cortes retos, sem rebarbas.</small>"
        )
        self.chk_imposition.toggled.connect(self._toggle_imposition_ui)
        ly_print.addWidget(self.chk_imposition)

        self.container_imposition = QWidget()
        self.container_imposition.setVisible(self.chk_imposition.isChecked())
        ly_imp = QVBoxLayout(self.container_imposition)
        ly_imp.setContentsMargins(10, 0, 0, 0)
        
        lbl_model_dims_title = QLabel("Dimensões do modelo final (Largura x Altura):")
        lbl_model_dims_title.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        lbl_model_dims_title.setToolTip(
            "<b>DIMENSÕES REAIS DO MODELO</b><br><br>"
            "Define o tamanho exato (em milímetros) que o seu cartão/documento terá após ser impresso e cortado.<br><br>"
            "<small style='color: #A0A0A0;'>Dica Smart: Essencial para materiais que precisam encaixar em suportes físicos, como displays de acrílico, crachás ou etiquetas. Meça o suporte com uma régua e digite os valores exatos aqui para um ajuste milimétrico.</small>"
        )
        ly_imp.addWidget(lbl_model_dims_title)
        self.spin_w_mm = QDoubleSpinBox()
        self.spin_w_mm.setRange(10, 2000)
        self.spin_w_mm.setSuffix(" mm")
        self.spin_w_mm.setDecimals(1)

        self.spin_h_mm = QDoubleSpinBox()
        self.spin_h_mm.setRange(10, 2000)
        self.spin_h_mm.setSuffix(" mm")
        self.spin_h_mm.setDecimals(1)


        saved_w = self.imposition_settings.get("target_w_mm", 0)
        if saved_w > 0:
            self.spin_w_mm.setValue(saved_w)
            self.spin_h_mm.setValue(saved_w / self.ratio)
        else:
            # Calcula o tamanho físico real baseado nos pixels a 300 DPI
            default_w_mm = (self.model_w / 300.0) * 25.4
            default_h_mm = (self.model_h / 300.0) * 25.4
            self.spin_w_mm.setValue(default_w_mm)
            self.spin_h_mm.setValue(default_h_mm)

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
        self.chk_crop_marks.setChecked(self.imposition_settings.get("crop_marks", True))
        self.chk_crop_marks.setToolTip(
            "<b>MARCAS DE CORTE</b><br><br>"
            "Adiciona pequenas guias visuais nos cantos de cada item na folha impressa.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Estas marcas indicam o caminho exato para a lâmina do estilete ou da guilhotina, garantindo um acabamento profissional e uniforme em todo o lote.</small>"
        )
        ly_imp.addWidget(self.chk_crop_marks)
        self.chk_bleed = QCheckBox("Habilitar margem de sangria")
        self.chk_bleed.setChecked(self.imposition_settings.get("bleed_margin", True))
        self.chk_bleed.setToolTip(
            "<b>MARGEM DE SANGRIA</b><br><br>"
            "Reserva um espaço extra (5mm) ao redor dos itens na folha.<br><br>"
            "<small style='color: #A0A0A0;'>Dica: Ative para garantir que artes com fundo contínuo não criem filetes brancos durante o corte manual.</small>"
        )
        ly_imp.addWidget(self.chk_bleed)
        
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
            "target_h_mm": self.spin_h_mm.value()
        }

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
        self.result_pattern = self.txt_pattern.text().strip()
        self.accept()

    def _toggle_imposition_ui(self, enabled):
        self.container_imposition.setVisible(enabled)

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
    
    