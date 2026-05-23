import re
import html as _html_mod
from html.parser import HTMLParser
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CellValue:
    plain: str
    rich_html: str

# ---------------------------------------------------------------------------
# Helpers Gerais de CSS e Limpeza de Texto
# ---------------------------------------------------------------------------
def _parse_style(style_str: str) -> dict:
    """Transforma uma string de CSS inline em um dicionário de propriedades."""
    result = {}
    if not style_str:
        return result
    for part in style_str.split(";"):
        if ":" not in part:
            continue
        prop, _, val = part.partition(":")
        result[prop.strip().lower()] = val.strip().lower()
    return result

def _clean_spaces(s: str) -> str:
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def _clean_spaces_keep_edges(s: str) -> str:
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s

# ---------------------------------------------------------------------------
# Trabalhadores Especializados
# ---------------------------------------------------------------------------

class GoogleSheets:
    @staticmethod
    def processar(html: str) -> List[List[CellValue]]:
        def attrs_to_dict(attrs) -> dict:
            attrs_dict = {}
            style_fragments = []

            for key, value in attrs:
                if not key:
                    continue

                key_l = key.lower()
                if key_l == "style":
                    style_fragments.append(value or "")
                    continue

                if value is None and style_fragments:
                    # Alguns HTMLs de clipboard chegam com aspas internas em style
                    # e o HTMLParser quebra o CSS em "atributos" soltos.
                    style_fragments.append(key)
                    continue

                attrs_dict[key_l] = value or ""

            if style_fragments:
                attrs_dict["style"] = " ".join(style_fragments)

            return attrs_dict

        def tags_from_style(style_str: str) -> List[str]:
            style = _parse_style(style_str)
            tags = []

            fw = style.get("font-weight", "")
            if fw in ("bold", "bolder"):
                tags.append("b")
            else:
                match = re.search(r"\d+", fw)
                if match and int(match.group(0)) >= 600:
                    tags.append("b")

            if style.get("font-style", "") in ("italic", "oblique"):
                tags.append("i")

            decoration = " ".join([
                style.get("text-decoration", ""),
                style.get("text-decoration-line", ""),
            ])
            if "underline" in decoration:
                tags.append("u")

            return tags

        def unique_ordered_tags(tags: List[str]) -> List[str]:
            ordered = []
            for tag in ("b", "i", "u"):
                if tag in tags:
                    ordered.append(tag)
            return ordered

        def plain_from_rich(rich: str) -> str:
            text = re.sub(r"<br\s*/?>", "\n", rich, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "", text)
            return _clean_spaces(text)

        class SheetsParser(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.grid: List[List[CellValue]] = []
                self.current_row: List[CellValue] = []
                self.in_td = False
                self.in_style = False
                self.seen_table_cell = False
                self.cell_chunks: List[str] = []
                self.base_tags: List[str] = []
                self.frames: List[tuple[str, List[str]]] = []
                self.fragment_chunks: List[str] = []
                self.fragment_frames: List[tuple[str, List[str]]] = []

            def _open_tags(self, tags: List[str], target: List[str]):
                for tag in tags:
                    target.append(f"<{tag}>")

            def _close_tags(self, tags: List[str], target: List[str]):
                for tag in reversed(tags):
                    target.append(f"</{tag}>")

            def _push_frame(self, tag: str, tags: List[str]):
                self._open_tags(tags, self.cell_chunks)
                self.frames.append((tag, tags))

            def _pop_frame(self, tag: str):
                if not self.frames:
                    return

                idx = len(self.frames) - 1
                while idx >= 0 and self.frames[idx][0] != tag:
                    idx -= 1

                if idx < 0:
                    idx = len(self.frames) - 1

                closing = self.frames[idx:]
                del self.frames[idx:]
                for _, tags in reversed(closing):
                    self._close_tags(tags, self.cell_chunks)

            def _push_fragment_frame(self, tag: str, tags: List[str]):
                self._open_tags(tags, self.fragment_chunks)
                self.fragment_frames.append((tag, tags))

            def _pop_fragment_frame(self, tag: str):
                if not self.fragment_frames:
                    return

                idx = len(self.fragment_frames) - 1
                while idx >= 0 and self.fragment_frames[idx][0] != tag:
                    idx -= 1

                if idx < 0:
                    idx = len(self.fragment_frames) - 1

                closing = self.fragment_frames[idx:]
                del self.fragment_frames[idx:]
                for _, tags in reversed(closing):
                    self._close_tags(tags, self.fragment_chunks)

            def _tags_for_tag(self, tag: str, attrs) -> List[str]:
                semantic = []
                if tag in ("b", "strong"):
                    semantic.append("b")
                elif tag in ("i", "em"):
                    semantic.append("i")
                elif tag == "u":
                    semantic.append("u")

                attrs_dict = attrs_to_dict(attrs)
                return unique_ordered_tags(semantic + tags_from_style(attrs_dict.get("style", "")))

            def _finalize_cell(self):
                while self.frames:
                    _, tags = self.frames.pop()
                    self._close_tags(tags, self.cell_chunks)

                self._close_tags(self.base_tags, self.cell_chunks)

                rich = "".join(self.cell_chunks)
                rich = re.sub(r"\s*<br>\s*", "<br>", rich).strip()
                plain = plain_from_rich(rich)
                self.current_row.append(CellValue(plain=plain, rich_html=rich))

                self.in_td = False
                self.cell_chunks = []
                self.base_tags = []
                self.frames = []

            def handle_starttag(self, tag, attrs):
                tag = tag.lower()

                if tag == "style":
                    self.in_style = True
                    return

                if tag == "tr":
                    self.current_row = []
                    return

                if tag in ("td", "th"):
                    self.in_td = True
                    self.seen_table_cell = True
                    self.cell_chunks = []
                    self.frames = []
                    self.base_tags = tags_from_style(attrs_to_dict(attrs).get("style", ""))
                    self._open_tags(self.base_tags, self.cell_chunks)
                    return

                if self.in_td:
                    if tag == "br":
                        self.cell_chunks.append("<br>")
                        return

                    self._push_frame(tag, self._tags_for_tag(tag, attrs))
                    return

                if not self.seen_table_cell:
                    if tag == "br":
                        self.fragment_chunks.append("<br>")
                        return
                    self._push_fragment_frame(tag, self._tags_for_tag(tag, attrs))

            def handle_endtag(self, tag):
                tag = tag.lower()

                if tag == "style":
                    self.in_style = False
                    return

                if tag == "tr":
                    if self.current_row:
                        self.grid.append(self.current_row)
                    return

                if tag in ("td", "th") and self.in_td:
                    self._finalize_cell()
                    return

                if self.in_td:
                    self._pop_frame(tag)
                    return

                if not self.seen_table_cell:
                    self._pop_fragment_frame(tag)

            def handle_data(self, data):
                if self.in_style or not data:
                    return

                if self.in_td:
                    self.cell_chunks.append(_html_mod.escape(_clean_spaces_keep_edges(data), quote=False))
                elif not self.seen_table_cell:
                    self.fragment_chunks.append(_html_mod.escape(_clean_spaces_keep_edges(data), quote=False))

        parser = SheetsParser()
        parser.feed(html or "")
        
        if not parser.grid and parser.fragment_chunks:
            while parser.fragment_frames:
                _, tags = parser.fragment_frames.pop()
                parser._close_tags(tags, parser.fragment_chunks)

            rich = "".join(parser.fragment_chunks)
            rich = re.sub(r"\s*<br>\s*", "<br>", rich).strip()
            plain = plain_from_rich(rich)
            if plain:
                return [[CellValue(plain=plain, rich_html=rich)]]
                
        return parser.grid


class Excel:
    @staticmethod
    def processar(html: str) -> List[List[CellValue]]:
        def attrs_to_dict(attrs) -> dict:
            attrs_dict = {}
            style_fragments = []

            for key, value in attrs:
                if not key:
                    continue

                key_l = key.lower()
                if key_l == "style":
                    style_fragments.append(value or "")
                    continue

                if value is None and style_fragments:
                    style_fragments.append(key)
                    continue

                attrs_dict[key_l] = value or ""

            if style_fragments:
                attrs_dict["style"] = " ".join(style_fragments)

            return attrs_dict

        def unique_ordered_tags(tags: List[str]) -> List[str]:
            ordered = []
            for tag in ("b", "i", "u"):
                if tag in tags:
                    ordered.append(tag)
            return ordered

        def tags_from_style(style_str: str) -> List[str]:
            style = _parse_style(style_str)
            tags = []

            fw = style.get("font-weight", "")
            if fw in ("bold", "bolder"):
                tags.append("b")
            else:
                match = re.search(r"\d+", fw)
                if match and int(match.group(0)) >= 600:
                    tags.append("b")

            if style.get("font-style", "") in ("italic", "oblique"):
                tags.append("i")

            decoration = " ".join([
                style.get("text-decoration", ""),
                style.get("text-decoration-line", ""),
            ])
            underline_style = style.get("text-underline-style", "")
            if "underline" in decoration or (underline_style and underline_style != "none"):
                tags.append("u")

            return tags

        def plain_from_rich(rich: str) -> str:
            text = re.sub(r"<br\s*/?>", "\n", rich, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "", text)
            return _clean_spaces(text)

        class ExcelParser(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.grid: List[List[CellValue]] = []
                self.current_row: List[CellValue] = []
                self.in_td = False
                self.in_style = False
                self.seen_table_cell = False
                self.cell_chunks: List[str] = []
                self.style_text = []
                self.classes_map: dict[str, List[str]] = {}
                self.base_tags: List[str] = []
                self.frames: List[tuple[str, List[str]]] = []
                self.fragment_chunks: List[str] = []
                self.fragment_frames: List[tuple[str, List[str]]] = []

            def _merge_class_tags(self, class_name: str, tags: List[str]):
                if not tags:
                    return

                current = self.classes_map.get(class_name, [])
                self.classes_map[class_name] = unique_ordered_tags(current + tags)

            def _parse_css_block(self, css_text: str):
                css_text = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)
                for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css_text):
                    selectors = m.group(1)
                    tags = tags_from_style(m.group(2))
                    if not tags:
                        continue

                    for selector in selectors.split(","):
                        for cls in re.findall(r"\.([\w-]+)", selector):
                            self._merge_class_tags(cls, tags)

            def _open_tags(self, tags: List[str], target: List[str]):
                for tag in tags:
                    target.append(f"<{tag}>")

            def _close_tags(self, tags: List[str], target: List[str]):
                for tag in reversed(tags):
                    target.append(f"</{tag}>")

            def _class_tags(self, class_attr: str) -> List[str]:
                tags = []
                for cls in (class_attr or "").split():
                    tags.extend(self.classes_map.get(cls, []))
                return unique_ordered_tags(tags)

            def _tags_for_tag(self, tag: str, attrs) -> List[str]:
                semantic = []
                if tag in ("b", "strong"):
                    semantic.append("b")
                elif tag in ("i", "em"):
                    semantic.append("i")
                elif tag == "u":
                    semantic.append("u")

                attrs_dict = attrs_to_dict(attrs)
                style_tags = tags_from_style(attrs_dict.get("style", ""))
                class_tags = self._class_tags(attrs_dict.get("class", ""))
                return unique_ordered_tags(semantic + class_tags + style_tags)

            def _push_frame(self, tag: str, tags: List[str]):
                self._open_tags(tags, self.cell_chunks)
                self.frames.append((tag, tags))

            def _pop_frame(self, tag: str):
                if not self.frames:
                    return

                idx = len(self.frames) - 1
                while idx >= 0 and self.frames[idx][0] != tag:
                    idx -= 1

                if idx < 0:
                    idx = len(self.frames) - 1

                closing = self.frames[idx:]
                del self.frames[idx:]
                for _, tags in reversed(closing):
                    self._close_tags(tags, self.cell_chunks)

            def _push_fragment_frame(self, tag: str, tags: List[str]):
                self._open_tags(tags, self.fragment_chunks)
                self.fragment_frames.append((tag, tags))

            def _pop_fragment_frame(self, tag: str):
                if not self.fragment_frames:
                    return

                idx = len(self.fragment_frames) - 1
                while idx >= 0 and self.fragment_frames[idx][0] != tag:
                    idx -= 1

                if idx < 0:
                    idx = len(self.fragment_frames) - 1

                closing = self.fragment_frames[idx:]
                del self.fragment_frames[idx:]
                for _, tags in reversed(closing):
                    self._close_tags(tags, self.fragment_chunks)

            def _finalize_cell(self):
                while self.frames:
                    _, tags = self.frames.pop()
                    self._close_tags(tags, self.cell_chunks)

                self._close_tags(self.base_tags, self.cell_chunks)

                rich = "".join(self.cell_chunks)
                rich = re.sub(r"\s*<br>\s*", "<br>", rich).strip()
                plain = plain_from_rich(rich)
                self.current_row.append(CellValue(plain=plain, rich_html=rich))

                self.in_td = False
                self.cell_chunks = []
                self.base_tags = []
                self.frames = []

            def handle_starttag(self, tag, attrs):
                tag = tag.lower()

                if tag == "style":
                    self.in_style = True
                    self.style_text = []
                    return

                if tag == "tr":
                    self.current_row = []
                    return

                if tag in ("td", "th"):
                    self.in_td = True
                    self.seen_table_cell = True
                    self.cell_chunks = []
                    self.frames = []
                    self.base_tags = self._tags_for_tag(tag, attrs)
                    self._open_tags(self.base_tags, self.cell_chunks)
                    return

                if self.in_td:
                    if tag == "br":
                        self.cell_chunks.append("<br>")
                        return

                    self._push_frame(tag, self._tags_for_tag(tag, attrs))
                    return

                if not self.seen_table_cell:
                    if tag == "br":
                        self.fragment_chunks.append("<br>")
                        return
                    self._push_fragment_frame(tag, self._tags_for_tag(tag, attrs))

            def handle_endtag(self, tag):
                tag = tag.lower()

                if tag == "style":
                    self.in_style = False
                    self._parse_css_block("".join(self.style_text))
                    return

                if tag == "tr":
                    if self.current_row:
                        self.grid.append(self.current_row)
                    return

                if tag in ("td", "th") and self.in_td:
                    self._finalize_cell()
                    return

                if self.in_td:
                    self._pop_frame(tag)
                    return

                if not self.seen_table_cell:
                    self._pop_fragment_frame(tag)

            def handle_data(self, data):
                if self.in_style:
                    self.style_text.append(data)
                elif self.in_td and data:
                    self.cell_chunks.append(_html_mod.escape(_clean_spaces_keep_edges(data), quote=False))
                elif not self.seen_table_cell and data:
                    self.fragment_chunks.append(_html_mod.escape(_clean_spaces_keep_edges(data), quote=False))

        parser = ExcelParser()
        parser.feed(html or "")

        if not parser.grid and parser.fragment_chunks:
            while parser.fragment_frames:
                _, tags = parser.fragment_frames.pop()
                parser._close_tags(tags, parser.fragment_chunks)

            rich = "".join(parser.fragment_chunks)
            rich = re.sub(r"\s*<br>\s*", "<br>", rich).strip()
            plain = plain_from_rich(rich)
            if plain:
                return [[CellValue(plain=plain, rich_html=rich)]]

        return parser.grid


