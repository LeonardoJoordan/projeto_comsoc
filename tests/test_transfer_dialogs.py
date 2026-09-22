from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from features.workspace.export_models_dialog import ExportModelsDialog
from features.workspace.import_models_dialog import ImportModelsDialog


def test_transfer_rows_have_24px_content_and_2px_vertical_padding(qtbot):
    export = ExportModelsDialog(models=[('a', 'Diploma'), ('b', 'Cartão')])
    imports = ImportModelsDialog(None, [('a', 'Diploma'), ('b', 'Cartão')], {'diploma'})
    for dialog in (export, imports):
        qtbot.addWidget(dialog)
        dialog.show()
    qtbot.waitUntil(lambda: export.list_widget.visualItemRect(export.list_widget.item(0)).height() == 28)
    rectangles = [export.list_widget.visualItemRect(export.list_widget.item(i)) for i in range(2)]
    assert all(rect.height() == 28 for rect in rectangles)
    assert rectangles[1].top() - rectangles[0].top() == 28
    for row in range(imports.table.rowCount()):
        assert imports.table.rowHeight(row) == 28
        actions = imports.table.cellWidget(row, 2)
        if actions is not None:
            margins = actions.layout().contentsMargins()
            assert (margins.top(), margins.bottom()) == (2, 2)
            for button in actions.findChildren(QPushButton):
                assert button.height() == 24
                assert button.y() == 2


def test_export_search_preserves_selection_and_bulk_is_explicit(qtbot):
    dialog = ExportModelsDialog(models=[('a', 'Diploma'), ('b', 'Cartão')])
    qtbot.addWidget(dialog)
    assert not dialog.primary.isEnabled()
    dialog.search.setText('diploma')
    dialog.select_all.click()
    assert dialog.get_selected_models() == ['a', 'b']
    dialog.search.setText('cartão')
    dialog.select_all.click()
    assert dialog.get_selected_models() == ['a', 'b']
    assert 'ZIP' in dialog.summary.text()
    dialog.clear_selection.click()
    assert dialog.get_selected_models() == []
    assert not dialog.primary.isEnabled()


def test_import_conflicts_preserve_existing_until_explicit_choice(qtbot):
    dialog = ImportModelsDialog(None, [('a', 'Diploma', 'Sem proteção'),
                                     ('b', 'Cartão', 'Assinaturas protegidas')], {'diploma'})
    qtbot.addWidget(dialog)
    assert dialog.get_decisions() == {'a': {'import': False, 'action': 'rename'},
                                      'b': {'import': True, 'action': 'new'}}
    dialog.search.setText('diploma')
    dialog.select_all.click()
    assert dialog.table.cellWidget(0, 2).isAncestorOf(dialog.copy_all)
    assert not dialog.table.isRowHidden(0)
    assert dialog.actions[1].button(0).isEnabled()
    dialog.replace_all.click()
    assert dialog.get_decisions()['a'] == {'import': True, 'action': 'replace'}
    assert '1' in dialog.summary.text()
    dialog.actions[1].button(0).click()
    assert dialog.get_decisions()['a']['action'] == 'rename'
    assert not dialog.actions[1].button(1).isChecked()
    dialog.clear_selection.click()
    assert not dialog.primary.isEnabled()
    assert not dialog.actions[1].button(0).isEnabled()
