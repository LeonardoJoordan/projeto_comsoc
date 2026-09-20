"""Contratos criptográficos e dos três modos do .fornax v1."""

from __future__ import annotations

import json
from pathlib import Path
import unicodedata
import zipfile

import pytest

from core.fornax_container import (
    FULL_MODE,
    SIGNATURES_MODE,
    FornaxFormatError,
    FornaxPasswordError,
    inspect_fornax,
    open_public_fornax,
    password_bytes,
    reencrypt_fornax,
    save_signature_free_copy,
    save_protected_fornax,
    unlock_fornax,
)
from core.fornax_container import _derive_kek
from core.model_document import document_signatures, load_model_document, persistent_model_document


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "fornax_stage1"
PASSWORD = "Frase segura de teste 2026"
NEW_PASSWORD = "Nova frase segura 2026"


def protected_document():
    document = load_model_document(FIXTURE_DIR / "template_v4.json")
    for page in document["pages"]:
        removed = {
            item["object_id"] for item in page["images"]
            if item.get("path") == "assets/intentionally-missing.png"
        }
        page["images"] = [
            item for item in page["images"]
            if item.get("path") != "assets/intentionally-missing.png"
        ]
        page["layer_order"] = [item for item in page["layer_order"] if item not in removed]
    return persistent_model_document(document)


def rewrite_zip(path: Path, mutate):
    with zipfile.ZipFile(path, "r") as archive:
        entries = {info.filename: archive.read(info) for info in archive.infolist()}
    mutate(entries)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, contents in entries.items():
            archive.writestr(name, contents)


def test_password_contract_normalizes_nfc_and_preserves_spaces():
    assert password_bytes("assinátu") == password_bytes("assina\u0301tu")
    assert password_bytes(" " * 8) == b" " * 8
    assert password_bytes("é" * 64) == unicodedata.normalize("NFC", "é" * 64).encode()
    for invalid in ("a" * 7, "a" * 65):
        with pytest.raises(FornaxPasswordError, match="8 e 64"):
            password_bytes(invalid)


def test_production_kdf_matches_public_stage2_vector():
    assert _derive_kek("Frase pública de teste 2026", bytes(range(16))).hex() == (
        "0c1b99d37d90fb462ec192743e92877df162181a158361b7000b40e1a72de5b3"
    )


def test_signature_mode_exposes_clean_public_copy_and_restores_all_signatures(tmp_path):
    source = protected_document()
    target = tmp_path / "partial.fornax"
    saved = save_protected_fornax(
        source, target, PASSWORD, mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )

    assert inspect_fornax(target).mode == SIGNATURES_MODE
    public = open_public_fornax(target)
    assert document_signatures(public.document()) == []
    assert all("signature" not in reference for reference in public.asset_references)

    with zipfile.ZipFile(target) as archive:
        names = set(archive.namelist())
        document_bytes = archive.read("public/document.json")
        assert "protected.bin" in names
        assert b"Diretor" not in document_bytes
        assert b"Secret" not in document_bytes
        assert b"reference-signature" not in b"".join(archive.read(name) for name in names)

    opened = unlock_fornax(saved, PASSWORD)
    signatures = document_signatures(opened.document())
    assert [item["signature_id"] for item in signatures] == [
        "sig-stage1-visible", "sig-stage1-hidden",
    ]
    assert [item["visible"] for item in signatures] == [True, False]
    assert opened.public_changed is False
    assert all(opened.asset(reference) for reference in opened.asset_references)


def test_full_mode_has_no_public_document_or_assets(tmp_path):
    target = tmp_path / "full.fornax"
    source = protected_document()
    save_protected_fornax(
        source, target, PASSWORD, mode=FULL_MODE, source_dir=FIXTURE_DIR,
    )

    with zipfile.ZipFile(target) as archive:
        assert set(archive.namelist()) == {"manifest.json", "protected.bin"}
        assert b"Diretor" not in archive.read("protected.bin")
    with pytest.raises(FornaxPasswordError, match="exige senha"):
        open_public_fornax(target)
    opened = unlock_fornax(target, PASSWORD)
    assert len(document_signatures(opened.document())) == 2
    assert opened.public_changed is False


