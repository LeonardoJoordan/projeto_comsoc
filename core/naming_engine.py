import re
from typing import Dict, Iterable, Set

_INVALID_WIN_CHARS = r'<>:"/\\|?*'
_INVALID_WIN_RE = re.compile(f"[{re.escape(_INVALID_WIN_CHARS)}]")

def sanitize_filename(name: str, replacement: str = "_") -> str:
    """
    Remove caracteres inválidos (Windows) e normaliza espaços/pontos.
    """
    name = name.strip()
    name = _INVALID_WIN_RE.sub(replacement, name)
    name = re.sub(r"\s+", " ", name).strip()
    name = name.rstrip(". ").strip()
    return name or "arquivo"

def apply_pattern(pattern: str, row: Dict[str, str]) -> str:
    """
    Substitui {coluna} pelos valores da linha.
    """
    def repl(match: re.Match) -> str:
        key = match.group(1).strip()
        return str(row.get(key, "")).strip()

    return re.sub(r"\{([^{}]+)\}", repl, pattern)

def unique_filename(base: str, used: Set[str]) -> str:
    """
    Se base já existe em used, adiciona sufixo _01, _02...
    """
    if base not in used:
        used.add(base)
        return base

    i = 1
    while True:
        candidate = f"{base}_{i:02d}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        i += 1

def build_output_filename(pattern: str, row: Dict[str, str], used: Set[str]) -> str:
    raw = apply_pattern(pattern, row)
    base = sanitize_filename(raw)
    return unique_filename(base, used)