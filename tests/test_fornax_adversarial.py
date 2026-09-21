"""Revisão 4.1: adulteração criptográfica e entradas hostis."""
import json
import os
import zipfile
from uuid import uuid4

import pytest

from core import fornax_container as container
from core import fornax_import as importing
from core.fornax_export import ExportRequest, export_models
from tests.test_fornax_crypto import FIXTURE_DIR, PASSWORD, protected_document, rewrite_zip


@pytest.fixture
def protected(tmp_path):
    path = tmp_path / "protected.fornax"
    container.save_protected_fornax(
        protected_document(), path, PASSWORD,
        mode=container.SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    return path


@pytest.mark.parametrize("field", [
    "model_id", "revision_id", "salt", "wrap_nonce", "payload_nonce",
    "crypto_profile", "mode", "version",
])
def test_header_mutation_never_releases_protected_content(protected, field):
    def mutate(entries):
        manifest = json.loads(entries["manifest.json"])
        header = manifest["header"]
        if field.endswith("_id"):
            header[field] = str(uuid4())
        elif field in {"salt", "wrap_nonce", "payload_nonce"}:
            header[field] = ("00" if header[field][:2] != "00" else "01") + header[field][2:]
        elif field == "crypto_profile":
            header[field] = "weaker-profile"
        elif field == "mode":
            header[field] = "none"
        else:
            header[field] = 2
        entries["manifest.json"] = json.dumps(manifest).encode()
    rewrite_zip(protected, mutate)
    with pytest.raises(container.FornaxError):
        container.unlock_fornax(protected, PASSWORD)


@pytest.mark.parametrize("mode", [[], {}, None, 7])
def test_malformed_mode_is_controlled_error(protected, mode):
    def mutate(entries):
        manifest = json.loads(entries["manifest.json"])
        manifest["header"]["mode"] = mode
        entries["manifest.json"] = json.dumps(manifest).encode()
    rewrite_zip(protected, mutate)
    with pytest.raises(container.FornaxError):
        container.inspect_fornax(protected)


def test_extreme_json_depth_is_controlled_error():
    with pytest.raises(container.FornaxError):
        container._strict_json(b"[" * 2000 + b"0" + b"]" * 2000, label="test")


@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink"])
def test_export_cannot_replace_original_through_alias(protected, tmp_path, alias):
    before = protected.read_bytes()
    destination = protected
    if alias != "same":
        destination = tmp_path / "alias.fornax"
        if alias == "symlink":
            try:
                destination.symlink_to(protected)
            except OSError as exc:
                if getattr(exc, "winerror", None) == 1314:
                    pytest.skip("Windows account lacks the symbolic-link privilege")
                raise
        else:
            os.link(protected, destination)
    with pytest.raises(container.FornaxError, match="sobrescrever"):
        export_models(
            [ExportRequest(protected, "Template")], destination,
            include_signatures=False,
        )
    assert protected.read_bytes() == before


def test_export_rejects_snapshot_from_other_model(protected, tmp_path):
    other = tmp_path / "other.fornax"
    container.save_protected_fornax(
        protected_document(), other, PASSWORD,
        mode=container.SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    target = tmp_path / "export.fornax"
    with pytest.raises(container.FornaxError, match="outro modelo"):
        export_models(
            [ExportRequest(protected, "Template", PASSWORD,
                           opened=container.unlock_fornax(other, PASSWORD))],
            target, include_signatures=True, transport_password=PASSWORD,
        )
    assert not target.exists()


@pytest.mark.parametrize("name", ["./a.fornax", "C:a.fornax", "a:stream.fornax", "a\n.fornax"])
def test_batch_rejects_noncanonical_paths(name):
    with pytest.raises(container.FornaxError):
        importing._validate_batch_member(zipfile.ZipInfo(name), set())


def test_batch_validates_all_sizes_before_copying(tmp_path, monkeypatch):
    batch = tmp_path / "batch.zip"
    with zipfile.ZipFile(batch, "w") as archive:
        archive.writestr("first.fornax", b"small")
        archive.writestr("oversized.fornax", b"x" * 128)
    monkeypatch.setattr(importing, "MAX_PACKAGE_BYTES", 64)
    def unexpected(*args):
        pytest.fail("A candidate was processed before inventory validation")
    monkeypatch.setattr(importing, "_candidate", unexpected)
    with pytest.raises(container.FornaxError, match="512 MiB"):
        with importing.open_import_package(batch):
            pass


@pytest.mark.parametrize("body", [
    '<style>@import "https://example.invalid/style";</style>',
    '<rect style="fill:url(file:///tmp/private.svg)"/>',
    '<rect fill="url(https://example.invalid/image)"/>',
    '<x:script xmlns:x="http://www.w3.org/2000/svg">alert(1)</x:script>',
    '<rect onload="alert(1)"/>',
    '<style>rect {fill:u\\72l(https://example.invalid/image)}</style>',
])
def test_svg_css_and_events_cannot_load_external_resources(body):
    raw = ('<svg xmlns="http://www.w3.org/2000/svg">' + body + '</svg>').encode()
    with pytest.raises(container.FornaxError):
        container._validate_svg(raw, reference="asset.svg")


def test_svg_local_gradient_remains_supported():
    container._validate_svg(
        b'<svg xmlns="http://www.w3.org/2000/svg"><rect fill="url(#gradient)"/></svg>',
        reference="asset.svg",
    )


def test_public_change_requires_explicit_ui_approval(monkeypatch):
    from types import SimpleNamespace
    from PySide6.QtWidgets import QApplication, QMessageBox
    from features.workspace.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    calls = []
    def decline(*args):
        calls.append(args)
        return QMessageBox.StandardButton.Cancel
    monkeypatch.setattr(QMessageBox, "warning", decline)
    assert MainWindow._approve_shared_model(None, SimpleNamespace(public_changed=False))
    assert not MainWindow._approve_shared_model(None, SimpleNamespace(public_changed=True))
    assert len(calls) == 1


def test_cancelled_public_change_does_not_leave_grace_authorization(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from PySide6.QtWidgets import QApplication, QMessageBox
    from core.fornax_session import AccessState
    from features.workspace.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    sessions = Mock()
    sessions.select.return_value = SimpleNamespace(
        state=AccessState.LOCKED, descriptor=SimpleNamespace(mode=container.FULL_MODE),
    )
    sessions.unlock.return_value = SimpleNamespace(public_changed=True)
    host = SimpleNamespace(
        _fornax_sessions=sessions,
        _request_fornax_password=lambda _: PASSWORD,
        _current_library_entry=lambda: model,
        _on_model_changed=Mock(),
        preview_panel=SimpleNamespace(cbo_models=SimpleNamespace(currentText=lambda: "Modelo")),
    )
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Cancel)
    model = SimpleNamespace(
        path=tmp_path / "model.fornax", is_fornax=True,
        descriptor=SimpleNamespace(mode=container.FULL_MODE),
    )
    MainWindow._unlock_selected_model(host)
    sessions.forget.assert_called_once_with(model.path)
    host._on_model_changed.assert_called_once_with("Modelo")
    sessions.document.assert_not_called()


def test_ciphertext_from_another_model_is_rejected(protected, tmp_path):
    other = tmp_path / "other.fornax"
    container.save_protected_fornax(
        protected_document(), other, PASSWORD,
        mode=container.SIGNATURES_MODE, source_dir=FIXTURE_DIR,
    )
    with zipfile.ZipFile(other) as archive:
        ciphertext = archive.read("protected.bin")
    rewrite_zip(protected, lambda entries: entries.update({"protected.bin": ciphertext}))
    with pytest.raises(container.FornaxPasswordError):
        container.unlock_fornax(protected, PASSWORD)
