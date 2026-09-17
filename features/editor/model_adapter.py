"""Fronteira entre documentos persistidos e o estado plano da cena do editor."""

from __future__ import annotations

from copy import deepcopy


def prepare_scene_page(page_data: dict) -> dict:
    """Retorna uma cópia com os poucos padrões exigidos pela cena atual.

    A normalização estrutural v3/v4 pertence a ``core.model_document``. Esta
    função concentra somente tolerâncias do editor para campos que versões
    antigas não gravavam e que o carregador da cena ainda acessa diretamente.
    """
    data = deepcopy(page_data)

    background = data.get("bg_props")
    if isinstance(background, dict):
        background.setdefault("layer_id", None)
        background.setdefault("custom_name", "")

    for box in data.get("boxes", []):
        box.setdefault("layer_id", None)
        if "html" not in box:
            box["html"] = f"<p>{box.get('id', 'Placeholder')}</p>"

    for collection in ("signatures", "images"):
        for item in data.get(collection, []):
            item.setdefault("layer_id", None)

    return data