class LibreOffice:
    @staticmethod
    def processar(html: str) -> List[List[CellValue]]:
        def attrs_to_dict(attrs) -> dict:
            attrs_dict = {}
            style_fragments = []

            for key, value in attrs:
                if not key:
                    continue

                key_l = key.lower()
                if key_l == "style":
                    style_fragments.append(value or "")
                    continue

                if value is None and style_fragments:
                    style_fragments.append(key)
                    continue

                attrs_dict[key_l] = value or ""

            if style_fragments:
                attrs_dict["style"] = " ".join(style_fragments)

            return attrs_dict

        def unique_ordered_tags(tags: List[str]) -> List[str]:
            ordered = []
            for tag in ("b", "i", "u"):
                if tag in tags:
                    ordered.append(tag)
            return ordered

        def tags_from_style(style_str: str) -> List[str]:
            style = _parse_style(style_str)
            tags = []

            fw = style.get("font-weight", "")
            if fw in ("bold", "bolder"):
                tags.append("b")
            else:
                match = re.search(r"\d+", fw)
                if match and int(match.group(0)) >= 600:
                    tags.append("b")

            if style.get("font-style", "") in ("italic", "oblique"):
                tags.append("i")

            decoration = " ".join([
                style.get("text-decoration", ""),
                style.get("text-decoration-line", ""),
            ])
            underline_style = style.get("text-underline-style", "")
            if "underline" in decoration or (underline_style and underline_style != "none"):
                tags.append("u")

            return tags

        def plain_from_rich(rich: str) -> str:
            text = re.sub(r"<br\s*/?>", "\n", rich, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "", text)
            return _clean_spaces(text)

        class LibreParser(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.grid: List[List[CellValue]] = []
                self.current_row: List[CellValue] = []
                self.in_td = False
                self.in_style = False
                self.seen_table_cell = False
                self.cell_chunks: List[str] = []
                self.style_text = []
                self.classes_map: dict[str, List[str]] = {}
                self.base_tags: List[str] = []
                self.frames: List[tuple[str, List[str]]] = []
                self.fragment_chunks: List[str] = []
                self.fragment_frames: List[tuple[str, List[str]]] = []

            def _merge_class_tags(self, class_name: str, tags: List[str]):
                if not tags:
                    return

                current = self.classes_map.get(class_name, [])
                self.classes_map[class_name] = unique_ordered_tags(current + tags)

            def _parse_css_block(self, css_text: str):
                css_text = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)
                for m in re.finditer(r"([^{}@]+)\{([^}]*)\}", css_text):
                    selectors = m.group(1)
                    tags = tags_from_style(m.group(2))
                    if not tags:
                        continue

                    for selector in selectors.split(","):
                        for cls in re.findall(r"\.([\w-]+)", selector):
                            self._merge_class_tags(cls, tags)

            def _open_tags(self, tags: List[str], target: List[str]):
                for tag in tags:
                    target.append(f"<{tag}>")

            def _close_tags(self, tags: List[str], target: List[str]):
                for tag in reversed(tags):
                    target.append(f"</{tag}>")

            def _class_tags(self, class_attr: str) -> List[str]:
                tags = []
                for cls in (class_attr or "").split():
                    tags.extend(self.classes_map.get(cls, []))
                return unique_ordered_tags(tags)

            def _tags_for_tag(self, tag: str, attrs) -> List[str]:
                semantic = []
                if tag in ("b", "strong"):
                    semantic.append("b")
                elif tag in ("i", "em"):
                    semantic.append("i")
                elif tag == "u":
                    semantic.append("u")

                attrs_dict = attrs_to_dict(attrs)
                class_tags = self._class_tags(attrs_dict.get("class", ""))
                style_tags = tags_from_style(attrs_dict.get("style", ""))
                return unique_ordered_tags(semantic + class_tags + style_tags)

            def _push_frame(self, tag: str, tags: List[str]):
                self._open_tags(tags, self.cell_chunks)
                self.frames.append((tag, tags))

            def _pop_frame(self, tag: str):
                if not self.frames:
                    return

                idx = len(self.frames) - 1
                while idx >= 0 and self.frames[idx][0] != tag:
                    idx -= 1

                if idx < 0:
                    idx = len(self.frames) - 1

                closing = self.frames[idx:]
                del self.frames[idx:]
                for _, tags in reversed(closing):
                    self._close_tags(tags, self.cell_chunks)

            def _push_fragment_frame(self, tag: str, tags: List[str]):
                self._open_tags(tags, self.fragment_chunks)
                self.fragment_frames.append((tag, tags))

            def _pop_fragment_frame(self, tag: str):
                if not self.fragment_frames:
                    return

                idx = len(self.fragment_frames) - 1
                while idx >= 0 and self.fragment_frames[idx][0] != tag:
                    idx -= 1

                if idx < 0:
                    idx = len(self.fragment_frames) - 1

                closing = self.fragment_frames[idx:]
                del self.fragment_frames[idx:]
                for _, tags in reversed(closing):
                    self._close_tags(tags, self.fragment_chunks)

            def _finalize_cell(self):
                while self.frames:
                    _, tags = self.frames.pop()
                    self._close_tags(tags, self.cell_chunks)

                self._close_tags(self.base_tags, self.cell_chunks)

                rich = "".join(self.cell_chunks)
                rich = re.sub(r"\s*<br>\s*", "<br>", rich).strip()
                plain = plain_from_rich(rich)
                self.current_row.append(CellValue(plain=plain, rich_html=rich))

                self.in_td = False
                self.cell_chunks = []
                self.base_tags = []
                self.frames = []

            def handle_starttag(self, tag, attrs):
                tag = tag.lower()

                if tag == "style":
                    self.in_style = True
                    self.style_text = []
                    return

                if tag == "tr":
                    self.current_row = []
                    return

                if tag in ("td", "th"):
                    self.in_td = True
                    self.seen_table_cell = True
                    self.cell_chunks = []
                    self.frames = []
                    self.base_tags = self._tags_for_tag(tag, attrs)
                    self._open_tags(self.base_tags, self.cell_chunks)
                    return

                if self.in_td:
                    if tag == "br":
                        self.cell_chunks.append("<br>")
                        return

                    self._push_frame(tag, self._tags_for_tag(tag, attrs))
                    return

                if not self.seen_table_cell:
                    if tag == "br":
                        self.fragment_chunks.append("<br>")
                        return

                    self._push_fragment_frame(tag, self._tags_for_tag(tag, attrs))

            def handle_endtag(self, tag):
                tag = tag.lower()

                if tag == "style":
                    self.in_style = False
                    self._parse_css_block("".join(self.style_text))
                    return

                if tag == "tr":
                    if self.current_row:
                        self.grid.append(self.current_row)
                    return

                if tag in ("td", "th") and self.in_td:
                    self._finalize_cell()
                    return

                if self.in_td:
                    self._pop_frame(tag)
                    return

                if not self.seen_table_cell:
                    self._pop_fragment_frame(tag)

            def handle_data(self, data):
                if self.in_style:
                    self.style_text.append(data)
                elif self.in_td and data:
                    self.cell_chunks.append(_html_mod.escape(_clean_spaces_keep_edges(data), quote=False))
                elif not self.seen_table_cell and data:
                    self.fragment_chunks.append(_html_mod.escape(_clean_spaces_keep_edges(data), quote=False))

        parser = LibreParser()
        parser.feed(html or "")

        if not parser.grid and parser.fragment_chunks:
            while parser.fragment_frames:
                _, tags = parser.fragment_frames.pop()
                parser._close_tags(tags, parser.fragment_chunks)

            rich = "".join(parser.fragment_chunks)
            rich = re.sub(r"\s*<br>\s*", "<br>", rich).strip()
            plain = plain_from_rich(rich)
            if plain:
                return [[CellValue(plain=plain, rich_html=rich)]]

        return parser.grid


