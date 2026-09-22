"""Verify W5 inventory and essential files without launching the application."""
import hashlib
import json
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]


def main():
    artifact = ROOT / 'build' / 'main.dist'
    inventory = json.loads((ROOT / 'build/release-inventory/inventory.json').read_text(encoding='utf-8'))
    failures = []
    listed = {entry['path'] for entry in inventory['files']}
    actual = {p.relative_to(artifact).as_posix() for p in artifact.rglob('*') if p.is_file()}
    if actual != listed:
        failures.append('Inventory file set differs from artifact')
    for entry in inventory['files']:
        path = artifact / entry['path']
        if not path.is_file():
            failures.append('Missing: ' + entry['path'])
            continue
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != entry['sha256']:
            failures.append('Hash mismatch: ' + entry['path'])
    for name in listed:
        parts = Path(name).parts
        # Third-party license evidence intentionally preserves upstream paths
        # containing words such as tests/tools. It is not application code.
        license_evidence = name.startswith('docs/licenses/')
        if license_evidence:
            source = ROOT / name
            if not source.is_file() or source.read_bytes() != (artifact / name).read_bytes():
                # Package notices are collected from the build venv, not source.
                if not name.startswith('docs/licenses/packages/'):
                    failures.append('License evidence differs from source: ' + name)
        if not license_evidence and any(p in {'tests', 'history', '__pycache__', '.venv-windows', 'tools'} for p in parts):
            failures.append('Excluded directory shipped: ' + name)
        if Path(name).name.startswith('test_'):
            failures.append('Test shipped: ' + name)
        if Path(name).name.lower() == 'qpdf.dll':
            failures.append('Unused PDF plugin shipped')
    required = [
        'FORNAX_Forge.exe', 'python313.dll', 'LICENSE', 'NOTICE',
        'PySide6/qt-plugins/platforms/qwindows.dll',
        'assets/translations/fornax_en_US.qm',
        'assets/translations/fornax_es_ES.qm',
        'assets/fonts/ui/OFL.txt',
    ]
    for name in required:
        if name not in listed:
            failures.append('Required file absent: ' + name)
    if not any(p.startswith('assets/fonts/ui/') and p.endswith('.ttf') for p in listed):
        failures.append('Embedded UI font absent')
    from defusedxml.ElementTree import parse
    compilation = parse(ROOT / 'build/compilation-report.xml', forbid_dtd=True)
    for module in compilation.findall('.//module'):
        name = module.get('name', '')
        if any(part.startswith('test_') or part in {'tests', 'pytest', '_pytest'} for part in name.split('.')):
            failures.append('Test module included: ' + name)
    executable = (artifact / 'FORNAX_Forge.exe').read_bytes()
    pe_offset = struct.unpack_from('<I', executable, 0x3c)[0]
    machine = struct.unpack_from('<H', executable, pe_offset + 4)[0]
    if executable[pe_offset:pe_offset + 4] != b'PE\0\0' or machine != 0x8664:
        failures.append('Executable is not an AMD64 PE')
    report = {
        'scope': 'Static artifact inspection; no runtime or clean-VM validation',
        'files_verified': len(listed), 'bytes': sum(e['size'] for e in inventory['files']),
        'executable_sha256': hashlib.sha256(executable).hexdigest(),
        'machine': hex(machine), 'failures': failures,
        'distributions': inventory['distributions_confirmed_by_nuitka'],
    }
    (ROOT / 'build/security/windows-w5-static-audit.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8',
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
