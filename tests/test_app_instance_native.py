"""IPC real entre processos, isolado do socket da instalação do usuário."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHILD = r'''
import json, sys
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QTimer
from core import app_instance
app = QCoreApplication([])
name, action, ready, output = sys.argv[1:5]
app_instance._server_name = lambda: name
instance = app_instance.ApplicationInstance()
if action == 'server':
    ok = instance.listen()
    Path(ready).write_text('ready' if ok else 'failed')
    if not ok:
        sys.exit(2)
    def receive(paths):
        Path(output).write_text(json.dumps(paths))
        instance.close()
        app.quit()
    instance.filesReceived.connect(receive)
    QTimer.singleShot(8000, app.quit)
    app.exec()
    instance.close()
elif action == 'contender':
    ok = instance.listen()
    instance.close()
    sys.exit(1 if ok else 0)
elif action == 'send':
    ok = instance.forward_to_running(json.loads(sys.argv[5]))
    sys.exit(0 if ok else 3)
'''


@pytest.mark.skipif(os.environ.get("FORNAX_RUN_NATIVE_IPC") != "1",
                    reason="IPC real exige FORNAX_RUN_NATIVE_IPC=1 e permissão para sockets locais")
def test_real_ipc_unicode_delivery_and_live_server_is_not_removed(tmp_path):
    # Socket curto para respeitar o limite AF_UNIX.
    import uuid
    name = f"fornax-test-{uuid.uuid4().hex}"
    ready, output = tmp_path / 'ready', tmp_path / 'received.json'
    command = [sys.executable, '-c', CHILD, name]
    process = subprocess.Popen(command + ['server', str(ready), str(output)], cwd=ROOT,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.01)
        assert ready.exists(), process.communicate(timeout=10)
        assert ready.read_text() == 'ready', process.communicate(timeout=10)
        contender = subprocess.run(command + ['contender', str(ready), str(output)],
                                   cwd=ROOT, capture_output=True, text=True, timeout=10)
        assert contender.returncode == 0, contender.stderr
        paths = ['/tmp/Modelo com espaço e ação.fornax', '/tmp/Lote.zip']
        sent = subprocess.run(command + ['send', str(ready), str(output), json.dumps(paths)],
                              cwd=ROOT, capture_output=True, text=True, timeout=10)
        assert sent.returncode == 0, sent.stderr
        _, errors = process.communicate(timeout=10)
        assert process.returncode == 0, errors
        assert json.loads(output.read_text()) == paths
        # O encerramento libera o endpoint para a próxima instância.
        replacement = subprocess.run(command + ['contender', str(ready), str(output)],
                                    cwd=ROOT, capture_output=True, text=True, timeout=10)
        assert replacement.returncode == 1, replacement.stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_restart_is_deferred_until_after_window_close(monkeypatch):
    from features.workspace import frontend
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    launch = Mock()
    monkeypatch.setattr(frontend.QProcess, 'startDetached', launch)
    window = Mock()
    window.close.return_value = True
    frontend._restart_application(window)
    assert app._restart_requested
    launch.assert_not_called()
    window.close.return_value = False
    frontend._restart_application(window)
    assert not app._restart_requested


def test_language_restart_does_not_reopen_imported_files(monkeypatch):
    from features.workspace import frontend
    monkeypatch.delenv('APPIMAGE', raising=False)
    monkeypatch.setattr(frontend.sys, 'argv', [str(ROOT / 'main.py'), '/tmp/received.fornax'])
    launch = Mock(return_value=(True, 123))
    monkeypatch.setattr(frontend.QProcess, 'startDetached', launch)
    assert frontend._launch_restarted_application()
    assert launch.call_args.args[1] == [str(ROOT / 'main.py')]
