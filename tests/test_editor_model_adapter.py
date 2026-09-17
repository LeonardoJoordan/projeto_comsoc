from copy import deepcopy

from features.editor.model_adapter import prepare_scene_page


def test_prepare_scene_page_adds_only_editor_defaults_without_mutating_source():
    source = {
        "bg_props": {},
        "boxes": [{"id": "{nome}"}],
        "images": [{"path": "foto.png"}],
        "signatures": [{"path": "assinatura.png"}],
    }
    original = deepcopy(source)

    prepared = prepare_scene_page(source)

    assert source == original
    assert prepared["bg_props"] == {"layer_id": None, "custom_name": ""}
    assert prepared["boxes"][0]["layer_id"] is None
    assert prepared["boxes"][0]["html"] == "<p>{nome}</p>"
    assert prepared["images"][0]["layer_id"] is None
    assert prepared["signatures"][0]["layer_id"] is None


def test_prepare_scene_page_preserves_explicit_current_values():
    source = {
        "bg_props": {"layer_id": 3, "custom_name": "Base"},
        "boxes": [{"id": "nome", "layer_id": 5, "html": "<p>Atual</p>"}],
        "images": [],
        "signatures": [],
    }

    assert prepare_scene_page(source) == source
