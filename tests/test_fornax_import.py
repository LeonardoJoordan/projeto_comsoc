"""Contratos da incorporação de pacotes recebidos à biblioteca local."""

from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from core.fornax_container import (
    FULL_MODE,
    PUBLIC_MODE,
    SIGNATURES_MODE,
    FornaxError,
    inspect_fornax,
    open_public_fornax,
    save_protected_fornax,
    save_public_fornax,
    unlock_fornax,
)
from core.fornax_import import import_candidate, import_legacy_document, open_import_package
from core.model_document import document_signatures
from tests.test_fornax_crypto import FIXTURE_DIR, PASSWORD, protected_document
from tests.test_fornax_export import (
    acknowledged_public_signature_document,
    signature_free_document,
)


TRANSPORT_PASSWORD = "Senha do pacote recebido 2026"
LOCAL_PASSWORD = "Nova senha local 2026"


def test_public_import_creates_new_local_identity_and_preserves_received_file(tmp_path):
    received = tmp_path / "received.fornax"
    remote = save_public_fornax(
        signature_free_document(), received, source_dir=FIXTURE_DIR,
    )
    before = received.read_bytes()
    destination = tmp_path / "library" / "modelo.fornax"

    with open_import_package(received) as candidates:
        imported = import_candidate(
            candidates[0], destination, include_signatures=False,
        )

    assert imported.mode == PUBLIC_MODE
    assert imported.model_id != remote.model_id
    assert received.read_bytes() == before
    assert open_public_fornax(destination).document()["origin_info"]["source"] == "imported"


def test_public_v2_import_requires_fresh_local_decision(tmp_path):
    received = tmp_path / "signed-public.fornax"
    save_public_fornax(
        acknowledged_public_signature_document(), received, source_dir=FIXTURE_DIR,
    )
    destination = tmp_path / "library" / "modelo.fornax"

    with open_import_package(received) as candidates:
        with pytest.raises(FornaxError, match="aceite local"):
            import_candidate(
                candidates[0], destination, include_signatures=True,
                target_mode=PUBLIC_MODE,
            )
        imported = import_candidate(
            candidates[0], destination, include_signatures=True,
            target_mode=PUBLIC_MODE, public_signatures_acknowledged=True,
        )

    restored = open_public_fornax(destination).document()
    assert imported.version == 2
    assert len(document_signatures(restored)) == 2
    assert restored["protection_preferences"]["public_signatures_acknowledged"] is True


def test_public_v2_import_can_remove_or_protect_signatures(tmp_path):
    received = tmp_path / "signed-public.fornax"
    save_public_fornax(
        acknowledged_public_signature_document(), received, source_dir=FIXTURE_DIR,
    )
    without = tmp_path / "library" / "without.fornax"
    protected = tmp_path / "library" / "protected.fornax"

    with open_import_package(received) as candidates:
        candidate = candidates[0]
        removed = import_candidate(
            candidate, without, include_signatures=False, target_mode=PUBLIC_MODE,
        )
        secured = import_candidate(
            candidate, protected, include_signatures=True,
            target_mode=SIGNATURES_MODE, local_password=LOCAL_PASSWORD,
        )

    assert removed.version == 1
    assert document_signatures(open_public_fornax(without).document()) == []
    assert secured.mode == SIGNATURES_MODE
    assert len(document_signatures(unlock_fornax(protected, LOCAL_PASSWORD).document())) == 2


@pytest.mark.parametrize("include_signatures", [True, False])
def test_legacy_public_import_keeps_signature_choice_independent_from_mode(
    tmp_path, include_signatures,
):
    destination = tmp_path / "library" / "legacy.fornax"
    descriptor = import_legacy_document(
        protected_document(), FIXTURE_DIR, destination,
        mode=PUBLIC_MODE, include_signatures=include_signatures,
        public_signatures_acknowledged=include_signatures,
    )
    restored = open_public_fornax(destination).document()

    assert descriptor.version == (2 if include_signatures else 1)
    assert bool(document_signatures(restored)) is include_signatures


