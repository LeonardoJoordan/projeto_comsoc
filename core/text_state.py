from dataclasses import dataclass

@dataclass
class TextState:
    """
    Fonte da Verdade para as propriedades de texto.
    Isola os metadados de formatação global do conteúdo HTML (limpo).
    """
    html_content: str = "Placeholder"
    font_family: str = "Arial"
    font_size: int = 16
    align: str = "left"
    vertical_align: str = "top"
    indent_px: float = 0.0
    line_height: float = 1.15