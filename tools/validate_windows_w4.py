"""Run W4 regressions with Python network attempts denied and recorded.

This guard does not intercept native-library network calls and does not
disconnect Windows. Evidence must not be described as an OS-level offline test.
"""
import json
import os
from pathlib import Path
import sys


def main():
    repository = Path(__file__).resolve().parents[1]
    os.chdir(repository)
    sys.path.insert(0, str(repository))
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    evidence = repository / 'build' / 'security'
    evidence.mkdir(parents=True, exist_ok=True)
    attempts = []

    def deny_network(event, args):
        if event in {'socket.connect', 'socket.getaddrinfo', 'socket.sendto'}:
            # Do not record destination addresses or application payloads.
            attempts.append(event)
            raise RuntimeError('Network disabled for W4 validation')

    sys.addaudithook(deny_network)
    import pytest

    result = pytest.main([
        '--import-mode=importlib', '-q', '-ra',
        '--junitxml=build/security/windows-w4-tests.xml',
        'tests/test_windows_persistence.py',
        'tests/test_fornax_persistence_failures.py',
        'tests/test_fornax_data_lifecycle.py',
        'tests/test_fornax_export.py',
        'tests/test_fornax_import.py',
        'tests/test_fornax_session.py',
        'tests/test_fornax_crypto.py',
        'tests/test_diagnostic_logs.py',
        'tests/test_temp_storage.py',
    ])
    report = {
        'pytest_exit_code': int(result),
        'python_network_attempts': attempts,
        'scope': 'Python audit events in this process only; not OS offline',
    }
    (evidence / 'windows-w4-network.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8',
    )
    return int(result) or bool(attempts)


if __name__ == '__main__':
    sys.exit(main())
