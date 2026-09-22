from PySide6.QtCore import Qt
from features.workspace.export_models_dialog import ExportModelsDialog
from features.workspace.import_models_dialog import ImportModelsDialog


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
