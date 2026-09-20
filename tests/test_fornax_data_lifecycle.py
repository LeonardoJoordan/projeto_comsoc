"""Auditoria 4.2: assets sintéticos, memória, clipboard e previews tardios."""
from types import SimpleNamespace
from unittest.mock import Mock
import zipfile
import pytest

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from core.fornax_container import FULL_MODE, SIGNATURES_MODE, save_protected_fornax
from core.fornax_session import FornaxSessionManager
from features.editor.editor_window import EditorWindow
from features.editor.canvas_items import ImageItem, BackgroundItem, SignatureItem
from features.generator.renderer import renderers_for_document
from features.preview.sheet_preview_worker import SheetPreviewWorker
from features.workspace.main_window import MainWindow
from tests.test_fornax_editor import _image_document

APP = QApplication.instance() or QApplication([])
PASSWORD = "audit-password-2026"
MARKER = "PRIVATE_AUDIT_42_d6e931"


def protected_model(tmp_path, mode=FULL_MODE):
    source = tmp_path / "sensitive.png"
    image = QImage(32, 20, QImage.Format.Format_ARGB32)
    image.fill(QColor("#2f80ed"))
    assert image.save(str(source))
    document = _image_document(source)
    document["name"] = MARKER if mode == FULL_MODE else "Public template"
    if mode == SIGNATURES_MODE:
        page = document["pages"][0]
        page["signatures"] = page["images"]
        page["images"] = []
        page["signatures"][0]["signature_id"] = "sig-audit"
        page["signatures"][0]["custom_name"] = MARKER
    expected = renderers_for_document(document)[0].render_to_qimage({}, {})
    path = tmp_path / "model.fornax"
    save_protected_fornax(document, path, PASSWORD, mode=mode)
    source.unlink()
    manager = FornaxSessionManager()
    status = manager.unlock(path, PASSWORD)
    return path, manager, status, expected


def assert_no_cleartext_artifacts(root):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        assert MARKER.encode() not in data
        # Identifica também imagem derivada, sem depender de marcador textual.
        assert QImage(str(path)).isNull(), path
        assert path.suffix == ".fornax", path
        with zipfile.ZipFile(path) as archive:
            assert "protected.bin" in archive.namelist()
            for name in archive.namelist():
                if name != "protected.bin":
                    assert MARKER.encode() not in archive.read(name)


@pytest.mark.parametrize("mode", [FULL_MODE, SIGNATURES_MODE])
def test_protected_editor_close_discards_scene_history_and_clipboard(tmp_path, mode):
    path, manager, status, expected = protected_model(tmp_path, mode)
    window = EditorWindow()
    APP.clipboard().setText("public clipboard unchanged")
    window.load_from_fornax(
        manager.document(), path=path, mode=mode,
        model_id=status.descriptor.model_id, asset_provider=manager.asset,
        session_manager=manager,
    )
    try:
        actual = renderers_for_document(manager.document(), asset_provider=manager.asset)[0].render_to_qimage({}, {})
        assert actual == expected
        kind = SignatureItem if mode == SIGNATURES_MODE else ImageItem
        item = next(i for i in window.scene.items()
                    if isinstance(i, kind) and not isinstance(i, BackgroundItem))
        item.setSelected(True)
        window.copy_selected_items()
        assert window._object_clipboard
        item.setPos(23, 14)
        window._write_fornax_recovery()
        recovery = window.fornax_recovery_path(path)
        assert recovery.exists()
        assert_no_cleartext_artifacts(tmp_path)
        window._last_saved_state = window.get_current_scene_state()
        window._last_saved_document_state = window._capture_document_history_state()
        window.close()
        assert not window.scene.items()
        assert window._fornax_asset_provider is None
        assert window._model_document is None
        assert not window._object_clipboard
        assert not window.history._undo_stack
        assert not recovery.exists()
        assert APP.clipboard().text() == "public clipboard unchanged"
        assert_no_cleartext_artifacts(tmp_path)
    finally:
        manager.close()
        APP.processEvents()


@pytest.mark.parametrize("mode", [FULL_MODE, SIGNATURES_MODE])
def test_protected_sheet_worker_keeps_pixels_in_memory_and_discards_inputs(tmp_path, mode):
    path, manager, status, _ = protected_model(tmp_path, mode)
    snapshot = manager.borrow_job()
    worker = SheetPreviewWorker(
        snapshot.document(), [({}, {})],
        {"enabled": True, "target_w_mm": 80, "target_h_mm": 50,
         "sheet_w_mm": 100, "sheet_h_mm": 100, "crop_marks": False},
        tmp_path / "forbidden-cache", 1,
        asset_provider=snapshot.asset, memory_only=True,
        authorized_snapshot=snapshot,
    )
    results, errors = [], []
    worker.pageReady.connect(lambda *args: results.append(args))
    worker.pageFailed.connect(lambda *args: errors.append(args))
    worker.run()
    assert not errors
    assert results and isinstance(results[0][2], QImage)
    assert not results[0][2].isNull()
    assert worker.authorized_snapshot is None
    assert worker.asset_provider is None
    assert worker.template is None
    assert not worker.rows
    assert not (tmp_path / "forbidden-cache").exists()
    assert_no_cleartext_artifacts(tmp_path)
    manager.close()


