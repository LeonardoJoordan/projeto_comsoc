from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                               QTableWidgetItem, QApplication, QMenu, QPushButton, QSpinBox,
                               QAbstractItemView)
from PySide6.QtGui import QKeySequence, QFontMetrics, QAction
from PySide6.QtCore import Qt, QTimer

# Importações relativas ao domínio
from .clipboard import parse_clipboard_html_table, parse_tsv
from .delegates import HTMLDelegate

class RichTableWidget(QTableWidget):
    RICH_ROLE = Qt.ItemDataRole.UserRole

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setItemDelegate(HTMLDelegate(self))
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.itemChanged.connect(self._force_qty_alignment)

    def _force_qty_alignment(self, item):
        # Se a mudança foi na coluna 0, bloqueia sinais para evitar loop e centraliza
        if item.column() == 0:
            self.blockSignals(True)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.blockSignals(False)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_bold = QAction("Negrito (Ctrl+B)", self)
        act_bold.triggered.connect(lambda: self._toggle_format("b"))
        act_italic = QAction("Itálico (Ctrl+I)", self)
        act_italic.triggered.connect(lambda: self._toggle_format("i"))
        act_underline = QAction("Sublinhado (Ctrl+U)", self)
        act_underline.triggered.connect(lambda: self._toggle_format("u"))
        act_clear = QAction("Limpar Formatação", self)
        act_clear.triggered.connect(self._clear_formatting)

        menu.addActions([act_bold, act_italic, act_underline])
        menu.addSeparator()
        menu.addAction(act_clear)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            if key == Qt.Key.Key_B:
                self._toggle_format("b")
                return
            elif key == Qt.Key.Key_I:
                self._toggle_format("i")
                return
            elif key == Qt.Key.Key_U:
                self._toggle_format("u")
                return
        
        if event.matches(QKeySequence.StandardKey.Paste):
            self._paste_from_clipboard()
            return

        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._handle_delete()
            return

        super().keyPressEvent(event)

    def _handle_delete(self):
        sel_rows = self.selectionModel().selectedRows()
        if sel_rows:
            rows_to_del = sorted([idx.row() for idx in sel_rows], reverse=True)
            for r in rows_to_del:
                self.removeRow(r)
            if self.rowCount() == 0:
                self.insertRow(0)
                has_sig_col = (self.horizontalHeaderItem(0) and self.horizontalHeaderItem(0).text() == "✍️ Assinatura")
                if has_sig_col:
                    item = QTableWidgetItem("")
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    item.setCheckState(Qt.CheckState.Checked)
                    self.setItem(0, 0, item)
        else:
            for item in self.selectedItems():
                item.setText("")
                item.setData(self.RICH_ROLE, None)

    def _add_rows(self, count: int):
        # Detecta a presença das colunas funcionais pelos headers
        has_qty_col = (self.columnCount() > 0 and self.horizontalHeaderItem(0).text() == "🔢 Qtd")
        has_sig_col = (self.columnCount() > 1 and self.horizontalHeaderItem(1).text() == "✍️ Ass.")
        
        for _ in range(count):
            row_idx = self.rowCount()
            self.insertRow(row_idx)
            
            # 1. Coluna Quantidade (Sempre Index 0)
            if has_qty_col:
                qty_item = QTableWidgetItem("1")
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row_idx, 0, qty_item)
            
            # 2. Coluna Assinatura (Sempre Index 1 se existir)
            if has_sig_col:
                default_chk = Qt.CheckState.Checked
                if row_idx > 0 and self.item(0, 1):
                    default_chk = self.item(0, 1).checkState()
                sig_item = QTableWidgetItem("")
                sig_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                sig_item.setCheckState(default_chk)
                sig_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row_idx, 1, sig_item)

    def _duplicate_selected_rows(self):
        indexes = self.selectionModel().selectedIndexes()
        if not indexes: return
        
        rows_to_dup = sorted(list(set(idx.row() for idx in indexes)), reverse=True)
        cols = self.columnCount()
        
        # Identifica os índices das colunas funcionais pelos headers atuais
        has_qty_col = (cols > 0 and self.horizontalHeaderItem(0).text() == "🔢 Qtd")
        has_sig_col = (cols > 1 and self.horizontalHeaderItem(1).text() == "✍️ Ass.")
        
        for r in rows_to_dup:
            new_row = r + 1
            self.insertRow(new_row)
            
            for c in range(cols):
                old_item = self.item(r, c)
                if not old_item:
                    continue
                
                new_item = QTableWidgetItem(old_item.text())
                
                # Caso especial: Coluna de Assinatura (Index 1)
                if has_sig_col and c == 1:
                    new_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    new_item.setCheckState(old_item.checkState())
                    new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Caso especial: Coluna de Qtd ou texto comum (copia alinhamento)
                else:
                    new_item.setTextAlignment(old_item.textAlignment())

                # Preserva os dados Rich Text (HTML) se existirem
                rich_data = old_item.data(self.RICH_ROLE)
                if rich_data:
                    new_item.setData(self.RICH_ROLE, rich_data)
                        
                self.setItem(new_row, c, new_item)

    def _toggle_word_wrap(self, state: bool):
        self.setWordWrap(state)
        if state:
            self.resizeRowsToContents()
            # Adiciona 15px de "respiro" para evitar o scroll interno nas células
            for r in range(self.rowCount()):
                self.setRowHeight(r, self.rowHeight(r) + 15)
        else:
            # Força todas as linhas a voltarem ao tamanho compacto padrão
            for r in range(self.rowCount()):
                self.setRowHeight(r, 30)

    def _delete_selected_rows_action(self):
        # selectedIndexes pega as coordenadas visuais, mesmo se a célula estiver virgem/vazia
        indexes = self.selectionModel().selectedIndexes()
        if not indexes: return
        
        rows_to_del = sorted(list(set(idx.row() for idx in indexes)), reverse=True)
        
        for r in rows_to_del:
            self.removeRow(r)
            
        # Se a tabela ficar vazia, recria a linha inicial padrão
        if self.rowCount() == 0:
            self.insertRow(0)
            has_sig_col = (self.horizontalHeaderItem(0) and self.horizontalHeaderItem(0).text() == "✍️ Ass.")
            if has_sig_col:
                item = QTableWidgetItem("")
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Checked)
                self.setItem(0, 0, item)

    def _toggle_format(self, tag: str):
        items = self.selectedItems()
        if not items: return

        start_tag = f"<{tag}>"
        end_tag = f"</{tag}>"

        for item in items:
            current_html = item.data(self.RICH_ROLE)
            if not current_html:
                current_html = item.text()

            check = current_html.strip()
            if check.startswith(start_tag) and check.endswith(end_tag):
                new_html = check[len(start_tag):-len(end_tag)]
            else:
                new_html = f"{start_tag}{check}{end_tag}"

            item.setData(self.RICH_ROLE, new_html)
        self.viewport().update()

    def _clear_formatting(self):
        for item in self.selectedItems():
            text = item.text()
            item.setData(self.RICH_ROLE, None)
            item.setText(text)

    def _text_width_px(self, text: str) -> int:
        fm = QFontMetrics(self.font())
        lines = (text or "").splitlines() or [""]
        return max(fm.horizontalAdvance(line) for line in lines)

    def _autofit_columns_after_paste(self, cols_logical: set[int], row_start: int, row_end: int, padding_px: int = 20):
        header = self.horizontalHeader()
        for col in cols_logical:
            header_item = self.horizontalHeaderItem(col)
            best = self._text_width_px(header_item.text() if header_item else "")
            for r in range(row_start, row_end + 1):
                it = self.item(r, col)
                if it is None: continue
                w = self._text_width_px(it.text())
                if w > best: best = w
            desired = best + padding_px
            if desired > self.columnWidth(col):
                self.setColumnWidth(col, desired)

    def _paste_from_clipboard(self):
        md = QApplication.clipboard().mimeData()
        if not md: return

        text_raw = md.text() if md.hasText() else ""
        grid_struct = parse_tsv(text_raw)
        
        grid_style = []
        if md.hasHtml():
            try:
                grid_style = parse_clipboard_html_table(md.html())
            except Exception:
                grid_style = []

        if not grid_struct: return

        header = self.horizontalHeader()
        has_sig_col = (header.count() > 0 and self.horizontalHeaderItem(0) and self.horizontalHeaderItem(0).text() == "✍️ Ass.")

        # --- LÓGICA DE PREENCHIMENTO EM MASSA (1 célula copiada -> Várias selecionadas) ---
        is_single_cell = (len(grid_struct) == 1 and len(grid_struct[0]) == 1)
        selected_indexes = self.selectionModel().selectedIndexes()
        
        if is_single_cell and len(selected_indexes) > 1:
            val_plain = grid_struct[0][0].plain
            val_rich = grid_style[0][0].rich_html if (grid_style and len(grid_style) > 0 and len(grid_style[0]) > 0) else val_plain
            
            affected_cols_logical = set()
            for idx in selected_indexes:
                r = idx.row()
                c_visual = idx.column()
                c_logical = header.logicalIndex(c_visual)
                
                if has_sig_col and c_logical == 0:
                    continue  # Protege a checkbox
                    
                item = self.item(r, c_logical)
                if item is None:
                    item = QTableWidgetItem()
                    self.setItem(r, c_logical, item)
                    
                item.setText(val_plain)
                item.setData(self.RICH_ROLE, val_rich)
                affected_cols_logical.add(c_logical)
                
            if affected_cols_logical:
                # Autoajuste de colunas baseado nas recém alteradas
                QTimer.singleShot(0, lambda: self._autofit_columns_after_paste(
                    affected_cols_logical, 0, self.rowCount() - 1, padding_px=20
                ))
            return

        # --- LÓGICA PADRÃO DE COLAGEM (Tabela/Bloco) ---
        curr = self.currentIndex()
        if not curr.isValid():
            start_row = 0
            start_col_logical = 0
        else:
            start_row = curr.row()
            start_col_logical = curr.column()

        start_visual_col = header.visualIndex(start_col_logical)
        
        # Desloca a colagem para o lado se o usuário tentou colar em cima da checkbox de assinatura
        if has_sig_col and start_col_logical == 0:
            start_col_logical = 1
            start_visual_col = header.visualIndex(start_col_logical)
            
        required_rows = start_row + len(grid_struct)
        if required_rows > self.rowCount():
            self.setRowCount(required_rows)

        affected_cols_logical = set()
        row_end = start_row + len(grid_struct) - 1

        # Identifica os índices das colunas funcionais
        has_qty_col = (header.count() > 0 and self.horizontalHeaderItem(0).text() == "🔢 Qtd")
        has_sig_col = (header.count() > 1 and self.horizontalHeaderItem(1).text() == "✍️ Ass.")

        for r, row_data in enumerate(grid_struct):
            dest_row = start_row + r
            style_row = grid_style[r] if r < len(grid_style) else []

            # 1. Garante a inicialização da Coluna Qtd (Index 0)
            if has_qty_col:
                qty_item = self.item(dest_row, 0)
                if qty_item is None:
                    qty_item = QTableWidgetItem("1")
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(dest_row, 0, qty_item)

            # 2. Garante a inicialização da Coluna Assinatura (Index 1)
            # 1. Garante a inicialização da Coluna Qtd (Index 0)
            if has_qty_col:
                qty_item = self.item(dest_row, 0)
                if qty_item is None:
                    qty_item = QTableWidgetItem("1")
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(dest_row, 0, qty_item)

            # 2. Garante a inicialização da Coluna Assinatura (Index 1)
            if has_sig_col:
                sig_item = self.item(dest_row, 1)
                if sig_item is None:
                    # Tenta copiar o estado da primeira linha ou assume Checked
                    default_chk = Qt.CheckState.Checked
                    if self.rowCount() > 0 and self.item(0, 1):
                        default_chk = self.item(0, 1).checkState()
                    
                    sig_item = QTableWidgetItem("")
                    sig_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    sig_item.setCheckState(default_chk)
                    sig_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(dest_row, 1, sig_item)

            for c, cell_plain in enumerate(row_data):
                target_visual_col = start_visual_col + c
                if target_visual_col >= self.columnCount():
                    break
                dest_col_logical = header.logicalIndex(target_visual_col)
                item = self.item(dest_row, dest_col_logical)
                if item is None:
                    item = QTableWidgetItem()
                    self.setItem(dest_row, dest_col_logical, item)

                txt_val = cell_plain.plain
                item.setText(txt_val)

                if c < len(style_row):
                    rich_val = style_row[c].rich_html
                    item.setData(self.RICH_ROLE, rich_val)
                else:
                    item.setData(self.RICH_ROLE, txt_val)

                affected_cols_logical.add(dest_col_logical)

        if affected_cols_logical:
            QTimer.singleShot(0, lambda: self._autofit_columns_after_paste(
                affected_cols_logical, start_row, row_end, padding_px=20
            ))

class TablePanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Tabela de dados")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        # --- Barra de Ferramentas da Tabela ---
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 5, 0, 5)
        
        self.spin_add_rows = QSpinBox()
        self.spin_add_rows.setMinimum(1)
        self.spin_add_rows.setMaximum(500)
        self.spin_add_rows.setFixedWidth(50)
        
        self.btn_add_rows = QPushButton("➕ Adicionar Linha(s)")
        self.btn_duplicate_row = QPushButton("📑 Duplicar Linha(s)")
        self.btn_delete_rows = QPushButton("🗑️ Excluir Linha(s)")
        self.btn_toggle_wrap = QPushButton("↕️ Expandir Células")
        self.btn_toggle_wrap.setCheckable(True)
        
        toolbar_layout.addWidget(self.spin_add_rows)
        toolbar_layout.addWidget(self.btn_add_rows)
        toolbar_layout.addWidget(self.btn_duplicate_row)
        toolbar_layout.addWidget(self.btn_delete_rows)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_toggle_wrap)
        
        layout.addLayout(toolbar_layout)

        self.table = RichTableWidget(0, 0)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionsMovable(True)
        layout.addWidget(self.table, 1)

        # --- Conexões da Barra de Ferramentas ---
        self.btn_add_rows.clicked.connect(lambda: self.table._add_rows(self.spin_add_rows.value()))
        self.btn_duplicate_row.clicked.connect(self.table._duplicate_selected_rows)
        self.btn_delete_rows.clicked.connect(self.table._delete_selected_rows_action)
        self.btn_toggle_wrap.toggled.connect(self.table._toggle_word_wrap)