from PySide6.QtGui import QFontDatabase


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

    for box in template_data.get("boxes", []):
        family = str(box.get("font_family", "")).strip()
        normalized = _normalized_font_name(family)
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