def test_stale_sheet_image_never_enters_current_cache():
    host = SimpleNamespace(_sheet_preview_revision=9, _sheet_preview_paths={})
    image = QImage(10, 10, QImage.Format.Format_ARGB32)
    image.fill(QColor("red"))
    MainWindow._on_sheet_preview_ready(host, 0, 0, image, 8)
    assert host._sheet_preview_paths == {}


def test_maintenance_expires_idle_authorizations_and_detects_suspend(monkeypatch):
    sessions = Mock()
    host = SimpleNamespace(_fornax_sessions=sessions, _session_clock_sample=(100, 1000))
    monkeypatch.setattr("features.workspace.main_window.time.monotonic", lambda: 101)
    monkeypatch.setattr("features.workspace.main_window.time.time", lambda: 1001)
    MainWindow._maintain_fornax_sessions(host)
    sessions.expire_due.assert_called_once()
    sessions.suspend.assert_not_called()
    monkeypatch.setattr("features.workspace.main_window.time.time", lambda: 1601)
    MainWindow._maintain_fornax_sessions(host)
    sessions.suspend.assert_called_once()


def test_abrupt_process_exit_leaves_only_encrypted_model_and_recovery(tmp_path):
    import os
    import subprocess
    import sys
    code = """
import os, sys
from pathlib import Path
from tests.test_fornax_data_lifecycle import protected_model
from features.editor.editor_window import EditorWindow
from features.editor.canvas_items import ImageItem, BackgroundItem, SignatureItem
from core.fornax_container import FULL_MODE
root = Path(sys.argv[1])
path, manager, status, _ = protected_model(root)
window = EditorWindow()
window.load_from_fornax(manager.document(), path=path, mode=FULL_MODE,
    model_id=status.descriptor.model_id, asset_provider=manager.asset,
    session_manager=manager)
item = next(i for i in window.scene.items()
    if isinstance(i, (ImageItem, SignatureItem)) and not isinstance(i, BackgroundItem))
item.setPos(23, 14)
window._write_fornax_recovery()
os._exit(17)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True, timeout=30,
    )
    assert completed.returncode == 17, completed.stderr.decode()
    assert MARKER.encode() not in completed.stdout + completed.stderr
    assert_no_cleartext_artifacts(tmp_path)
    recovery = EditorWindow.fornax_recovery_path(tmp_path / "model.fornax")
    assert recovery.exists()
    from core.fornax_container import unlock_fornax
    assert unlock_fornax(recovery, PASSWORD).document()["pages"][0]["images"][0]["x"] == 23


def test_oversized_local_message_is_disconnected_without_opening_files():
    from core.app_instance import ApplicationInstance, MAX_MESSAGE_BYTES
    receiver = ApplicationInstance()
    received = []
    receiver.filesReceived.connect(received.append)
    socket = Mock()
    socket.bytesAvailable.return_value = MAX_MESSAGE_BYTES + 1
    receiver._read_client(socket)
    socket.abort.assert_called_once()
    assert received == []


def test_generation_releases_all_protected_renderers_after_final_output(tmp_path):
    from PySide6.QtTest import QTest
    from features.generator.manager import RenderManager
    from core.fornax_container import FornaxError
    root = tmp_path / "library"
    root.mkdir()
    path, sessions, status, expected = protected_model(root)
    snapshot = sessions.borrow_job()
    output = tmp_path / "authorized-output"
    output.mkdir()
    manager = RenderManager(
        renderers_for_document(snapshot.document(), asset_provider=snapshot.asset),
        [{}], [{}], output, "result", authorized_snapshot=snapshot,
        protected_content=True,
    )
    done, errors, logs = [], [], []
    manager.finished_process.connect(lambda: done.append(True))
    manager.error_occurred.connect(errors.append)
    manager.log_updated.connect(logs.append)
    try:
        manager.start()
        for _ in range(500):
            if done:
                break
            QTest.qWait(10)
        assert done and not errors, errors
        result = list(output.glob("*.png"))
        assert len(result) == 1
        assert QImage(str(result[0])) == expected
        assert not manager.page_renderers and manager.renderer is None
        assert not manager.rows_plain and not manager.rows_rich
        assert all(not w.renderers for w in manager.workers)
        with pytest.raises(FornaxError):
            snapshot.document()
        assert MARKER not in "\n".join(logs)
        assert_no_cleartext_artifacts(root)
        assert {p.suffix for p in output.iterdir()} == {".png"}
    finally:
        manager.stop()
        sessions.close()


@pytest.mark.parametrize("failure", [False, True])
def test_preview_cancel_or_failure_discards_protected_inputs(tmp_path, monkeypatch, failure):
    path, sessions, status, _ = protected_model(tmp_path)
    snapshot = sessions.borrow_job()
    worker = SheetPreviewWorker(
        snapshot.document(), [({}, {})],
        {"enabled": True, "target_w_mm": 80, "target_h_mm": 50,
         "sheet_w_mm": 100, "sheet_h_mm": 100},
        None, 1, asset_provider=snapshot.asset, memory_only=True,
        authorized_snapshot=snapshot,
    )
    if failure:
        def fail(*args, **kwargs):
            raise RuntimeError("synthetic failure")
        monkeypatch.setattr(
            "features.preview.sheet_preview_worker.renderers_for_document", fail,
        )
    else:
        worker.stop()
    ready = []
    worker.pageReady.connect(lambda *args: ready.append(args))
    worker.run()
    assert not ready
    assert worker.template is None and worker.asset_provider is None
    assert worker.authorized_snapshot is None and not worker.rows
    assert_no_cleartext_artifacts(tmp_path)
    sessions.close()
