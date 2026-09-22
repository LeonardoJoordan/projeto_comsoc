"""Real Windows sharing and read-only failures preserve the last valid model."""
import stat
import subprocess
import sys
import time

import pytest

from core import fornax_container as container
from tests.test_fornax_persistence_failures import save, read


pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Windows file semantics')


@pytest.mark.parametrize('mode', [container.PUBLIC_MODE, container.FULL_MODE])
@pytest.mark.parametrize('restriction', ['read_only', 'other_process'])
def test_windows_failed_replacement_preserves_model_and_can_retry(tmp_path, mode, restriction):
    path = tmp_path / 'Modelo com espaço e acentuação.fornax'
    save(path, 'original', mode)
    before = path.read_bytes()
    process = None
    try:
        if restriction == 'read_only':
            path.chmod(stat.S_IREAD)
        else:
            ready = tmp_path / 'reader-ready'
            code = (
                'import sys; from pathlib import Path; '
                'stream = open(sys.argv[1], "rb"); '
                'Path(sys.argv[2]).touch(); sys.stdin.readline(); stream.close()'
            )
            process = subprocess.Popen(
                [sys.executable, '-c', code, str(path), str(ready)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
            )
            deadline = time.monotonic() + 10
            while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            assert ready.exists(), 'The independent reader did not open the model'
        with pytest.raises(OSError):
            save(path, 'replacement', mode)
        assert path.read_bytes() == before
        assert read(path, mode)['name'] == 'original'
        assert not list(tmp_path.glob('.*pending-*'))
        assert not list(tmp_path.glob('.*backup-*'))
    finally:
        path.chmod(stat.S_IREAD | stat.S_IWRITE)
        if process is not None:
            try:
                process.communicate('\n', timeout=10)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=5)
    save(path, 'retry', mode)
    assert read(path, mode)['name'] == 'retry'
