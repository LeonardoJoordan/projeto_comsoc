import re
import html as _html_mod
from html.parser import HTMLParser
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

ALLOWED_TAGS = {"b", "i", "u", "br"}


@dataclass
class CellValue:
    plain: str
    rich_html: str


# ---------------------------------------------------------------------------
# CSS helpers
# ---------------------------------------------------------------------------

def _parse_style(style: str) -> Dict[str, str]:
    """Parse a CSS inline style string into a dict of property->value."""
    result: Dict[str, str] = {}
    for part in style.split(";"):
        part = part.strip()
        if ":" not in part:
            continue
        prop, _, val = part.partition(":")
        result[prop.strip().lower()] = val.strip().lower()
    return result


def _is_bold(style_dict: Dict[str, str]) -> bool:
    fw = style_dict.get("font-weight", "")
    if fw in ("bold", "bolder"):
        return True
    try:
        return int(fw) >= 600
    except ValueError:
        return False


def _is_italic(style_dict: Dict[str, str]) -> bool:
    return style_dict.get("font-style", "") == "italic"


def _is_underline(style_dict: Dict[str, str]) -> bool:
    td = style_dict.get("text-decoration", "")
    tdl = style_dict.get("text-decoration-line", "")
    return "underline" in td or "underline" in tdl


# ---------------------------------------------------------------------------
# Style stack — tracks inherited bold/italic/underline while walking the tree
# ---------------------------------------------------------------------------

@dataclass
class _StyleState:
    bold: bool = False
    italic: bool = False
    underline: bool = False


class _StyleStack:
    """Maintains a stack of formatting states for nested tags."""

    def __init__(self, base: Optional[_StyleState] = None):
        initial = base or _StyleState()
        self._stack: List[_StyleState] = [initial]

    @property
    def current(self) -> _StyleState:
        return self._stack[-1]

    def push(self, style_dict: Dict[str, str]) -> _StyleState:
        prev = self._stack[-1]
        new = _StyleState(
            bold=prev.bold or _is_bold(style_dict),
            italic=prev.italic or _is_italic(style_dict),
            underline=prev.underline or _is_underline(style_dict),
        )
        self._stack.append(new)
        return new

    def push_explicit(self, bold=False, italic=False, underline=False) -> _StyleState:
        prev = self._stack[-1]
        new = _StyleState(
            bold=prev.bold or bold,
            italic=prev.italic or italic,
            underline=prev.underline or underline,
        )
        self._stack.append(new)
        return new

    def pop(self) -> Optional[_StyleState]:
        if len(self._stack) > 1:
            return self._stack.pop()
        return None


# ---------------------------------------------------------------------------
# parse_clipboard_html_table
# ---------------------------------------------------------------------------

def parse_clipboard_html_table(html: str) -> List[List[CellValue]]:
    parser = _HtmlTableParser()
    parser.feed(html or "")
    out: List[List[CellValue]] = []
    for row in parser.grid:
        out_row: List[CellValue] = []
        for cell_html, cell_base_style in row:
            rich = sanitize_inline_html(cell_html, base_style=cell_base_style, class_styles=parser._class_styles)
            plain = _plain_from_rich_html(rich)
            out_row.append(CellValue(plain=plain, rich_html=rich))
        out.append(out_row)
    return out


# ---------------------------------------------------------------------------
# parse_tsv  (fallback — unchanged)
# ---------------------------------------------------------------------------

def parse_tsv(text: str) -> List[List[CellValue]]:
    rows = (text or "").splitlines()
    grid: List[List[CellValue]] = []
    for r in rows:
        cols = r.split("\t")
        row: List[CellValue] = []
        for c in cols:
            plain = _clean_spaces(c)
            row.append(CellValue(plain=plain, rich_html=_html_mod.escape(plain, quote=False)))
        grid.append(row)
    return grid


# ---------------------------------------------------------------------------
# sanitize_inline_html
# ---------------------------------------------------------------------------

