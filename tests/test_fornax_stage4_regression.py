from unittest.mock import patch
import pytest
from core.fornax_container import FULL_MODE, PUBLIC_MODE, FornaxError, save_protected_fornax, save_public_fornax
from core.fornax_session import FornaxSessionManager, AccessState
from core.fornax_export import ExportRequest, export_models
from core.fornax_import import open_import_package, import_candidate
from core.file_transactions import file_sha256
from tests.test_legacy_migration import _legacy_document

PASSWORD = 'regression-test-password'


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
