import os
import json
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QTableWidget, QTableWidgetItem

from features.spreadsheet.headers import (
    SIGNATURE_HEADER,
    SIGNATURE_ID_ROLE,
    quantity_header_label,
)
from features.spreadsheet.table_panel import RichTableWidget
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


def test_each_signature_receives_its_own_stable_table_column():
    table = RichTableWidget(0, 0)
    harness = SimpleNamespace(table_panel=SimpleNamespace(table=table))
    signatures = [
        {"signature_id": "sig-reitor", "custom_name": "Reitor", "visible": True},
        {"signature_id": "sig-diretor", "custom_name": "Diretor local", "visible": False},
    ]

    MainWindow._update_table_columns(harness, ["Nome"], signatures)

    assert table.columnCount() == 4
    assert [table.horizontalHeaderItem(column).text() for column in range(4)] == [
        quantity_header_label(), "Reitor", "Diretor local", "Nome",
    ]
    assert table.horizontalHeaderItem(1).data(SIGNATURE_ID_ROLE) == "sig-reitor"
    assert table.horizontalHeaderItem(2).data(SIGNATURE_ID_ROLE) == "sig-diretor"
    assert table.item(0, 1).checkState() == Qt.CheckState.Checked
    assert table.item(0, 2).checkState() == Qt.CheckState.Unchecked

    table.item(0, 1).setCheckState(Qt.CheckState.Unchecked)
    table.item(0, 2).setCheckState(Qt.CheckState.Checked)
    table.setItem(0, 3, QTableWidgetItem("Ada"))
    data = SimpleNamespace(
        table_panel=SimpleNamespace(table=table),
        active_model_name="Modelo de teste",
    )
    plain, rich = MainWindow._scrape_table_data(data)

    expected = {"sig-reitor": False, "sig-diretor": True}
    assert plain[0]["__signature_visibility__"] == expected
    assert rich[0]["__signature_visibility__"] == expected
    assert "__use_signature__" not in plain[0]


def test_new_and_duplicated_rows_preserve_each_signature_default():
    table = RichTableWidget(0, 0)
    harness = SimpleNamespace(table_panel=SimpleNamespace(table=table))
    MainWindow._update_table_columns(harness, [], [
        {"signature_id": "sig-a", "custom_name": "A", "visible": True},
        {"signature_id": "sig-b", "custom_name": "B", "visible": False},
    ])

    table._add_rows(1)
    assert table.item(1, 1).checkState() == Qt.CheckState.Checked
    assert table.item(1, 2).checkState() == Qt.CheckState.Unchecked

    table.selectRow(1)
    table._duplicate_selected_rows()
    assert table.item(2, 1).checkState() == Qt.CheckState.Checked
    assert table.item(2, 2).checkState() == Qt.CheckState.Unchecked


def test_duplicated_text_cell_preserves_alignment():
    table = RichTableWidget(1, 2)
    table.setHorizontalHeaderLabels(['Quantidade', 'Nome'])
    alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    cell = QTableWidgetItem('Texto')
    cell.setTextAlignment(alignment)
    table.setItem(0, 1, cell)
    table.selectRow(0)
    table._duplicate_selected_rows()
    assert table.item(1, 1).textAlignment() == alignment


def test_clicking_signature_header_icon_toggles_only_that_whole_column():
    table = RichTableWidget(0, 0)
    harness = SimpleNamespace(table_panel=SimpleNamespace(table=table))
    MainWindow._update_table_columns(harness, [], [
        {"signature_id": "sig-a", "custom_name": "Reitor", "visible": True},
        {"signature_id": "sig-b", "custom_name": "Diretor", "visible": False},
    ])
    table._add_rows(2)
    table.resize(360, 160)
    table.show()
    APP.processEvents()

    changes = []
    table.signatureColumnToggled.connect(
        lambda column, checked: changes.append((column, checked))
    )
    header = table.horizontalHeader()
    icon_rect = header.signature_icon_rect(1)
    assert not icon_rect.isEmpty()

    QTest.mouseClick(
        header.viewport(), Qt.MouseButton.LeftButton, pos=icon_rect.center()
    )
    assert changes == [(1, False)]
    assert all(
        table.item(row, 1).checkState() == Qt.CheckState.Unchecked
        for row in range(table.rowCount())
    )
    assert all(
        table.item(row, 2).checkState() == Qt.CheckState.Unchecked
        for row in range(table.rowCount())
    )

    QTest.mouseClick(
        header.viewport(), Qt.MouseButton.LeftButton, pos=icon_rect.center()
    )
    assert changes[-1] == (1, True)
    assert all(
        table.item(row, 1).checkState() == Qt.CheckState.Checked
        for row in range(table.rowCount())
    )
    assert all(
        table.item(row, 2).checkState() == Qt.CheckState.Unchecked
        for row in range(table.rowCount())
    )
    table.close()


def test_signature_checkbox_is_centered_clickable_and_explained():
    table = RichTableWidget(0, 0)
    harness = SimpleNamespace(table_panel=SimpleNamespace(table=table))
    MainWindow._update_table_columns(harness, [], [
        {"signature_id": "sig-a", "custom_name": "Reitor", "visible": True},
    ])
    table.resize(240, 120)
    table.show()
    APP.processEvents()

    item = table.item(0, 1)
    cell_rect = table.visualItemRect(item)
    assert item.textAlignment() & Qt.AlignmentFlag.AlignHCenter
    assert "assinatura" in item.toolTip().lower()
    assert "ícone" in table.horizontalHeaderItem(1).toolTip().lower()

    QTest.mouseClick(
        table.viewport(), Qt.MouseButton.LeftButton, pos=cell_rect.center()
    )
    assert item.checkState() == Qt.CheckState.Unchecked
    QTest.mouseClick(
        table.viewport(), Qt.MouseButton.LeftButton, pos=cell_rect.center()
    )
    assert item.checkState() == Qt.CheckState.Checked
    table.close()


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
        _protected_model_names=lambda: {},
        _model_library_list_setting=lambda _key: [],
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


def test_model_library_places_pinned_first_and_then_recent_models(tmp_path, monkeypatch):
    models = tmp_path / "models"
    names = {
        "modelo_a": "Alfa", "modelo_b": "Beta",
        "modelo_c": "Gama", "modelo_d": "Delta",
    }
    for key in names:
        (models / key).mkdir(parents=True, exist_ok=True)
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue("workspace/model_library_sort", "recent")
    settings.setValue("workspace/model_library_pinned", json.dumps(["modelo_c"]))
    settings.setValue(
        "workspace/model_library_recent", json.dumps(["modelo_b", "modelo_a"])
    )
    combo = QComboBox()
    loaded = []
    harness = SimpleNamespace(
        preview_panel=SimpleNamespace(cbo_models=combo),
        settings=settings,
        _on_model_changed=loaded.append,
        _protected_model_names=lambda: {},
        _model_library_list_setting=lambda key: json.loads(
            str(settings.value(key, "[]"))
        ),
    )
    monkeypatch.setattr(
        "features.workspace.main_window.get_models_dir", lambda: models
    )
    monkeypatch.setattr(
        "features.workspace.main_window.load_model_document",
        lambda folder: {"name": names[folder.name]},
    )

    MainWindow._reload_models_from_disk(harness)

    ordered_keys = [
        combo.itemData(index) for index in range(combo.count())
        if combo.itemData(index) is not None
    ]
    assert ordered_keys == ["modelo_c", "modelo_b", "modelo_a", "modelo_d"]
    assert combo.itemData(1) is None  # separador após os modelos fixados
    assert combo.currentText() == "Gama"
    assert loaded == ["Gama"]
