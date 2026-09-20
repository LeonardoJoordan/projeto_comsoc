"""Contratos de sessão, expiração e snapshots autorizados do .fornax."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.fornax_container import (
    FULL_MODE,
    SIGNATURES_MODE,
    FornaxFormatError,
    FornaxOperationCancelled,
    FornaxPasswordError,
    save_protected_fornax,
    save_public_fornax,
)
from core.fornax_container import _KDF_LOCK, _derive_kek
from core.fornax_session import (
    SIGNATURE_FREE_LABEL,
    AccessState,
    FornaxExternalChangeError,
    FornaxSessionManager,
)
from core.model_document import document_signatures, load_model_document, persistent_model_document


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "fornax_stage1"
PASSWORD = "Frase segura de sessão 2026"


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def source_document(*, signatures=True):
    document = load_model_document(FIXTURE_DIR / "template_v4.json")
    for page in document["pages"]:
        missing = {
            item["object_id"] for item in page["images"]
            if item.get("path") == "assets/intentionally-missing.png"
        }
        page["images"] = [
            item for item in page["images"]
            if item.get("path") != "assets/intentionally-missing.png"
        ]
        page["layer_order"] = [item for item in page["layer_order"] if item not in missing]
        if not signatures:
            signature_ids = {item["object_id"] for item in page["signatures"]}
            page["signatures"] = []
            page["layer_order"] = [
                item for item in page["layer_order"] if item not in signature_ids
            ]
    return persistent_model_document(document)


@pytest.fixture
def packages(tmp_path):
    partial = tmp_path / "partial.fornax"
    full = tmp_path / "full.fornax"
    public = tmp_path / "public.fornax"
    save_protected_fornax(
        source_document(), partial, PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    save_protected_fornax(
        source_document(), full, PASSWORD,
        mode=FULL_MODE, source_dir=FIXTURE_DIR,
    )
    save_public_fornax(source_document(signatures=False), public, source_dir=FIXTURE_DIR)
    return partial, full, public


def test_active_model_never_expires_and_return_before_deadline_reuses_access(packages):
    partial, _, public = packages
    clock = FakeClock()
    manager = FornaxSessionManager(clock=clock)

    assert manager.select(partial).state == AccessState.LOCKED
    assert manager.unlock(partial, PASSWORD).state == AccessState.AUTHORIZED_ACTIVE
    clock.advance(10_000)
    assert manager.status(partial).state == AccessState.AUTHORIZED_ACTIVE

    manager.select(public)
    grace = manager.status(partial)
    assert grace.state == AccessState.GRACE
    assert grace.grace_remaining == pytest.approx(300.0)
    clock.advance(299.9)
    assert manager.select(partial).state == AccessState.AUTHORIZED_ACTIVE
    assert len(document_signatures(manager.document())) == 2


def test_leaving_again_restarts_five_minutes_and_exact_deadline_expires(packages):
    partial, _, public = packages
    clock = FakeClock()
    manager = FornaxSessionManager(clock=clock)
    manager.unlock(partial, PASSWORD)
    manager.select(public)
    clock.advance(200)
    manager.select(partial)
    manager.select(public)
    clock.advance(299)
    assert manager.status(partial).grace_remaining == pytest.approx(1.0)
    clock.advance(1)
    expired = manager.expire_due()
    assert [item.model_id for item in expired]
    status = manager.select(partial)
    assert status.state == AccessState.EXPIRED
    assert status.requires_password is True
    assert status.can_open_without_signatures is True
    with pytest.raises(FornaxPasswordError):
        manager.document()


def test_suspend_invalidates_grace_but_not_active_model(packages):
    partial, full, _ = packages
    manager = FornaxSessionManager(clock=FakeClock())
    manager.unlock(partial, PASSWORD)
    manager.unlock(full, PASSWORD)
    assert manager.status(partial).state == AccessState.GRACE

    manager.suspend()
    assert manager.status(partial).state == AccessState.EXPIRED
    assert manager.status(full).state == AccessState.AUTHORIZED_ACTIVE


def test_signature_free_copy_has_exact_notice_and_requires_save_as(packages):
    partial, full, _ = packages
    manager = FornaxSessionManager()
    status = manager.open_without_signatures(partial)

    assert status.state == AccessState.SIGNATURE_FREE_COPY
    assert status.notice == SIGNATURE_FREE_LABEL
    assert status.save_as_required is True
    assert document_signatures(manager.document()) == []
    with pytest.raises(FornaxPasswordError, match="integral"):
        manager.open_without_signatures(full)


def test_temporary_flag_is_exposed_without_persisting_any_registration(packages):
    partial, _, _ = packages
    manager = FornaxSessionManager()
    status = manager.unlock(partial, PASSWORD, temporary=True)
    assert status.temporary is True
    manager.close()
    with pytest.raises(FornaxFormatError, match="encerrado"):
        manager.status(partial)


def test_external_change_invalidates_ui_access_and_requires_explicit_reload(packages):
    partial, _, _ = packages
    manager = FornaxSessionManager()
    manager.unlock(partial, PASSWORD)
    token = manager.issue_token()
    with partial.open("ab") as stream:
        stream.write(b"external-change")

    assert manager.check_external_change(partial) is True
    status = manager.status(partial)
    assert status.state == AccessState.EXTERNAL_CHANGED
    assert status.requires_password is True
    assert manager.token_is_current(token) is False
    with pytest.raises(FornaxPasswordError):
        manager.document()
    assert manager.reload(partial).state == AccessState.LOCKED


def test_authorized_job_survives_ui_expiration_without_renewing_it(packages):
    partial, _, public = packages
    clock = FakeClock()
    manager = FornaxSessionManager(clock=clock)
    manager.unlock(partial, PASSWORD)
    job = manager.borrow_job()
    references = job.asset_references
    assert references
    assert not hasattr(job, "kek")

    manager.select(public)
    clock.advance(300)
    manager.expire_due()
    assert manager.status(partial).state == AccessState.EXPIRED
    assert len(document_signatures(job.document())) == 2
    assert job.asset(references[0])
    assert manager.status(partial).state == AccessState.EXPIRED

    job.close()
    with pytest.raises(FornaxFormatError, match="encerrado"):
        job.document()


def test_preview_token_is_invalidated_by_switch_and_reactivation(packages):
    partial, _, public = packages
    manager = FornaxSessionManager()
    manager.unlock(partial, PASSWORD)
    token = manager.issue_token()
    assert manager.token_is_current(token) is True
    manager.select(public)
    assert manager.token_is_current(token) is False
    manager.select(partial)
    assert manager.token_is_current(token) is False
    assert manager.token_is_current(manager.issue_token()) is True


def test_close_discards_authorization_material(packages):
    partial, _, _ = packages
    manager = FornaxSessionManager()
    manager.unlock(partial, PASSWORD)
    internal = manager._sessions[partial.resolve()]
    retained_key = internal.kek
    assert retained_key and any(retained_key)

    manager.close()
    assert internal.kek is None
    assert retained_key is not None and not any(retained_key)
    assert internal.opened is None


def test_forget_discards_authorization_for_removed_library_entry(packages):
    partial, _, _ = packages
    manager = FornaxSessionManager()
    manager.unlock(partial, PASSWORD)
    internal = manager._sessions[partial.resolve()]
    retained_key = internal.kek

    manager.forget(partial)

    assert internal.state == AccessState.CLOSED
    assert internal.kek is None
    assert retained_key is not None and not any(retained_key)
    with pytest.raises(FornaxFormatError, match="ainda não possui sessão"):
        manager.status(partial)


def test_authorized_save_reuses_session_key_and_publishes_new_revision(packages, monkeypatch):
    partial, _, _ = packages
    manager = FornaxSessionManager()
    original = manager.unlock(partial, PASSWORD)
    document = manager.document()
    document["name"] = "Revisão autorizada"
    monkeypatch.setattr(
        "core.fornax_container._derive_kek",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("KDF repetida")),
    )

    saved = manager.save(document, path=partial)

    assert saved.state == AccessState.AUTHORIZED_ACTIVE
    assert saved.descriptor.model_id == original.descriptor.model_id
    assert saved.descriptor.revision_id != original.descriptor.revision_id
    assert manager.document()["name"] == "Revisão autorizada"
    assert partial.with_name(partial.name + ".bak").is_file()


def test_protected_recovery_uses_same_access_scope_without_touching_original(packages):
    partial, _, _ = packages
    original_bytes = partial.read_bytes()
    manager = FornaxSessionManager()
    manager.unlock(partial, PASSWORD)
    document = manager.document()
    document["name"] = "Trabalho ainda não salvo"
    recovery = partial.with_name(f".{partial.name}.autosave.fornax")

    descriptor = manager.write_recovery(document, recovery, path=partial)
    opened = manager.read_recovery(recovery, path=partial)

    assert descriptor.mode == SIGNATURES_MODE
    assert opened.document()["name"] == "Trabalho ainda não salvo"
    assert partial.read_bytes() == original_bytes


def test_save_never_overwrites_file_changed_outside_editor(packages):
    partial, _, _ = packages
    manager = FornaxSessionManager()
    manager.unlock(partial, PASSWORD)
    document = manager.document()
    with partial.open("ab") as stream:
        stream.write(b"external-change")
    changed_bytes = partial.read_bytes()

    with pytest.raises(FornaxExternalChangeError):
        manager.save(document, path=partial)

    assert partial.read_bytes() == changed_bytes
    assert manager.status(partial).state == AccessState.EXTERNAL_CHANGED


def test_authorized_session_can_remove_last_signature_and_drop_protection(packages):
    partial, _, _ = packages
    manager = FornaxSessionManager()
    manager.unlock(partial, PASSWORD)
    internal = manager._sessions[partial.resolve()]
    retained_key = internal.kek
    document = manager.document()
    for page in document["pages"]:
        signature_ids = {item["object_id"] for item in page["signatures"]}
        page["signatures"] = []
        page["layer_order"] = [
            object_id for object_id in page["layer_order"]
            if object_id not in signature_ids
        ]

    saved = manager.save(document, path=partial, mode="none")

    assert saved.state == AccessState.PUBLIC_ACTIVE
    assert saved.descriptor.mode == "none"
    assert retained_key is not None and not any(retained_key)
    assert document_signatures(manager.document()) == []


def test_waiting_kdf_can_be_cancelled_before_expensive_derivation():
    assert _KDF_LOCK.acquire(timeout=1)
    try:
        with pytest.raises(FornaxOperationCancelled, match="cancelado"):
            _derive_kek(
                PASSWORD, bytes(range(16)), cancel_check=lambda: True,
            )
    finally:
        _KDF_LOCK.release()
