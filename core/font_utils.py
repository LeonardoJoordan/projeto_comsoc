from PySide6.QtGui import QFontDatabase
import re
from html import unescape


def _normalized_font_name(name: str) -> str:
    return " ".join(str(name or "").strip().casefold().split())


def system_font_families() -> set[str]:
    """Retorna nomes normalizados das fontes disponíveis para o Qt."""
    try:
        families = QFontDatabase.families()
    except TypeError:
        families = QFontDatabase().families()
    return {_normalized_font_name(family) for family in families}


def template_font_families(template_data: dict) -> list[str]:
    """Coleta as famílias tipográficas declaradas nas caixas de texto do modelo."""
    fonts = []
    seen = set()

    if template_data.get("schema_version") == 4 and isinstance(template_data.get("pages"), list):
        boxes = [box for page in template_data["pages"] for box in page.get("boxes", [])]
    else:
        boxes = template_data.get("boxes", [])

    for box in boxes:
        families = [str(box.get("font_family", "")).strip()]
        if box.get("rich_text_version") == 1:
            for match in re.findall(
                r'font-family\s*:\s*(.+?)(?=;|["\'](?:\s|>)|$)',
                unescape(box.get("html", "")), re.I,
            ):
                families.extend(part.strip(" '\"") for part in match.split(","))
        for family in families:
            normalized = _normalized_font_name(family)
            if normalized in ("serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"):
                continue
            if family and normalized not in seen:
                fonts.append(family)
                seen.add(normalized)

    return fonts


def missing_template_fonts(template_data: dict) -> list[str]:
    available = system_font_families()
    missing = []

    for family in template_font_families(template_data):
        if _normalized_font_name(family) not in available:
            missing.append(family)

    return missing


def format_font_list(fonts: list[str]) -> str:
    return ", ".join(fonts)
