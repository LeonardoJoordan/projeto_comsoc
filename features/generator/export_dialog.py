from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QFrame, QGridLayout, 
                               QDialogButtonBox, QCheckBox, QGroupBox, QDoubleSpinBox,
                               QWidget, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt
from .imposition import SheetAssembler

class NamingDialog(QDialog):
    def __init__(self, parent, model_slug: str, available_vars: list[str], 
                 current_pattern: str = "", model_size_px: tuple[int, int] = (1000, 1000),
                 current_imposition: dict = None, is_dark: bool = True):
        super().__init__(parent)
        self.setWindowTitle("Configurar Saída e Impressão")
        self.resize(500, 450)
        
        self.model_slug = model_slug
        self.result_pattern = current_pattern
        self.model_w, self.model_h = model_size_px
        self.ratio = self.model_w / self.model_h if self.model_h > 0 else 1.0
        
        self.imposition_settings = current_imposition or {
            "enabled": False, 
            "sheet_w_mm": 210.0,
            "sheet_h_mm": 297.0,
            "crop_marks": True,
            "target_w_mm": 0, 
            "target_h_mm": 0,
            "print_after_generation": False
        }

        # Captura o estado atual do tema recebido da MainWindow
        self.current_is_dark = is_dark

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("<b>1. Padrão de Nomenclatura:</b>"))

        ly_preview = QHBoxLayout()
        ly_preview.setSpacing(5)
        
        lbl_prefix = QLabel(f"{self.model_slug}_")
        lbl_prefix.setStyleSheet("font-weight: bold; font-size: 14px;") 
        
        self.txt_pattern = QLineEdit()
        self.txt_pattern.setPlaceholderText("padrão (sequencial)")
        self.txt_pattern.setText(current_pattern)
        self.txt_pattern.setMinimumHeight(34) 
        
        lbl_ext = QLabel(".png")
        lbl_ext.setStyleSheet("font-size: 14px; opacity: 0.7;") 

        ly_preview.addWidget(lbl_prefix)
        ly_preview.addWidget(self.txt_pattern)
        ly_preview.addWidget(lbl_ext)
        layout.addLayout(ly_preview)

        layout.addWidget(QLabel("Variáveis disponíveis:"))
        grid_vars = QGridLayout()
        grid_vars.setSpacing(8)
        col, row = 0, 0
        
        if not available_vars:
            layout.addWidget(QLabel("<i>(Nenhuma coluna encontrada)</i>"))
        else:
            for var in available_vars:
                btn = QPushButton(f"{{{var}}}")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setMinimumHeight(30)
                btn.clicked.connect(lambda checked, v=var: self._insert_variable(v))
                grid_vars.addWidget(btn, row, col)
                col += 1
                if col > 3: 
                    col = 0
                    row += 1
            layout.addLayout(grid_vars)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        layout.addWidget(QLabel("<b>2. Saída e Impressão:</b>"))
        
        # -- Folha de Saída (Independente da imposição) --
        layout.addWidget(QLabel("Folha de saída (Largura x Altura):"))
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
        layout.addLayout(ly_sheet)

        self.chk_imposition = QCheckBox("Habilitar Imposição (Agrupamento na folha)")
        self.chk_imposition.setChecked(self.imposition_settings.get("enabled", False))
        self.chk_imposition.toggled.connect(self._toggle_imposition_ui)
        layout.addWidget(self.chk_imposition)

        # Container para agrupar os controles de imposição e facilitar o ocultamento
        self.container_imposition = QWidget()
        self.container_imposition.setVisible(self.chk_imposition.isChecked())
        ly_imp = QVBoxLayout(self.container_imposition)
        ly_imp.setContentsMargins(10, 0, 0, 0) # Recuo à esquerda para hierarquia

        # -- Dimensões do Modelo --
        ly_imp.addWidget(QLabel("Dimensões do modelo final (Largura x Altura):"))
        
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
            self.spin_w_mm.setValue(100.0)
            self.spin_h_mm.setValue(100.0 / self.ratio)

        self.spin_w_mm.valueChanged.connect(self._on_width_changed)
        self.spin_h_mm.valueChanged.connect(self._on_height_changed)

        ly_model_dims = QHBoxLayout()
        ly_model_dims.addWidget(self.spin_w_mm)
        ly_model_dims.addWidget(QLabel("x"))
        ly_model_dims.addWidget(self.spin_h_mm)
        ly_model_dims.addStretch()
        ly_imp.addLayout(ly_model_dims)

        # -- Indicador de Capacidade --
        self.lbl_capacity = QLabel("Calculando capacidade...")
        self.lbl_capacity.setContentsMargins(0, 5, 0, 5) # Recuo alinhado aos inputs
        self.lbl_capacity.setStyleSheet("font-weight: bold; color: #2ecc71;")
        ly_imp.addWidget(self.lbl_capacity)

        # -- Linha Divisória --
        line_imp = QFrame()
        line_imp.setFrameShape(QFrame.Shape.HLine)
        line_imp.setFrameShadow(QFrame.Shadow.Sunken)
        ly_imp.addWidget(line_imp)

        # -- Marcas de Corte --
        self.chk_crop_marks = QCheckBox("Habilitar marcas de corte")
        self.chk_crop_marks.setChecked(self.imposition_settings.get("crop_marks", True))
        ly_imp.addWidget(self.chk_crop_marks)

        # -- Imprimir automaticamente --
        self.chk_print_after = QCheckBox("Imprimir automaticamente após gerar")
        self.chk_print_after.setToolTip("Gera os arquivos na pasta e envia para a impressora ao final.")
        self.chk_print_after.setChecked(self.imposition_settings.get("print_after_generation", False))
        ly_imp.addWidget(self.chk_print_after)

        # Adiciona o container ao layout principal da janela
        layout.addWidget(self.container_imposition)

        # Conectar todos os inputs que afetam o cálculo
        self.spin_sheet_w_mm.valueChanged.connect(self._update_capacity_preview)
        self.spin_sheet_h_mm.valueChanged.connect(self._update_capacity_preview)
        self.spin_w_mm.valueChanged.connect(self._update_capacity_preview)
        self.spin_h_mm.valueChanged.connect(self._update_capacity_preview)
        self.chk_crop_marks.toggled.connect(self._update_capacity_preview)
        self.chk_imposition.toggled.connect(self._update_capacity_preview)

        layout.addStretch()

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns = self.buttonBox
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # --- Seção: Preferências do Sistema ---
        grp_system = QGroupBox("Preferências do Sistema (Global)")
        ly_system = QVBoxLayout(grp_system)
        
        self.radio_light = QRadioButton("☀️ Tema Claro")
        self.radio_dark = QRadioButton("🌙 Tema Escuro (Mint-Y)")
        
        self.theme_group = QButtonGroup(self)
        self.theme_group.addButton(self.radio_light)
        self.theme_group.addButton(self.radio_dark)
        
        if self.current_is_dark:
            self.radio_dark.setChecked(True)
        else:
            self.radio_light.setChecked(True)
            
        ly_system.addWidget(self.radio_dark)
        ly_system.addWidget(self.radio_light)
        layout.addWidget(grp_system)

        # Executa o cálculo inicial somente após toda a interface (incluindo botões) ser criada
        self._update_capacity_preview()

    def get_pattern(self):
        return self.result_pattern
    
    def get_imposition_settings(self):
        return {
            "enabled": self.chk_imposition.isChecked(),
            "sheet_w_mm": self.spin_sheet_w_mm.value(),
            "sheet_h_mm": self.spin_sheet_h_mm.value(),
            "crop_marks": self.chk_crop_marks.isChecked(),
            "target_w_mm": self.spin_w_mm.value(),
            "target_h_mm": self.spin_h_mm.value(),
            "print_after_generation": self.chk_print_after.isChecked()
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

        # Instancia o assembler (o mesmo motor que gera as imagens)
        assembler = SheetAssembler(tw, th, sw, sh, marks)
        
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

    
    
    