import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QComboBox, QTableWidget, QTableWidgetItem

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


def test_editor_save_discards_columns_removed_from_the_model_without_prompt():
    table = workspace_harness(
        [quantity_header_label(), "Nome", "Link"],
        [[1, "Ada", "https://example.test"]],
    ).table_panel.table
    combo = QComboBox()
    combo.addItem("Modelo de teste")
    log = []

    def reload_models(*, select_name):
        assert select_name == "Modelo de teste"
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([quantity_header_label(), "Nome"])
        table.setRowCount(1)
        table.setItem(0, 0, QTableWidgetItem("1"))
        combo.setCurrentText(select_name)

    harness = SimpleNamespace(
        table_panel=SimpleNamespace(table=table),
        preview_panel=SimpleNamespace(cbo_models=combo),
        log_panel=SimpleNamespace(append=log.append),
        _reload_models_from_disk=reload_models,
        _on_table_selection=lambda: None,
    )

    MainWindow._on_editor_saved(
        harness, "Modelo de teste", ["Nome"], "/tmp/template_v4.json"
    )

    assert table.columnCount() == 2
    assert [table.horizontalHeaderItem(column).text() for column in range(2)] == [
        quantity_header_label(), "Nome",
    ]
    assert table.item(0, 1).text() == "Ada"


def test_model_reload_restores_last_selected_model(tmp_path, monkeypatch):
    models = tmp_path / "models"
    (models / "modelo_1").mkdir(parents=True)
    (models / "modelo_4").mkdir()
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue("workspace/last_model_id", "modelo_4")
    combo = QComboBox()
    loaded = []
    harness = SimpleNamespace(
        preview_panel=SimpleNamespace(cbo_models=combo),
        settings=settings,
        _on_model_changed=loaded.append,
    )
    monkeypatch.setattr(
        "features.workspace.main_window.get_models_dir", lambda: models
    )
    monkeypatch.setattr(
        "features.workspace.main_window.load_model_document",
        lambda folder: {"name": "Modelo 4" if folder.name == "modelo_4" else "Modelo 1"},
    )

    MainWindow._reload_models_from_disk(harness)

    assert combo.currentText() == "Modelo 4"
    assert combo.currentData() == "modelo_4"
    assert loaded == ["Modelo 4"]
