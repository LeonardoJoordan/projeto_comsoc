import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

from features.spreadsheet.headers import SIGNATURE_HEADER, quantity_header_label
from features.workspace.main_window import MainWindow


APP = QApplication.instance() or QApplication([])


def workspace_harness(headers, rows):
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    for row_index, values in enumerate(rows):
        for column, value in enumerate(values):
            if headers[column] == SIGNATURE_HEADER:
                item = QTableWidgetItem("")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)
            else:
                item = QTableWidgetItem(str(value))
            table.setItem(row_index, column, item)
    return SimpleNamespace(
        table_panel=SimpleNamespace(table=table),
        active_model_name="Modelo de teste",
    )


def test_copies_expand_whole_document_rows_and_zero_skips_them():
    harness = workspace_harness(
        [quantity_header_label(), SIGNATURE_HEADER, "Nome", "Campo do verso"],
        [
            [3, True, "Ada", "A"],
            [0, True, "Ignorado", "B"],
            ["inválido", False, "Grace", "C"],
        ],
    )

    plain, rich, sources = MainWindow._scrape_table_data(harness, include_sources=True)

    assert len(plain) == len(rich) == 4
    assert sources == [0, 0, 0, 2]
    assert [row["Nome"] for row in plain] == ["Ada", "Ada", "Ada", "Grace"]
    assert all(row["Campo do verso"] == "A" for row in plain[:3])
    assert plain[-1]["__use_signature__"] is False


def test_inactive_fields_keep_cell_data_but_do_not_feed_generation():
    harness = workspace_harness(
        [quantity_header_label(), "Ativo", "Removido"],
        [[1, "valor atual", "valor preservado"]],
    )
    harness._inactive_table_fields = {"Removido"}

    plain, rich = MainWindow._scrape_table_data(harness)

    assert plain == [{"modelo": "modelo_de_teste", "Ativo": "valor atual"}]
    assert rich == plain
