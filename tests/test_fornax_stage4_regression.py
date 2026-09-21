from unittest.mock import patch
import pytest
from core.fornax_container import FULL_MODE, PUBLIC_MODE, FornaxError, save_protected_fornax, save_public_fornax
from core.fornax_session import FornaxSessionManager, AccessState
from core.fornax_export import ExportRequest, export_models
from core.fornax_import import open_import_package, import_candidate
from core.file_transactions import file_sha256
from tests.test_legacy_migration import _legacy_document

PASSWORD = 'regression-test-password'


@pytest.mark.parametrize('mode', ['signatures', 'full'])
def test_protecting_public_v2_also_protects_backup(tmp_path, mode):
    from tests.test_fornax_export import acknowledged_public_signature_document
    from tests.test_fornax_crypto import FIXTURE_DIR
    from core.fornax_container import inspect_fornax, open_public_fornax, unlock_fornax
    from core.model_document import document_signatures
    source = acknowledged_public_signature_document()
    target = tmp_path / 'model.fornax'
    descriptor = save_public_fornax(source, target, source_dir=FIXTURE_DIR)
    save_protected_fornax(source, target, PASSWORD, mode=mode,
                         source_dir=FIXTURE_DIR, model_id=descriptor.model_id)
    for path in (target, target.with_name(target.name + '.bak')):
        assert inspect_fornax(path).mode == mode
        assert inspect_fornax(path).model_id == descriptor.model_id
        if mode == FULL_MODE:
            with pytest.raises(FornaxError):
                open_public_fornax(path)
        else:
            assert not document_signatures(open_public_fornax(path).document())
        opened = unlock_fornax(path, PASSWORD)
        assert document_signatures(opened.document())
        assert 'protection_preferences' not in opened.document()


@pytest.mark.parametrize('case', ['external', 'recovery', 'recovery_backup'])
def test_protection_action_preserves_external_files_and_pending_recovery(tmp_path, case):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from features.workspace.main_window import MainWindow
    from features.editor.editor_window import EditorWindow
    target = tmp_path / 'model.fornax'
    descriptor = save_public_fornax(_legacy_document('public'), target)
    before = target.read_bytes()
    entry = SimpleNamespace(is_fornax=True, path=target, descriptor=descriptor,
                            key='external:model' if case == 'external' else 'model')
    if case != 'external':
        recovery = EditorWindow.fornax_recovery_path(target)
        if case == 'recovery_backup':
            recovery = recovery.with_name(recovery.name + '.bak')
        recovery.write_bytes(b'unsaved recovery')
    host = SimpleNamespace(_current_library_entry=lambda: entry,
                           _open_selected_fornax=Mock())
    with patch('features.workspace.main_window.QMessageBox.information'), \
         patch('features.workspace.main_window.QMessageBox.warning'):
        MainWindow._protect_current_model(host)
    host._open_selected_fornax.assert_not_called()
    assert target.read_bytes() == before
    if case != 'external':
        assert recovery.read_bytes() == b'unsaved recovery'


def test_public_signatures_never_derive_password_and_preserve_rendering(tmp_path):
    from tests.test_fornax_export import acknowledged_public_signature_document
    from tests.test_fornax_crypto import FIXTURE_DIR
    from core.fornax_container import open_public_fornax
    from features.generator.renderer import renderers_for_document
    source = acknowledged_public_signature_document()
    expected = [r.render_to_qimage({}, {}) for r in renderers_for_document(
        source, asset_provider=lambda reference: (FIXTURE_DIR / reference).read_bytes())]
    target = tmp_path / 'public.fornax'
    with patch('core.fornax_container._derive_kek', side_effect=AssertionError('public KDF')):
        save_public_fornax(source, target, source_dir=FIXTURE_DIR)
        opened = open_public_fornax(target)
        actual = [r.render_to_qimage({}, {}) for r in renderers_for_document(
            opened.document(), asset_provider=opened.asset)]
        assert actual == expected
        sessions = FornaxSessionManager()
        sessions.select(target)
        sessions.save(sessions.document())
        sessions.close()


