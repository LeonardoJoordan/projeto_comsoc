import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.font_utils import is_font_available, template_font_families, text_box_font_families
from core.model_document import load_model_document, normalize_model_document, save_model_document
from core.model_info import build_model_snapshot, ensure_origin_info
from core.ui_font import DOCUMENT_FONT_FAMILY, install_ui_font
from features.editor.canvas_items import DesignerBox


APP = QApplication.instance() or QApplication([])


def _document():
    document = normalize_model_document({
        "name": "Informações",
        "canvas_size": {"w": 1000, "h": 500},
        "target_w_mm": 100.0,
        "target_h_mm": 50.0,
        "placeholders": ["Nome"],
        "boxes": [{
            "id": "Nome", "custom_name": "Nome do aluno",
            "html": '<p><span style="font-family:Inter">A</span>'
                    '<span style="font-family:Fonte Ausente">B</span></p>',
            "rich_text_version": 1, "font_family": "Inter",
        }],
    })
    document["pages"][0]["layer_order"] = [
        item["object_id"]
        for collection in ("boxes", "images", "signatures", "shapes")
        for item in document["pages"][0][collection]
    ]
    document.pop("__source_schema_version", None)
    return document


def test_snapshot_lists_every_rich_text_family_per_box():
    snapshot = build_model_snapshot(_document(), source="imported")

    assert snapshot["text_boxes"] == [{
        "page": 1,
        "name": "Nome do aluno",
        "fonts": ["Inter", "Fonte Ausente"],
    }]
    assert template_font_families(_document()) == ["Inter", "Fonte Ausente"]


def test_origin_is_immutable_across_future_saves(tmp_path):
    original = ensure_origin_info(_document(), source="imported")
    first_origin = original["origin_info"]
    save_model_document(original, tmp_path)

    changed = load_model_document(tmp_path)
    changed["name"] = "Nome alterado"
    save_model_document(changed, tmp_path)

    assert load_model_document(tmp_path)["origin_info"] == first_origin


def test_bundled_inter_alias_is_available_and_new_text_uses_it():
    install_ui_font(APP)

    assert is_font_available("Inter")
    assert is_font_available("Inter 18pt")
    assert DesignerBox().state.font_family == DOCUMENT_FONT_FAMILY
