"""Examina arquivos versionados e novos não ignorados, sem enviar conteúdo à rede."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def scan(scanner):
    files=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0')
    reports=ROOT/'build/security';reports.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fornax-secret-scan-') as folder:
        destination=Path(folder)
        for raw in files:
            if not raw: continue
            relative=Path(raw.decode('utf-8'))
            source=ROOT/relative
            if source.is_symlink(): raise ValueError(f'Link não examinado: {relative}')
            if not source.is_file(): continue  # arquivo removido no worktree
            target=destination/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
        subprocess.run([str(Path(scanner).resolve()),'dir',str(destination),
                        '--config',str(ROOT/'.gitleaks.toml'),'--redact',
                        '--report-format','json','--report-path',str(reports/'gitleaks-worktree.json')],check=True)

if __name__=='__main__':scan(sys.argv[1])
