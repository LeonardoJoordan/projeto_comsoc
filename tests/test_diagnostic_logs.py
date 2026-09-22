from pathlib import Path

from core import diagnostic_logs


def test_persisted_log_redacts_paths_filenames_and_multiline_details(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnostic_logs, "get_logs_dir", lambda: tmp_path)

    path = diagnostic_logs.append_diagnostic_log(
        "app.log",
        "[1/3] Salvo: Leonardo_Silva.pdf\nTraceback com dados adicionais",
    )
    diagnostic_logs.append_diagnostic_log(
        "app.log", "Falha ao abrir /home/pessoa/documentos/modelo.fornax",
    )

    content = path.read_text(encoding="utf-8")
    assert "Leonardo" not in content
    assert "Traceback" not in content
    assert "/home/pessoa" not in content
    assert "[detalhes omitidos]" in content
    assert "[caminho omitido]" in content


def test_log_rotation_and_clear_are_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnostic_logs, "get_logs_dir", lambda: tmp_path)

    for index in range(8):
        diagnostic_logs.append_diagnostic_log(
            "app.log", f"evento {index} " + "x" * 30,
            sanitize=False, max_bytes=90, backups=3,
        )

    assert (tmp_path / "app.log").is_file()
    assert (tmp_path / "app.log.1").is_file()
    assert not (tmp_path / "app.log.4").exists()

    diagnostic_logs.clear_diagnostic_log("app.log")
    assert not list(tmp_path.glob("app.log*"))


def test_crash_summary_omits_absolute_paths_source_and_exception_value():
    try:
        raise RuntimeError("segredo do usuário")
    except RuntimeError as error:
        summary = diagnostic_logs.crash_summary(type(error), error.__traceback__)

    assert "RuntimeError" in summary
    assert "segredo do usuário" not in summary
    assert str(Path(__file__).resolve()) not in summary
    assert Path(__file__).name in summary
