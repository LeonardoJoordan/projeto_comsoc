from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                               QTableWidgetItem, QApplication, QMenu)
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

        curr = self.currentIndex()
        if not curr.isValid():
            start_row = 0
            start_col_logical = 0
        else:
            start_row = curr.row()
            start_col_logical = curr.column()

        header = self.horizontalHeader()
        start_visual_col = header.visualIndex(start_col_logical)
        
        has_sig_col = (header.count() > 0 and self.horizontalHeaderItem(0) and self.horizontalHeaderItem(0).text() == "✍️ Ass.")
        
        # Desloca a colagem para o lado se o usuário tentou colar em cima da checkbox de assinatura
        if has_sig_col and start_col_logical == 0:
            start_col_logical = 1
            start_visual_col = header.visualIndex(start_col_logical)
            
        required_rows = start_row + len(grid_struct)
        if required_rows > self.rowCount():
            self.setRowCount(required_rows)

        affected_cols_logical = set()
        row_end = start_row + len(grid_struct) - 1

        for r, row_data in enumerate(grid_struct):
            dest_row = start_row + r
            style_row = grid_style[r] if r < len(grid_style) else []

            if has_sig_col:
                sig_item = self.item(dest_row, 0)
                if sig_item is None:
                    default_chk = Qt.CheckState.Checked
                    if self.rowCount() > 0 and self.item(0, 0):
                        default_chk = self.item(0, 0).checkState()
                    sig_item = QTableWidgetItem("")
                    sig_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    sig_item.setCheckState(default_chk)
                    sig_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(dest_row, 0, sig_item)

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

        self.table = RichTableWidget(0, 0)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionsMovable(True)
        layout.addWidget(self.table, 1)