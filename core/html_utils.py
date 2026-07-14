import re


_TEXT_DECORATION_RE = re.compile(
    r"(?i)(?<![-\w])text-decoration(?:-line)?\s*:\s*([^;\"']+)\s*;?"
)


def normalize_text_decoration(html: str) -> str:
    """Preserva somente o sublinhado entre as decorações visuais do HTML."""
    def replace_decoration(match: re.Match) -> str:
        value = match.group(1)
        if re.search(r"(?i)\bunderline\b", value):
            return "text-decoration: underline;"
        if re.search(r"(?i)\bnone\b", value):
            return "text-decoration: none;"
        return ""

    return _TEXT_DECORATION_RE.sub(replace_decoration, html)
