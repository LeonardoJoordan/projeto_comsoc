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
    layer_ids = [prepared[collection][0]['layer_id']
                 for collection in ('boxes', 'images', 'signatures')]
    assert all(type(value) is int for value in layer_ids)
    assert len(set(layer_ids)) == 3
    assert prepared["boxes"][0]["html"] == "<p>{nome}</p>"


def test_prepare_scene_page_reserves_background_id_and_repairs_duplicates():
    source = {'bg_props': {'layer_id': 3},
              'shapes': [{'layer_id': 3, 'object_id': 'mask'}],
              'images': [{'layer_id': 3, 'mask_shape_id': 'mask'}]}
    prepared = prepare_scene_page(source)
    shape = prepared['shapes'][0]
    image = prepared['images'][0]
    assert len({3, shape['layer_id'], image['layer_id']}) == 3
    assert image['mask_shape_id'] == f"shape:{shape['layer_id']}"
    assert source['images'][0]['mask_shape_id'] == 'mask'


def test_prepare_scene_page_preserves_explicit_current_values():
    source = {
        "bg_props": {"layer_id": 3, "custom_name": "Base"},
        "boxes": [{"id": "nome", "layer_id": 5, "html": "<p>Atual</p>"}],
        "images": [],
        "signatures": [],
    }

    assert prepare_scene_page(source) == source