def sanitize_inline_html(html: str, base_style: Optional[_StyleState] = None, class_styles: Optional[Dict[str, _StyleState]] = None) -> str:
    """
    Convert arbitrary spreadsheet cell HTML into a clean subset using only
    <b>, <i>, <u>, <br>.  Handles style inheritance from the cell itself
    (base_style) down through nested tags including Excel-style <span class>.
    """
    classes_map = class_styles or {}

    class _InlineSanitizer(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.out: List[str] = []
            # open_tags tracks which formatting tags WE emitted so we can close
            # them properly; it is separate from the style stack.
            self.open_tags: List[str] = []
            self.style_stack = _StyleStack(base_style)
            # Track which formatting tags were opened for each DOM tag push so
            # we know what to close when the tag ends.
            self.tag_opened_fmt: List[List[str]] = []
            # Emite tags iniciais se base_style já vier ativo
            if base_style:
                for attr, tag in (("bold", "b"), ("italic", "i"), ("underline", "u")):
                    if getattr(base_style, attr):
                        self.out.append(f"<{tag}>")
                        self.open_tags.append(tag)

        # ------------------------------------------------------------------
        def _apply_state(self, new_state: _StyleState) -> List[str]:
            """Emit opening tags for any formatting newly active in new_state."""
            prev = self.style_stack._stack[-2] if len(self.style_stack._stack) >= 2 else _StyleState()
            opened: List[str] = []
            for attr, tag in (("bold", "b"), ("italic", "i"), ("underline", "u")):
                if getattr(new_state, attr) and not getattr(prev, attr):
                    self.out.append(f"<{tag}>")
                    self.open_tags.append(tag)
                    opened.append(tag)
            return opened

        def _close_tags(self, tags: List[str]) -> None:
            for tag in reversed(tags):
                if tag in self.open_tags:
                    self.out.append(f"</{tag}>")
                    # remove last occurrence
                    idx = len(self.open_tags) - 1 - self.open_tags[::-1].index(tag)
                    self.open_tags.pop(idx)

        # ------------------------------------------------------------------
        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            attrs_dict = {(k or "").lower(): (v or "") for k, v in attrs}

            if tag == "br":
                self.out.append("<br>")
                return

            if tag in ("b", "strong"):
                new = self.style_stack.push_explicit(bold=True)
                opened = self._apply_state(new)
                self.tag_opened_fmt.append(opened)
                return

            if tag in ("i", "em"):
                new = self.style_stack.push_explicit(italic=True)
                opened = self._apply_state(new)
                self.tag_opened_fmt.append(opened)
                return

            if tag == "u":
                new = self.style_stack.push_explicit(underline=True)
                opened = self._apply_state(new)
                self.tag_opened_fmt.append(opened)
                return

            if tag in ("span", "font", "p", "div"):
                style_str = attrs_dict.get("style", "")
                style_dict = _parse_style(style_str)

                is_b = _is_bold(style_dict)
                is_i = _is_italic(style_dict)
                is_u = _is_underline(style_dict)

                for cls in attrs_dict.get("class", "").split():
                    if cs := classes_map.get(cls):
                        is_b = is_b or cs.bold
                        is_i = is_i or cs.italic
                        is_u = is_u or cs.underline

                new = self.style_stack.push_explicit(bold=is_b, italic=is_i, underline=is_u)
                opened = self._apply_state(new)
                self.tag_opened_fmt.append(opened)
                return

            # Any other tag: push a no-op frame so pop stays balanced
            self.style_stack.push_explicit()
            self.tag_opened_fmt.append([])

        def handle_endtag(self, tag):
            tag = tag.lower()
            if tag == "br":
                return
            if self.tag_opened_fmt:
                opened = self.tag_opened_fmt.pop()
                self._close_tags(opened)
            self.style_stack.pop()

        def handle_data(self, data):
            if data:
                self.out.append(_html_mod.escape(_clean_spaces_keep_edges(data), quote=False))

        def get_html(self) -> str:
            # Close any tags still open
            for tag in reversed(self.open_tags[:]):
                self.out.append(f"</{tag}>")
            s = "".join(self.out)
            s = re.sub(r"\s*<br>\s*", "<br>", s)
            s = s.strip()
            return s

    p = _InlineSanitizer()
    p.feed(html or "")
    return p.get_html()


# ---------------------------------------------------------------------------
# _HtmlTableParser  — extracts grid + per-cell base styles
# ---------------------------------------------------------------------------

class _HtmlTableParser(HTMLParser):
    """
    Parses an HTML table from clipboard data.

    grid rows contain tuples of (cell_raw_html, _StyleState) so that
    formatting declared on the <td>/<th> itself is passed downstream.

    Also pre-processes the <style> block (common in Excel-exported HTML)
    to build a class->StyleState map.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_td = False
        self.in_tr = False
        self.current_cell_chunks: List[str] = []
        self.current_row: List[Tuple[str, _StyleState]] = []
        self.grid: List[List[Tuple[str, _StyleState]]] = []
        self._current_cell_base: _StyleState = _StyleState()
        # CSS class map extracted from <style> block
        self._class_styles: Dict[str, _StyleState] = {}
        self._in_style = False
        self._style_text: List[str] = []

    # ------------------------------------------------------------------
    # <style> block handling (Excel embeds class definitions here)
    # ------------------------------------------------------------------

    def _parse_style_block(self, css: str) -> None:
        """Extract class rules like  .xl65{font-weight:700;}  from a CSS block."""
        for m in re.finditer(r'\.([\w-]+)\s*\{([^}]*)\}', css):
            cls = m.group(1)
            style_dict = _parse_style(m.group(2))
            state = _StyleState(
                bold=_is_bold(style_dict),
                italic=_is_italic(style_dict),
                underline=_is_underline(style_dict),
            )
            self._class_styles[cls] = state

    def _state_from_attrs(self, attrs) -> _StyleState:
        attrs_dict = {(k or "").lower(): (v or "") for k, v in attrs}
        style_dict = _parse_style(attrs_dict.get("style", ""))
        state = _StyleState(
            bold=_is_bold(style_dict),
            italic=_is_italic(style_dict),
            underline=_is_underline(style_dict),
        )
        # Merge class-based styles
        for cls in attrs_dict.get("class", "").split():
            cs = self._class_styles.get(cls)
            if cs:
                state.bold = state.bold or cs.bold
                state.italic = state.italic or cs.italic
                state.underline = state.underline or cs.underline
        return state

    # ------------------------------------------------------------------

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag == "style":
            self._in_style = True
            self._style_text = []
            return

        if tag == "tr":
            self.in_tr = True
            self.current_row = []
            return

        if tag in ("td", "th") and self.in_tr:
            self.in_td = True
            self.current_cell_chunks = []
            self._current_cell_base = self._state_from_attrs(attrs)
            return

        if self.in_td:
            if tag == "br":
                self.current_cell_chunks.append("<br>")
                return
            if tag in ("b", "strong", "i", "em", "u"):
                self.current_cell_chunks.append(f"<{tag}>")
                return
            if tag in ("span", "font", "p", "div"):
                style = ""
                cls = ""
                for k, v in attrs:
                    kl = (k or "").lower()
                    if kl == "style":
                        style = v or ""
                    elif kl == "class":
                        cls = v or ""
                parts = []
                if style:
                    parts.append(f'style="{_html_mod.escape(style, quote=True)}"')
                if cls:
                    parts.append(f'class="{_html_mod.escape(cls, quote=True)}"')
                attr_str = " ".join(parts)
                self.current_cell_chunks.append(f"<{tag}{' ' + attr_str if attr_str else ''}>")
                return

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag == "style":
            self._in_style = False
            self._parse_style_block("".join(self._style_text))
            return

        if tag == "tr":
            if self.in_tr and self.current_row:
                self.grid.append(self.current_row)
            self.in_tr = False
            return

        if tag in ("td", "th"):
            if self.in_td:
                self.current_row.append(
                    ("".join(self.current_cell_chunks), self._current_cell_base)
                )
            self.in_td = False
            return

        if self.in_td:
            if tag in ("b", "strong", "i", "em", "u", "span", "font", "p", "div"):
                self.current_cell_chunks.append(f"</{tag}>")

    def handle_data(self, data):
        if self._in_style:
            self._style_text.append(data)
            return
        if self.in_td and data:
            self.current_cell_chunks.append(_html_mod.escape(data, quote=False))


# ---------------------------------------------------------------------------
# String utilities
# ---------------------------------------------------------------------------

def _plain_from_rich_html(html: str) -> str:
    """Extrai texto puro de rich_html, convertendo <br> em \n e decodificando entidades."""
    class _P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts: List[str] = []
        def handle_data(self, data):
            self.parts.append(data)
        def handle_starttag(self, tag, attrs):
            if tag == "br":
                self.parts.append("\n")
    p = _P()
    p.feed(html or "")
    return _clean_spaces("".join(p.parts))

def _clean_spaces(s: str) -> str:
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def _clean_spaces_keep_edges(s: str) -> str:
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s
