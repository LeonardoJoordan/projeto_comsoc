from core.text_layout import variables_in_html
from features.generator.renderer import NativeRenderer


def test_rich_text_extracts_accented_placeholder_split_between_spans():
    html = "<p>{Matrí<span style='color:#f00'>cula</span>}</p>"

    assert variables_in_html(html) == ["Matrícula"]


def test_renderer_replaces_accented_placeholder():
    renderer = NativeRenderer({
        "canvas_size": {"w": 10, "h": 10},
        "background_path": None,
        "boxes": [], "images": [], "signatures": [], "shapes": [],
        "placeholders": ["Matrícula"],
    })

    assert renderer.resolve_html("<p>{Matrícula}</p>", {"Matrícula": "123"}) == "<p>123</p>"
