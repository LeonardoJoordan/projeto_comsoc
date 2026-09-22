from core import temp_storage
from tests.symlinks import create_symlink


def test_cleanup_removes_only_entries_inside_app_temporary_directory(tmp_path, monkeypatch):
    root = tmp_path / "temporary"
    root.mkdir()
    work = root / "generation-stale"
    work.mkdir()
    (work / "card.png").write_bytes(b"sensitive")
    outside = tmp_path / "keep.txt"
    outside.write_bytes(b"keep")
    monkeypatch.setattr(temp_storage, "get_temp_dir", lambda: root)

    temp_storage.cleanup_stale_workspaces()

    assert not work.exists()
    assert outside.read_bytes() == b"keep"


def test_cleanup_does_not_follow_external_symlink(tmp_path, monkeypatch):
    root = tmp_path / 'temporary'
    root.mkdir()
    outside = tmp_path / 'keep.txt'
    outside.write_bytes(b'keep')
    link = root / 'outside-link'
    create_symlink(link, outside)
    monkeypatch.setattr(temp_storage, 'get_temp_dir', lambda: root)
    temp_storage.cleanup_stale_workspaces()
    assert outside.read_bytes() == b'keep'
    assert not link.exists()
