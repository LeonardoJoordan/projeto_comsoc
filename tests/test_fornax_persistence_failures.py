"""Checkpoint 4.3: falhas de persistência e retomada sem perda do original."""
import errno
import json
import os
from pathlib import Path
from unittest.mock import patch
import zipfile

import pytest

from core import fornax_container as container, legacy_migration as migration
from core.file_transactions import file_lock
from core.fornax_import import open_import_package, import_candidate
from core.model_document import save_model_document, UnsupportedSchemaError
from core.model_library import scan_model_library
from tests.test_legacy_migration import _legacy_document

PASSWORD = "persistence-test-2026"


def legacy(tmp_path):
    models = tmp_path / "models"
    source = models / "modelo"
    save_model_document(_legacy_document(), source)
    return models, source


def save(path, name, mode):
    document = _legacy_document(name)
    if mode == container.PUBLIC_MODE:
        return container.save_public_fornax(document, path)
    return container.save_protected_fornax(document, path, PASSWORD, mode=mode)


def read(path, mode):
    if mode == container.PUBLIC_MODE:
        return container.open_public_fornax(path).document()
    return container.unlock_fornax(path, PASSWORD).document()


@pytest.mark.parametrize("mode", [container.PUBLIC_MODE, container.FULL_MODE])
@pytest.mark.parametrize("failure", ["disk_full", "fsync", "backup", "publish"])
def test_failed_save_preserves_last_valid_revision(tmp_path, monkeypatch, mode, failure):
    path = tmp_path / "model.fornax"
    save(path, "original", mode)
    before = path.read_bytes()
    real_replace = os.replace

    def fail(*args, **kwargs):
        raise OSError(errno.ENOSPC if failure == "disk_full" else errno.EACCES, failure)

    def replace(source, target):
        if Path(target) == path:
            fail()
        return real_replace(source, target)

    with monkeypatch.context() as scoped:
        if failure == "disk_full":
            scoped.setattr(zipfile.ZipFile, "writestr", fail)
        elif failure == "fsync":
            scoped.setattr(os, "fsync", fail)
        elif failure == "backup":
            scoped.setattr(container.shutil, "copyfile", fail)
        else:
            scoped.setattr(os, "replace", replace)
        with pytest.raises(OSError):
            save(path, "new", mode)
    assert path.read_bytes() == before
    assert read(path, mode)["name"] == "original"
    assert not list(tmp_path.glob(".*pending*"))
    assert not list(tmp_path.glob(".*backup*"))
    backup = path.with_name(path.name + ".bak")
    if backup.exists():
        if mode == container.PUBLIC_MODE:
            assert backup.read_bytes() == before
        else:
            assert read(backup, mode)["name"] == "new"


@pytest.mark.parametrize("state", ["VERIFIED", "PUBLISHED", "CLEANED"])
@pytest.mark.parametrize("after", [False, True])
def test_migration_resumes_interruption_at_each_journal_transition(tmp_path, state, after):
    models, source = legacy(tmp_path)
    original_write = migration._write_state

    def interrupt(path, journal, next_state):
        if next_state == state:
            if after:
                original_write(path, journal, next_state)
            raise KeyboardInterrupt("power off")
        return original_write(path, journal, next_state)

    with patch.object(migration, "_write_state", side_effect=interrupt):
        with pytest.raises(KeyboardInterrupt):
            migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    migration.resume_legacy_migrations(models)
    if source.exists():  # PREPARED: descarta staging e mantém a origem completa.
        assert not list(models.glob("*.fornax"))
        migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    found = scan_model_library(models)
    assert len(found) == 1 and found[0].kind == "fornax"
    assert read(found[0].path, container.PUBLIC_MODE)["name"] == "Legado"
    assert not source.exists()
    assert not list((tmp_path / "migrations").glob("*.json"))
    assert not list(models.glob(".*migration*"))


def test_cleanup_permission_failure_is_pending_and_retriable(tmp_path, monkeypatch):
    models, source = legacy(tmp_path)
    original_unlink = Path.unlink

    def unlink(path, *args, **kwargs):
        if source in path.parents:
            raise PermissionError("cannot clean legacy")
        return original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "unlink", unlink)
        result = migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    assert not result.cleanup_complete and result.remaining_paths
    assert source.exists()
    assert len(scan_model_library(models)) == 1
    assert not source.exists()