def test_partial_import_without_signatures_does_not_require_transport_password(tmp_path):
    received = tmp_path / "partial.fornax"
    save_protected_fornax(
        protected_document(), received, TRANSPORT_PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    before = received.read_bytes()
    destination = tmp_path / "library" / "public.fornax"

    with open_import_package(received) as candidates:
        import_candidate(candidates[0], destination, include_signatures=False)

    assert inspect_fornax(destination).mode == PUBLIC_MODE
    assert document_signatures(open_public_fornax(destination).document()) == []
    with zipfile.ZipFile(destination) as archive:
        assert "protected.bin" not in archive.namelist()
    assert received.read_bytes() == before


def test_signature_choice_and_target_protection_are_independent(tmp_path):
    received = tmp_path / "partial.fornax"
    save_protected_fornax(
        protected_document(), received, TRANSPORT_PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    destination = tmp_path / "library" / "full-without-signatures.fornax"

    with open_import_package(received) as candidates:
        imported = import_candidate(
            candidates[0], destination, include_signatures=False,
            target_mode=FULL_MODE, local_password=LOCAL_PASSWORD,
        )

    assert imported.mode == FULL_MODE
    restored = unlock_fornax(destination, LOCAL_PASSWORD).document()
    assert document_signatures(restored) == []


def test_signature_only_target_rejects_content_without_signatures(tmp_path):
    received = tmp_path / "public.fornax"
    save_public_fornax(signature_free_document(), received, source_dir=FIXTURE_DIR)
    destination = tmp_path / "library" / "invalid.fornax"

    with open_import_package(received) as candidates:
        with pytest.raises(FornaxError, match="ao menos uma assinatura"):
            import_candidate(
                candidates[0], destination, include_signatures=False,
                target_mode=SIGNATURES_MODE, local_password=LOCAL_PASSWORD,
            )
    assert not destination.exists()


@pytest.mark.parametrize("mode", [SIGNATURES_MODE, FULL_MODE])
def test_protected_import_replaces_transport_password_with_local_password(tmp_path, mode):
    received = tmp_path / f"{mode}.fornax"
    remote = save_protected_fornax(
        protected_document(), received, TRANSPORT_PASSWORD,
        mode=mode, source_dir=FIXTURE_DIR,
    )
    destination = tmp_path / "library" / f"local-{mode}.fornax"

    with open_import_package(received) as candidates:
        imported = import_candidate(
            candidates[0], destination, include_signatures=True,
            transport_password=TRANSPORT_PASSWORD,
            local_password=LOCAL_PASSWORD,
        )

    assert imported.mode == mode
    assert imported.model_id != remote.model_id
    assert imported.salt != remote.salt
    with pytest.raises(FornaxError):
        unlock_fornax(destination, TRANSPORT_PASSWORD)
    assert len(document_signatures(unlock_fornax(destination, LOCAL_PASSWORD).document())) == 2


def test_full_import_without_signatures_still_requires_transport_unlock(tmp_path):
    received = tmp_path / "full.fornax"
    save_protected_fornax(
        protected_document(), received, TRANSPORT_PASSWORD,
        mode=FULL_MODE, source_dir=FIXTURE_DIR,
    )
    destination = tmp_path / "library" / "public.fornax"

    with open_import_package(received) as candidates:
        with pytest.raises(FornaxError):
            import_candidate(candidates[0], destination, include_signatures=False)
        assert not destination.exists()
        import_candidate(
            candidates[0], destination, include_signatures=False,
            transport_password=TRANSPORT_PASSWORD,
        )

    assert inspect_fornax(destination).mode == PUBLIC_MODE
    assert document_signatures(open_public_fornax(destination).document()) == []


def test_mixed_batch_is_read_without_extractall_and_imported_independently(tmp_path):
    public = tmp_path / "public.fornax"
    partial = tmp_path / "partial.fornax"
    save_public_fornax(signature_free_document(), public, source_dir=FIXTURE_DIR)
    save_protected_fornax(
        protected_document(), partial, TRANSPORT_PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    batch = tmp_path / "batch.zip"
    with zipfile.ZipFile(batch, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(public, "public.fornax")
        archive.write(partial, "partial.fornax")
    before = batch.read_bytes()

    with open_import_package(batch) as candidates:
        assert {candidate.descriptor.mode for candidate in candidates} == {
            PUBLIC_MODE, SIGNATURES_MODE,
        }
        for index, candidate in enumerate(candidates):
            protected = candidate.descriptor.mode != PUBLIC_MODE
            import_candidate(
                candidate, tmp_path / "library" / f"model-{index}.fornax",
                include_signatures=protected,
                transport_password=TRANSPORT_PASSWORD if protected else None,
                local_password=LOCAL_PASSWORD if protected else None,
            )

    assert len(list((tmp_path / "library").glob("*.fornax"))) == 2
    assert batch.read_bytes() == before


@pytest.mark.parametrize("entry", ["../escape.fornax", "/absolute.fornax", "dir/model.fornax", "bad.txt"])
def test_batch_rejects_unsafe_or_non_model_entries(tmp_path, entry):
    batch = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(batch, "w") as archive:
        archive.writestr(entry, b"invalid")
    with pytest.raises(FornaxError):
        with open_import_package(batch):
            pass


def test_wrong_password_publishes_nothing_and_received_file_is_unchanged(tmp_path):
    received = tmp_path / "partial.fornax"
    save_protected_fornax(
        protected_document(), received, TRANSPORT_PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    before = received.read_bytes()
    destination = tmp_path / "library" / "failed.fornax"

    with open_import_package(received) as candidates:
        with pytest.raises(FornaxError):
            import_candidate(
                candidates[0], destination, include_signatures=True,
                transport_password="Senha incorreta válida",
                local_password=LOCAL_PASSWORD,
            )

    assert not destination.exists()
    assert received.read_bytes() == before
