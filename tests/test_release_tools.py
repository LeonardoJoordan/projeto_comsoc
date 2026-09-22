from pathlib import Path
import json
import pytest
from scripts.release_tools import ROOT, selected_files, stage, inventory


def test_release_selection_excludes_development_and_keeps_legal():
    files={p.relative_to(ROOT).as_posix() for p in selected_files()}
    assert 'features/editor/editor_window.py' in files
    assert 'assets/fonts/ui/OFL.txt' in files
    assert 'docs/licenses/LUCIDE-LICENSE.txt' in files
    assert 'assets/icons/ui/README.pdf' not in files
    assert not any('/test_' in p or '__pycache__' in p or p.endswith('.ts') for p in files)
    assert not any(p.startswith(('history/', '.venv/', 'docs/historico/')) for p in files)


def test_stage_refuses_to_merge_or_follow_resource_symlinks(tmp_path):
    existing=tmp_path/'existing';existing.mkdir();(existing/'keep').write_text('keep')
    with pytest.raises(ValueError):stage(existing)
    assert (existing/'keep').read_text()=='keep'
    fake=tmp_path/'root';fake.mkdir();(fake/'main.py').symlink_to(ROOT/'main.py')
    with pytest.raises(ValueError,match='fora da árvore'):stage(tmp_path/'out', fake)


def test_artifact_inventory_hashes_actual_files_and_separates_environment(tmp_path):
    artifact=tmp_path/'artifact';artifact.mkdir();(artifact/'file').write_bytes(b'abc')
    report=inventory(artifact,tmp_path/'report')
    assert report['files'][0]['sha256']=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    assert report['signed'] is False
    assert report['license_review_complete'] is False
    bom=json.loads((tmp_path/'report/files.cdx.json').read_text())
    assert bom['components'][0]['type']=='file'
    with pytest.raises(ValueError):inventory(artifact,artifact/'report')
    (artifact/'outside').symlink_to(ROOT/'main.py')
    with pytest.raises(ValueError,match='fora do artefato'):inventory(artifact,tmp_path/'report2')


def test_pdf_plugin_removal_keeps_image_formats(tmp_path):
    from scripts.release_tools import remove_unused_pdf_plugin
    folder=tmp_path/'PySide6/qt-plugins/imageformats';folder.mkdir(parents=True)
    for name in ('libqpdf.so','qpdf.dll','libqsvg.so','libqjpeg.so'):
        (folder/name).write_bytes(b'test')
    remove_unused_pdf_plugin(tmp_path)
    assert {p.name for p in folder.iterdir()}=={'libqsvg.so','libqjpeg.so'}