def test_cleanup_does_not_follow_replaced_parent_symlink(tmp_path):
    models, source = legacy(tmp_path)
    nested = source / "assets"
    nested.mkdir()
    (nested / "same.txt").write_text("same contents")
    outside = tmp_path / "outside"
    outside.mkdir()
    foreign = outside / "same.txt"
    foreign.write_text("same contents")
    original_cleanup = migration._cleanup_source

    def swap_then_cleanup(folder, inventory):
        (nested / "same.txt").unlink()
        nested.rmdir()
        nested.symlink_to(outside, target_is_directory=True)
        return original_cleanup(folder, inventory)

    with patch.object(migration, "_cleanup_source", side_effect=swap_then_cleanup):
        result = migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    assert not result.cleanup_complete
    assert foreign.read_text() == "same contents"
    migration.resume_legacy_migrations(models)
    assert foreign.read_text() == "same contents"


@pytest.mark.parametrize("tamper", ["source", "staging", "inventory", "hash", "version"])
def test_invalid_journal_never_authorizes_cleanup(tmp_path, tamper):
    models, source = legacy(tmp_path)
    with patch.object(migration, "_cleanup_source", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    journal_path = next((tmp_path / "migrations").glob("*.json"))
    journal = json.loads(journal_path.read_text())
    original = {path.name: path.read_bytes() for path in source.iterdir()}
    if tamper == "source":
        journal["source"] = "../outside"
    elif tamper == "staging":
        journal["staging"] = "modelo.fornax"
    elif tamper == "inventory":
        journal["source_inventory"][0]["path"] = "../outside"
    elif tamper == "hash":
        journal["package_sha256"] = None
    else:
        journal["version"] = 900
    journal_path.write_text(json.dumps(journal))
    assert migration.resume_legacy_migrations(models) == ()
    assert {path.name: path.read_bytes() for path in source.iterdir()} == original
    assert journal_path.exists()


def test_concurrent_migration_is_rejected_before_any_conversion(tmp_path):
    models, source = legacy(tmp_path)
    with file_lock(tmp_path / "migrations" / ".migration.lock"):
        with pytest.raises(OSError, match="Outra operação"):
            migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    assert source.exists()
    assert not list(models.glob("*.fornax"))


def test_concurrent_destination_is_never_replaced_by_migration(tmp_path):
    models, source = legacy(tmp_path)
    target = models / "modelo.fornax"
    publish = migration.publish_new

    def race(staged, destination):
        destination.write_bytes(b"third party")
        return publish(staged, destination)

    with patch.object(migration, "publish_new", side_effect=race):
        with pytest.raises(FileExistsError):
            migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    assert target.read_bytes() == b"third party"
    assert source.exists()
    migration.resume_legacy_migrations(models)
    assert source.exists() and target.read_bytes() == b"third party"


def test_unknown_legacy_version_is_not_converted(tmp_path):
    models, source = legacy(tmp_path)
    model_json = next(source.glob("*.json"))
    data = json.loads(model_json.read_text())
    data["schema_version"] = 900
    model_json.write_text(json.dumps(data))
    before = model_json.read_bytes()
    with pytest.raises(UnsupportedSchemaError):
        migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    assert model_json.read_bytes() == before
    assert not list(models.glob("*.fornax"))


def test_future_container_is_not_downgraded_to_backup(tmp_path):
    path = tmp_path / "future.fornax"
    save(path, "old", container.PUBLIC_MODE)
    save(path, "new", container.PUBLIC_MODE)
    with zipfile.ZipFile(path) as archive:
        entries = {info.filename: archive.read(info) for info in archive.infolist()}
    manifest = json.loads(entries[container.MANIFEST_PATH])
    manifest["header"]["version"] = 900
    entries[container.MANIFEST_PATH] = json.dumps(manifest).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    before = path.read_bytes()
    assert scan_model_library(tmp_path) == ()
    assert path.read_bytes() == before


def test_corrupt_backup_and_original_are_preserved_for_diagnosis(tmp_path):
    path = tmp_path / "corrupt.fornax"
    backup = path.with_name(path.name + ".bak")
    path.write_bytes(b"bad original")
    backup.write_bytes(b"bad backup")
    assert scan_model_library(tmp_path) == ()
    assert path.read_bytes() == b"bad original"
    assert backup.read_bytes() == b"bad backup"


def test_failed_save_does_not_replace_good_backup_with_corrupt_original(tmp_path):
    path = tmp_path / "model.fornax"
    save(path, "old", container.PUBLIC_MODE)
    save(path, "new", container.PUBLIC_MODE)
    backup = path.with_name(path.name + ".bak")
    before = backup.read_bytes()
    path.write_bytes(b"corrupted")
    with pytest.raises(container.FornaxError):
        save(path, "third", container.PUBLIC_MODE)
    assert backup.read_bytes() == before
    assert scan_model_library(tmp_path)[0].display_name == "old"


def test_import_replacement_requires_consent_and_keeps_backup(tmp_path):
    source = tmp_path / "received.fornax"
    target = tmp_path / "library" / "local.fornax"
    save(source, "received", container.PUBLIC_MODE)
    save(target, "local", container.PUBLIC_MODE)
    before = target.read_bytes()
    with open_import_package(source) as candidates:
        with pytest.raises(container.FornaxError, match="destino já existe"):
            import_candidate(candidates[0], target, include_signatures=False)
        import_candidate(candidates[0], target, include_signatures=False, replace_existing=True)
    assert target.with_name(target.name + ".bak").read_bytes() == before
    assert read(target, container.PUBLIC_MODE)["name"] == "received"


def test_import_never_replaces_received_file_even_with_replace_consent(tmp_path):
    source = tmp_path / "received.fornax"
    save(source, "received", container.PUBLIC_MODE)
    before = source.read_bytes()
    with open_import_package(source) as candidates:
        with pytest.raises(container.FornaxError, match="arquivo recebido"):
            import_candidate(candidates[0], source, include_signatures=False, replace_existing=True)
    assert source.read_bytes() == before


def test_enabling_protection_replaces_public_backup_with_encrypted_revision(tmp_path):
    path = tmp_path / "model.fornax"
    save(path, "SECRET_MARKER_43", container.PUBLIC_MODE)
    save(path, "SECRET_MARKER_43", container.FULL_MODE)
    backup = path.with_name(path.name + ".bak")
    assert container.inspect_fornax(backup).mode == container.FULL_MODE
    assert read(backup, container.FULL_MODE)["name"] == "SECRET_MARKER_43"
    with zipfile.ZipFile(backup) as archive:
        assert container.PUBLIC_DOCUMENT_PATH not in archive.namelist()


def test_password_change_does_not_leave_backup_with_previous_password(tmp_path):
    path = tmp_path / "model.fornax"
    save(path, "old", container.FULL_MODE)
    container.save_protected_fornax(_legacy_document("new"), path, "new-password-2026", mode=container.FULL_MODE)
    backup = path.with_name(path.name + ".bak")
    with pytest.raises(container.FornaxPasswordError):
        container.unlock_fornax(backup, PASSWORD)
    assert container.unlock_fornax(backup, "new-password-2026").document()["name"] == "new"


def test_import_legacy_replacement_is_resumable_after_crash(tmp_path):
    models, source = legacy(tmp_path)
    received = tmp_path / "received.fornax"
    save(received, "received", container.PUBLIC_MODE)
    target = models / "modelo.fornax"
    before = received.read_bytes()
    with open_import_package(received) as candidates:
        with patch.object(migration, "_cleanup_source", side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt):
                import_candidate(candidates[0], target, include_signatures=False,
                                 replace_existing=True, legacy_source=source)
    assert source.exists() and target.exists()
    found = scan_model_library(models)
    assert len(found) == 1 and found[0].display_name == "received"
    assert not source.exists()
    assert received.read_bytes() == before


@pytest.mark.parametrize("error", [errno.ENOSPC, errno.EACCES])
def test_migration_write_failure_keeps_original(tmp_path, monkeypatch, error):
    models, source = legacy(tmp_path)
    before = {path.name: path.read_bytes() for path in source.iterdir()}
    with monkeypatch.context() as scoped:
        def fail(*args, **kwargs):
            raise OSError(error, "injected write failure")
        scoped.setattr(zipfile.ZipFile, "writestr", fail)
        with pytest.raises(OSError):
            migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    assert {path.name: path.read_bytes() for path in source.iterdir()} == before
    assert not list(models.glob("*.fornax"))


def test_source_changed_while_loading_cannot_be_deleted(tmp_path):
    models, source = legacy(tmp_path)
    load = migration.load_model_document

    def change_after_load(folder):
        document = load(folder)
        save_model_document(_legacy_document("changed externally"), folder)
        return document

    with patch.object(migration, "load_model_document", side_effect=change_after_load):
        with pytest.raises(migration.LegacyMigrationError, match="mudou"):
            migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    assert load(source)["name"] == "changed externally"
    assert not list(models.glob("*.fornax"))


@pytest.mark.parametrize("published", [True, False])
def test_corrupted_package_does_not_authorize_legacy_cleanup(tmp_path, published):
    models, source = legacy(tmp_path)
    target_method = "_cleanup_source" if published else "publish_new"
    with patch.object(migration, target_method, side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            migration.migrate_legacy_model(source, models, mode=container.PUBLIC_MODE)
    package = next(models.glob("*.fornax"))
    package.write_bytes(b"corrupted package")
    assert migration.resume_legacy_migrations(models) == ()
    assert source.exists()
    assert list((tmp_path / "migrations").glob("*.json"))


def test_restore_failure_preserves_backup_and_original(tmp_path, monkeypatch):
    path = tmp_path / "model.fornax"
    save(path, "old", container.PUBLIC_MODE)
    save(path, "new", container.PUBLIC_MODE)
    backup = path.with_name(path.name + ".bak")
    before = backup.read_bytes()
    path.write_bytes(b"broken")
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "replace", lambda *args: (_ for _ in ()).throw(PermissionError("read only")))
        assert scan_model_library(tmp_path) == ()
    assert backup.read_bytes() == before
    assert path.read_bytes() == b"broken"
    assert scan_model_library(tmp_path)[0].display_name == "old"


def test_unexpected_concurrent_save_is_not_silently_overwritten(tmp_path):
    path = tmp_path / "model.fornax"
    save(path, "old", container.PUBLIC_MODE)
    alternate = tmp_path / "alternate.fornax"
    save(alternate, "other writer", container.PUBLIC_MODE)
    other_bytes = alternate.read_bytes()
    real_publish = container._publish_package

    def changed_before_publish(destination, entries, verify, **kwargs):
        destination.write_bytes(other_bytes)
        return real_publish(destination, entries, verify, **kwargs)

    with patch.object(container, "_publish_package", side_effect=changed_before_publish):
        with pytest.raises(container.FornaxError, match="mudou"):
            save(path, "ours", container.PUBLIC_MODE)
    assert path.read_bytes() == other_bytes


def test_import_destination_created_during_staging_is_not_replaced(tmp_path):
    received = tmp_path / "received.fornax"
    target = tmp_path / "library" / "new.fornax"
    save(received, "received", container.PUBLIC_MODE)
    from core import fornax_import
    real_save = fornax_import.save_public_fornax

    def race(*args, **kwargs):
        result = real_save(*args, **kwargs)
        target.write_bytes(b"concurrent file")
        return result

    with open_import_package(received) as candidates:
        with patch.object(fornax_import, "save_public_fornax", side_effect=race):
            with pytest.raises(container.FornaxError, match="mudou"):
                import_candidate(candidates[0], target, include_signatures=False)
    assert target.read_bytes() == b"concurrent file"
    assert not list(target.parent.glob(".*import*"))


@pytest.mark.parametrize("signed", [False, True])
def test_legacy_zip_document_uses_transactional_package_import(tmp_path, signed):
    from core.fornax_import import import_legacy_document
    from tests.test_legacy_migration import _image
    source = tmp_path / "extracted"
    source.mkdir()
    signature = source / "signature.png"
    _image(signature)
    document = _legacy_document(signature_path="signature.png" if signed else None)
    save_model_document(document, source)
    original = {p.name: p.read_bytes() for p in source.iterdir()}
    mode = container.SIGNATURES_MODE if signed else container.PUBLIC_MODE
    destination = tmp_path / "library" / "imported.fornax"
    import_legacy_document(document, source, destination, mode=mode,
                           password=PASSWORD if signed else None)
    assert container.inspect_fornax(destination).mode == mode
    assert read(destination, mode)["name"] == "Legado"
    assert {p.name: p.read_bytes() for p in source.iterdir()} == original
    assert len(scan_model_library(destination.parent)) == 1


def test_protected_recovery_write_failure_preserves_previous_snapshot(tmp_path):
    from core.fornax_session import FornaxSessionManager
    path = tmp_path / "model.fornax"
    recovery = tmp_path / "recovery.fornax"
    save(path, "model", container.FULL_MODE)
    sessions = FornaxSessionManager()
    sessions.unlock(path, PASSWORD)
    sessions.write_recovery(_legacy_document("first recovery"), recovery)
    previous = recovery.read_bytes()
    try:
        with patch.object(zipfile.ZipFile, "writestr", side_effect=OSError(errno.ENOSPC, "full")):
            with pytest.raises(OSError):
                sessions.write_recovery(_legacy_document("later recovery"), recovery)
        assert recovery.read_bytes() == previous
        assert sessions.read_recovery(recovery).document()["name"] == "first recovery"
    finally:
        sessions.close()


@pytest.mark.parametrize("future", [True, False])
def test_library_distinguishes_future_public_schema_from_corrupt_document(tmp_path, future):
    from tests.test_fornax_crypto import rewrite_zip
    path = tmp_path / "model.fornax"
    save(path, "old", container.PUBLIC_MODE)
    save(path, "new", container.PUBLIC_MODE)

    def mutate(entries):
        if future:
            document = json.loads(entries[container.PUBLIC_DOCUMENT_PATH])
            document["schema_version"] = 900
            entries[container.PUBLIC_DOCUMENT_PATH] = json.dumps(document).encode()
        else:
            entries[container.PUBLIC_DOCUMENT_PATH] = b"not json"
    rewrite_zip(path, mutate)
    before = path.read_bytes()
    found = scan_model_library(tmp_path)
    if future:
        assert found == () and path.read_bytes() == before
    else:
        assert len(found) == 1 and found[0].display_name == "old"


@pytest.mark.parametrize("mode", [container.SIGNATURES_MODE, container.FULL_MODE])
def test_protected_migration_resumes_after_partial_asset_cleanup(tmp_path, mode):
    from tests.test_legacy_migration import _image
    models, source = legacy(tmp_path)
    _image(source / "signature.png")
    save_model_document(_legacy_document(signature_path="signature.png"), source)

    def partial_cleanup(folder, inventory):
        (folder / "signature.png").unlink()
        raise KeyboardInterrupt("crash during cleanup")

    with patch.object(migration, "_cleanup_source", side_effect=partial_cleanup):
        with pytest.raises(KeyboardInterrupt):
            migration.migrate_legacy_model(source, models, mode=mode, password=PASSWORD)
    migration.resume_legacy_migrations(models)
    target = models / "modelo.fornax"
    opened = container.unlock_fornax(target, PASSWORD)
    signatures = opened.document()["pages"][0]["signatures"]
    assert len(signatures) == 1
    assert opened.asset(signatures[0]["path"])
    assert not source.exists()
    assert len(scan_model_library(models)) == 1


@pytest.mark.parametrize("action", ["rename", "replace"])
def test_legacy_zip_ui_respects_existing_fornax_conflict(tmp_path, monkeypatch, action):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from features.workspace import main_window as workspace
    source = tmp_path / "source"
    save_model_document(_legacy_document("Legado"), source)
    received = tmp_path / "legacy.zip"
    with zipfile.ZipFile(received, "w") as archive:
        for path in source.iterdir():
            archive.write(path, f"remote/{path.name}")
    models = tmp_path / "models"
    original = models / "legado.fornax"
    save(original, "Legado", container.PUBLIC_MODE)
    before_original, before_received = original.read_bytes(), received.read_bytes()
    dialog = Mock()
    dialog.exec.return_value = True
    dialog.get_decisions.return_value = {"Legado": {"import": True, "action": action}}
    monkeypatch.setattr(workspace, "get_models_dir", lambda: models)
    monkeypatch.setattr(workspace, "ImportModelsDialog", Mock(return_value=dialog))
    critical = Mock()
    monkeypatch.setattr(workspace.QMessageBox, "critical", critical)
    monkeypatch.setattr(workspace.QMessageBox, "information", Mock())
    monkeypatch.setattr(workspace.QMessageBox, "warning", Mock())
    host = SimpleNamespace(log_panel=Mock(), _reload_models_from_disk=Mock(),
                           _legacy_migration_credentials=lambda doc: (container.PUBLIC_MODE, None))
    workspace.MainWindow._on_import_legacy_zip(host, str(received))
    critical.assert_not_called()
    host._reload_models_from_disk.assert_called_once()
    found = scan_model_library(models)
    assert len(found) == (2 if action == "rename" else 1)
    if action == "rename":
        assert original.read_bytes() == before_original
    else:
        assert original.with_name(original.name + ".bak").read_bytes() == before_original
    assert received.read_bytes() == before_received


def test_received_legacy_cannot_import_unrelated_local_asset(tmp_path):
    from core.fornax_import import import_legacy_document
    from tests.test_legacy_migration import _image
    source = tmp_path / "extracted"
    source.mkdir()
    outside = tmp_path / "private.png"
    _image(outside)
    original = outside.read_bytes()
    target = tmp_path / "library" / "model.fornax"
    with pytest.raises(container.FornaxError, match="fora da pasta"):
        import_legacy_document(_legacy_document(image_path=str(outside)), source, target)
    assert outside.read_bytes() == original and not target.exists()
