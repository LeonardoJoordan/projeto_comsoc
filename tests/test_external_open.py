"""Entrada por associação de arquivo e encaminhamento para a instância ativa."""

from __future__ import annotations

from pathlib import Path
import shutil
from types import SimpleNamespace
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QComboBox

from core.app_instance import ApplicationInstance
from core.fornax_container import inspect_fornax, save_public_fornax
from core.model_document import normalize_model_document
from core.model_library import LibraryModel
from features.workspace.main import _external_arguments
from features.workspace.main_window import MainWindow


APP = QApplication.instance() or QApplication([])


def test_external_arguments_accept_spaces_accents_and_supported_packages(tmp_path):
    model = tmp_path / "Modelo com acentuação e espaço.fornax"
    batch = tmp_path / "Lote de modelos.zip"
    ignored = tmp_path / "texto.txt"

    assert _external_arguments(["fornax", str(model), str(batch), str(ignored)]) == [
        str(model.resolve()), str(batch.resolve()),
    ]


def test_instance_protocol_receives_unicode_paths():
    receiver = ApplicationInstance()
    received = []
    receiver.filesReceived.connect(received.append)
    paths = ["/tmp/Modelo com espaço e ação.fornax"]

    class Socket:
        pending = True

        def bytesAvailable(self):
            return 100

        def canReadLine(self):
            return self.pending

        def readLine(self):
            self.pending = False
            return b'{"files":["/tmp/Modelo com espa\xc3\xa7o e a\xc3\xa7\xc3\xa3o.fornax"]}\n'

    receiver._read_client(Socket())

    assert received == [paths]


def test_instance_ignores_queued_read_after_native_socket_was_deleted():
    receiver = ApplicationInstance()

    class DeletedSocket:
        def __hash__(self):
            return id(self)

        def bytesAvailable(self):
            raise RuntimeError("Internal C++ object already deleted")

    socket = DeletedSocket()
    receiver._clients.add(socket)
    receiver._read_client(socket)
    assert socket not in receiver._clients


def _document(name="Modelo da biblioteca"):
    document = normalize_model_document({
        "name": name,
        "canvas_size": {"w": 100, "h": 60},
        "target_w_mm": 50, "target_h_mm": 30,
        "placeholders": [], "boxes": [], "images": [], "signatures": [],
    })
    document["pages"][0]["layer_order"] = []
    return document


def _external_harness(model):
    combo = QComboBox()
    combo.addItem(model.display_name, model.key)
    messages = []
    harness = SimpleNamespace(
        _library_models_by_key={model.key: model},
        preview_panel=SimpleNamespace(cbo_models=combo),
        log_panel=SimpleNamespace(append=messages.append),
        editor_window=None,
    )
    harness._matching_library_model = lambda source: MainWindow._matching_library_model(
        harness, source
    )
    return harness, messages


def test_opening_library_file_selects_it_without_import_prompt(tmp_path):
    source = tmp_path / "modelo.fornax"
    save_public_fornax(_document(), source)
    descriptor = inspect_fornax(source)
    model = LibraryModel(
        f"fornax:{descriptor.model_id}", "Modelo da biblioteca", source,
        "fornax", descriptor,
    )
    harness, messages = _external_harness(model)

    with patch("features.workspace.main_window.QMessageBox.exec",
               side_effect=AssertionError("não deve perguntar")):
        MainWindow.handle_external_file(harness, source)

    assert messages == ["Modelo já presente na biblioteca: Modelo da biblioteca"]


def test_opening_identical_revision_copy_selects_library_but_new_revision_prompts(tmp_path):
    library = tmp_path / "library.fornax"
    received = tmp_path / "received.fornax"
    save_public_fornax(_document(), library)
    shutil.copyfile(library, received)
    descriptor = inspect_fornax(library)
    model = LibraryModel(
        f"fornax:{descriptor.model_id}", "Modelo da biblioteca", library,
        "fornax", descriptor,
    )
    harness, _messages = _external_harness(model)
    assert MainWindow._matching_library_model(harness, received) is model

    save_public_fornax(
        _document("Revisão recebida"), received, model_id=descriptor.model_id,
    )
    assert MainWindow._matching_library_model(harness, received) is None


def test_windows_upgrade_removes_only_obsolete_pdf_plugin():
    root = Path(__file__).resolve().parents[1]
    installer = (root / 'instalador.iss').read_text(encoding='utf-8')
    section = installer.split('[InstallDelete]', 1)[1].split('[', 1)[0]
    entries = [line.strip() for line in section.splitlines()
               if line.strip() and not line.lstrip().startswith(';')]
    assert entries == [
        'Type: files; Name: "{app}\\PySide6\\qt-plugins\\imageformats\\qpdf.dll"'
    ]


def test_distribution_files_register_fornax_extension():
    root = Path(__file__).resolve().parents[1]
    installer = (root / "instalador.iss").read_text(encoding="utf-8")
    appimage = (root / "script_appimage.sh").read_text(encoding="utf-8")
    flatpak = (root / "com.leobelisario.FornaxForge.yaml").read_text(encoding="utf-8")
    mime = (root / "assets/linux/com.leobelisario.FornaxForge.xml").read_text(encoding="utf-8")
    nuitka = (root / "script_nuitka.py").read_text(encoding="utf-8")

    assert 'Software\\Classes\\.fornax' in installer
    assert '""%1""' in installer
    assert "Exec=FORNAX_Forge %F" in appimage
    assert "application/x-fornax-template" in appimage
    assert "Exec=fornax-forge %F" in flatpak
    assert "assets/linux/com.leobelisario.FornaxForge.xml" in flatpak
    assert '<glob pattern="*.fornax" weight="80"/>' in mime
    assert '<generic-icon name="com.leobelisario.FornaxForge"/>' in mime
    assert '"public.filename-extension": ["fornax"]' in nuitka
