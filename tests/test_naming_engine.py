from pathlib import Path

import pytest

from core.naming_engine import (
    MAX_OUTPUT_BASENAME,
    build_output_filename,
    confined_output_path,
    sanitize_filename,
    unique_filename,
)


@pytest.mark.parametrize("raw", ["../fora", r"..\fora", "/tmp/fora", r"C:\fora"])
def test_filename_sanitization_removes_path_separators(raw):
    name = sanitize_filename(raw)

    assert "/" not in name and "\\" not in name
    assert Path(name).name == name


@pytest.mark.parametrize("reserved", ["CON", "nul.txt", "LPT1", "com9.pdf"])
def test_windows_reserved_names_are_made_portable(reserved):
    assert sanitize_filename(reserved).startswith("_")


def test_output_names_are_unique_case_insensitively_and_bounded():
    used = {"Diploma"}

    assert unique_filename("diploma", used) == "diploma_01"
    assert len(sanitize_filename("x" * 500)) == MAX_OUTPUT_BASENAME


def test_pattern_values_cannot_create_a_path():
    name = build_output_filename("{nome}", {"nome": "../../segredo"}, set())

    assert name == "__.._segredo"


def test_confined_output_rejects_escape_and_existing_external_symlink(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")
    link = output / "result.png"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("O ambiente não permite links simbólicos.")

    with pytest.raises(ValueError, match="fora da pasta"):
        confined_output_path(output, "result.png")
    with pytest.raises(ValueError, match="inválido"):
        confined_output_path(output, "../result.png")
