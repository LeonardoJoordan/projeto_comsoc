"""Launch native W3 validation without touching production storage or IPC.

Run from the repository with .venv-windows/Scripts/python.exe.
Language restarts reexecute this file and retain the isolated profile.
"""
import hashlib
import os
from pathlib import Path
import sys


REPOSITORY = Path(__file__).resolve().parents[1]
PROFILE = REPOSITORY / 'build' / 'security' / 'windows-w3-profile'


def prepare():
    sys.path.insert(0, str(REPOSITORY))
    os.environ.pop('QT_QPA_PLATFORM', None)
    os.environ.pop('FORNAX_RUN_NATIVE_IPC', None)
    from tests.isolated_environment import activate

    root = activate(PROFILE)
    from core import app_instance

    name = 'fornax-w3-' + hashlib.sha256(str(root).encode()).hexdigest()[:24]
    app_instance._server_name = lambda: name
    return root


if __name__ == '__main__':
    prepare()
    from features.workspace.main import main

    sys.exit(main())