class FallbackTSV:
    @staticmethod
    def processar(text: str) -> List[List[CellValue]]:
        rows = (text or "").splitlines()
        grid: List[List[CellValue]] = []
        for r in rows:
            if not r.strip() and len(rows) > 1: 
                continue  # Pula linhas puramente vazias de quebra de bloco externa
            cols = r.split("\t")
            row: List[CellValue] = []
            for c in cols:
                plain = _clean_spaces(c)
                # No texto puro não há tags, tratamos entidades básicas por segurança
                rich = _html_mod.escape(plain, quote=False)
                row.append(CellValue(plain=plain, rich_html=rich))
            grid.append(row)
        return grid


# ---------------------------------------------------------------------------
# O PORTEIRO (Função de Triagem Centralizada)
# ---------------------------------------------------------------------------
def router(html: str, texto: str) -> List[List[CellValue]]:
    """Função de triagem que atua como porteiro, identificando a assinatura

    dos dados e direcionando ao trabalhador especializado correspondente.
    """
    if not html or not html.strip():
        return FallbackTSV.processar(texto)

    html_low = html.lower()

    # 1. Triagem Google Sheets
    if "data-sheets-" in html_low or "google-sheets-html-origin" in html_low:
        return GoogleSheets.processar(html)

    # 2. Triagem Microsoft Excel
    if "excel.sheet" in html_low or "progid content=excel" in html_low or "class=xl" in html_low:
        return Excel.processar(html)

    # 3. Triagem LibreOffice Calc
    if "libreoffice" in html_low or 'content="libreoffice' in html_low or "generator content=" in html_low:
        return LibreOffice.processar(html)

    # 4. Fallback de Segurança: Se possui tags de tabela genéricas, usa o parser do Excel
    if "<table" in html_low or "<tr" in html_low:
        return Excel.processar(html)

    # Se nada acima corresponder, trata como texto separado por tabulações (TSV)
    return FallbackTSV.processar(texto)


# ---------------------------------------------------------------------------
# Pontos de Entrada Legados (Mantidos para compatibilidade com o table_panel.py)
# ---------------------------------------------------------------------------
def parse_clipboard_html_table(html: str) -> List[List[CellValue]]:
    return router(html, "")

def parse_tsv(text: str) -> List[List[CellValue]]:
    return FallbackTSV.processar(text)

def parse_clipboard_html_fragment(html: str) -> List[List[CellValue]]:
    # Garante o roteamento mesmo para fragmentos de texto estilizados avulsos
    return router(html, "")