@pytest.mark.parametrize("mode", [SIGNATURES_MODE, FULL_MODE])
def test_wrong_password_and_tampered_ciphertext_release_nothing(tmp_path, mode):
    target = tmp_path / f"{mode}.fornax"
    save_protected_fornax(
        protected_document(), target, PASSWORD, mode=mode, source_dir=FIXTURE_DIR,
    )
    with pytest.raises(FornaxPasswordError, match="incorreta|danificado"):
        unlock_fornax(target, "Senha errada mas válida")

    def tamper(entries):
        value = bytearray(entries["protected.bin"])
        value[len(value) // 2] ^= 1
        entries["protected.bin"] = bytes(value)

    rewrite_zip(target, tamper)
    with pytest.raises(FornaxPasswordError, match="incorreta|danificado"):
        unlock_fornax(target, PASSWORD)


def test_tampered_wrapped_key_is_rejected(tmp_path):
    target = tmp_path / "wrap.fornax"
    save_protected_fornax(
        protected_document(), target, PASSWORD, mode=FULL_MODE, source_dir=FIXTURE_DIR,
    )

    def tamper(entries):
        manifest = json.loads(entries["manifest.json"])
        wrapped = manifest["wrapped_key_hex"]
        manifest["wrapped_key_hex"] = ("0" if wrapped[0] != "0" else "1") + wrapped[1:]
        entries["manifest.json"] = json.dumps(manifest).encode()

    rewrite_zip(target, tamper)
    with pytest.raises(FornaxPasswordError, match="incorreta|danificado"):
        unlock_fornax(target, PASSWORD)


def test_valid_public_change_allows_unlock_and_sets_warning_flag(tmp_path):
    target = tmp_path / "changed-public.fornax"
    save_protected_fornax(
        protected_document(), target, PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )

    def change_public(entries):
        document = json.loads(entries["public/document.json"])
        document["name"] = "Conteúdo público alterado externamente"
        entries["public/document.json"] = json.dumps(
            document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode() + b"\n"

    rewrite_zip(target, change_public)
    opened = unlock_fornax(target, PASSWORD)
    assert opened.public_changed is True
    assert opened.document()["name"] == "Conteúdo público alterado externamente"
    assert len(document_signatures(opened.document())) == 2


def test_reencrypt_uses_new_crypto_material_and_can_create_new_identity(tmp_path):
    source = tmp_path / "source.fornax"
    first = save_protected_fornax(
        protected_document(), source, PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    changed_password = tmp_path / "changed-password.fornax"
    second = reencrypt_fornax(source, PASSWORD, changed_password, NEW_PASSWORD)

    assert second.model_id == first.model_id
    assert second.revision_id != first.revision_id
    assert second.salt != first.salt
    assert second.wrap_nonce != first.wrap_nonce
    assert second.payload_nonce != first.payload_nonce
    assert second.wrapped_key != first.wrapped_key
    with pytest.raises(FornaxPasswordError):
        unlock_fornax(changed_password, PASSWORD)
    assert len(document_signatures(unlock_fornax(changed_password, NEW_PASSWORD).document())) == 2

    copied = tmp_path / "copy.fornax"
    third = reencrypt_fornax(
        changed_password, NEW_PASSWORD, copied, NEW_PASSWORD, new_identity=True,
    )
    assert third.model_id != second.model_id
    assert third.salt != second.salt


def test_signature_mode_requires_signature(tmp_path):
    source = protected_document()
    for page in source["pages"]:
        signature_ids = {item["object_id"] for item in page["signatures"]}
        page["signatures"] = []
        page["layer_order"] = [item for item in page["layer_order"] if item not in signature_ids]
    with pytest.raises(FornaxFormatError, match="ao menos uma assinatura"):
        save_protected_fornax(
            source, tmp_path / "invalid.fornax", PASSWORD,
            mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
        )


def test_signature_free_copy_gets_new_identity_and_never_overwrites_original(tmp_path):
    partial = tmp_path / "partial.fornax"
    original = save_protected_fornax(
        protected_document(), partial, PASSWORD,
        mode=SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    original_bytes = partial.read_bytes()
    copied_path = tmp_path / "public-copy.fornax"
    copied = save_signature_free_copy(partial, copied_path)

    assert copied.mode == "none"
    assert copied.model_id != original.model_id
    assert document_signatures(open_public_fornax(copied_path).document()) == []
    assert partial.read_bytes() == original_bytes
    with pytest.raises(FornaxFormatError, match="sobrescrever"):
        save_signature_free_copy(partial, partial)


def test_full_signature_free_copy_requires_valid_password(tmp_path):
    full = tmp_path / "full.fornax"
    save_protected_fornax(
        protected_document(), full, PASSWORD,
        mode=FULL_MODE, source_dir=FIXTURE_DIR,
    )
    with pytest.raises(FornaxPasswordError, match="exige senha"):
        save_signature_free_copy(full, tmp_path / "copy.fornax")
    copied = save_signature_free_copy(
        full, tmp_path / "copy.fornax", password=PASSWORD,
    )
    assert copied.mode == "none"
    opened = open_public_fornax(copied.path)
    assert document_signatures(opened.document()) == []
    with zipfile.ZipFile(copied.path) as archive:
        assert b"reference-signature" not in archive.read("public/document.json")