def test_grace_keeps_authorization_but_releases_document_and_assets(tmp_path):
    one, two = tmp_path / 'one.fornax', tmp_path / 'two.fornax'
    save_protected_fornax(_legacy_document('one'), one, PASSWORD, mode=FULL_MODE)
    save_public_fornax(_legacy_document('two'), two)
    manager = FornaxSessionManager()
    manager.unlock(one, PASSWORD)
    job = manager.borrow_job()
    manager.select(two)
    assert manager.status(one).state == AccessState.GRACE
    assert manager._sessions[one].opened is None
    assert manager._sessions[one].kek is not None
    assert job.document()['name'] == 'one'
    with patch('core.fornax_container._derive_kek', side_effect=AssertionError('KDF repeated')):
        manager.select(one)
        assert manager.document()['name'] == 'one'
    assert manager._sessions[two].opened is None
    manager.select(two)
    assert manager.document()['name'] == 'two'
    job.close()
    manager.close()


def test_export_rejects_change_after_approval_without_retaining_opened_documents(tmp_path):
    source = tmp_path / 'one.fornax'
    target = tmp_path / 'out.fornax'
    save_protected_fornax(_legacy_document('one'), source, PASSWORD, mode=FULL_MODE)
    request = ExportRequest(source, 'one', local_password=PASSWORD, approved_sha256=file_sha256(source))
    save_protected_fornax(_legacy_document('changed'), source, PASSWORD, mode=FULL_MODE)
    with pytest.raises(FornaxError, match='mudou após'):
        export_models([request], target, include_signatures=True, transport_password=PASSWORD)
    assert not target.exists()


def test_import_rejects_change_after_approval_without_retaining_opened_documents(tmp_path):
    source = tmp_path / 'one.fornax'
    target = tmp_path / 'out.fornax'
    save_public_fornax(_legacy_document('one'), source)
    with open_import_package(source) as candidates:
        candidate = candidates[0]
        approved = file_sha256(candidate.path)
        candidate.path.write_bytes(b'changed')
        with pytest.raises(FornaxError, match='mudou após'):
            import_candidate(candidate, target, include_signatures=False, approved_sha256=approved)
    assert not target.exists()


def test_editor_preserves_saved_canvas_pixels_and_custom_mask_ids(tmp_path):
    from features.editor.editor_window import EditorWindow
    from features.editor.canvas_items import ImageItem, RectangleItem
    from tests.test_fornax_crypto import protected_document, FIXTURE_DIR
    from core.fornax_container import SIGNATURES_MODE
    document = protected_document()
    path = tmp_path / 'fixture.fornax'
    save_protected_fornax(document, path, PASSWORD, mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR)
    manager = FornaxSessionManager()
    status = manager.unlock(path, PASSWORD)
    editor = EditorWindow()
    try:
        editor.load_from_fornax(manager.document(), path=path, mode=SIGNATURES_MODE,
                               model_id=status.descriptor.model_id,
                               asset_provider=manager.asset, session_manager=manager)
        state = editor.get_current_scene_state()
        assert state['canvas_size'] == document['canvas_size']
        image = next(item for item in editor.scene.items() if type(item) is ImageItem)
        assert isinstance(image.parentItem(), RectangleItem)
        assert image.mask_shape_id == f'shape:{image.parentItem().layer_id}'
        assert image.parentItem().x() == 282
        # A normalização da cena não altera o arquivo que originou o modelo.
        assert manager.document()['pages'][0]['images'][0]['mask_shape_id'] == 'shape:mask'
    finally:
        editor._last_saved_state = editor.get_current_scene_state()
        editor._last_saved_document_state = editor._capture_document_history_state()
        editor.close()
        manager.close()
