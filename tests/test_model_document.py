import copy
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QImage

from core.model_document import (
    MAX_CANVAS_DIMENSION,
    MAX_CANVAS_PIXELS,
    MAX_PHYSICAL_DIMENSION_MM,
    ModelDocumentError,
    ModelValidationError,
    UnsupportedSchemaError,
    adapt_model_page,
    add_blank_back_page,
    clear_model_page,
    document_signatures,
    install_model_directory,
    load_model_document,
    load_recovery_documents,
    normalize_model_document,
    page_ids,
    persistent_model_document,
    replace_model_page,
    remove_model_page,
    resolve_model_file,
    save_model_document,
    iter_page_asset_paths,
    iter_page_link_items,
)
from features.editor.editor_window import EditorWindow
from features.generator.renderer import NativeRenderer, renderers_for_document
from core.render_cache import (
    ensure_background_proxy,
    get_background_proxy_path,
    get_thumbnail_cache_path,
    publish_thumbnail_cache,
)
from core.font_utils import template_font_families


APP = QApplication.instance() or QApplication([])
FIXTURE = Path(__file__).parent / "fixtures" / "front_back_baseline" / "template_v3.json"


def legacy_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def two_page_document():
    document = normalize_model_document(legacy_fixture())
    back = copy.deepcopy(document["pages"][0])
    back["page_id"] = "back"
    back["field_ids"] = ["Nome", "Verso"]
    back["boxes"][0]["html"] = "<p>{Verso}</p>"
    back["shapes"][0]["fill_color"] = "#223344"
    for signature in back.get("signatures", []):
        signature.pop("signature_id", None)
    document["pages"].append(back)
    document["placeholders"] = ["Nome", "Cargo", "Site", "Verso"]
    document.pop("__source_schema_version", None)
    return normalize_model_document(document)


def test_v3_normalizes_in_memory_without_mutating_or_duplicating_background():
    source = legacy_fixture()
    before = copy.deepcopy(source)

    document = normalize_model_document(source)

    assert source == before
    assert document["schema_version"] == 4
    assert document["__source_schema_version"] == 3
    assert page_ids(document) == ("front",)
    front = document["pages"][0]
    assert front["background_path"] is None
    assert len(front["shapes"]) == len(source["shapes"])
    assert sum(bool(shape.get("is_document_background")) for shape in front["shapes"]) == 1


def test_normalization_is_idempotent_and_assigns_stable_missing_ids():
    source = legacy_fixture()
    source["boxes"][0].pop("object_id")

    first = normalize_model_document(source)
    second = normalize_model_document(first)

    assert first == second
    assert first["pages"][0]["boxes"][0]["object_id"] == "text:1"


def test_legacy_image_background_keeps_its_original_rendering_role_only_once():
    source = legacy_fixture()
    source["background_path"] = "assets/reference-image.svg"
    source["bg_props"] = {"x": 0, "y": 0, "w": 320, "h": 200, "visible": True}
    source["shapes"] = [shape for shape in source["shapes"] if not shape.get("is_document_background")]

    document = normalize_model_document(source)
    adapted = adapt_model_page(document)

    assert document["pages"][0]["background_path"] == "assets/reference-image.svg"
    assert not any(shape.get("is_document_background") for shape in document["pages"][0]["shapes"])
    assert adapted["background_path"] == "assets/reference-image.svg"


def test_two_pages_are_ordered_isolated_and_share_document_dimensions():
    document = two_page_document()
    normalized = normalize_model_document(document)

    assert page_ids(normalized) == ("front", "back")
    front = adapt_model_page(normalized, "front")
    back = adapt_model_page(normalized, "back")
    assert front["canvas_size"] == back["canvas_size"] == {"w": 320, "h": 200}
    assert front["target_w_mm"] == back["target_w_mm"] == 80.0
    assert front["shapes"][0]["fill_color"] != back["shapes"][0]["fill_color"]

    back["boxes"][0]["html"] = "alterado"
    assert normalized["pages"][1]["boxes"][0]["html"] == "<p>{Verso}</p>"


def test_add_clear_and_remove_pages_keep_a_valid_document():
    original = normalize_model_document(legacy_fixture())
    with_back = add_blank_back_page(original)
    assert page_ids(with_back) == ("front", "back")
    assert with_back["pages"][1]["field_ids"] == []
    assert with_back["pages"][1]["layer_order"] == ["shape:0"]
    assert with_back["pages"][1]["shapes"][0]["is_document_background"] is True

    cleared = clear_model_page(two_page_document(), "front")
    assert cleared["pages"][0]["boxes"] == []
    assert cleared["pages"][1]["boxes"]
    # O link da imagem existente no verso também alimenta a tabela.
    assert cleared["placeholders"] == ["Nome", "Site", "Verso"]

    promoted = remove_model_page(two_page_document(), "front")
    assert page_ids(promoted) == ("front",)
    assert promoted["pages"][0]["boxes"][0]["html"] == "<p>{Verso}</p>"
    assert promoted["placeholders"] == ["Nome", "Site", "Verso"]
    with pytest.raises(ModelValidationError, match="única página"):
        remove_model_page(promoted, "front")


def test_document_factory_builds_one_legacy_renderer_per_page():
    document = two_page_document()
    front_renderer, back_renderer = renderers_for_document(document)
    front = front_renderer.render_preview_image()
    back = back_renderer.render_preview_image()

    assert front.size() == back.size()
    assert front != back
    assert back_renderer.page_id == "back"


def test_identical_front_and_back_render_pixel_identically():
    document = normalize_model_document(legacy_fixture())
    back = copy.deepcopy(document["pages"][0])
    back["page_id"] = "back"
    for signature in back.get("signatures", []):
        signature.pop("signature_id", None)
    document["pages"].append(back)
    document.pop("__source_schema_version", None)
    row = {
        "Nome": "Ada", "Cargo": "Referência",
        "Site": "https://example.com", "__use_signature__": True,
    }

    front_renderer, back_renderer = renderers_for_document(document)

    assert front_renderer.tpl != back_renderer.tpl  # identidade da página é independente
    assert front_renderer.render_to_qimage(row, row) == back_renderer.render_to_qimage(row, row)


def test_renderer_keeps_links_scoped_to_the_rendered_page():
    document = two_page_document()
    for page in document["pages"]:
        for collection in ("boxes", "images", "shapes"):
            for item in page[collection]:
                item["has_link"] = False
    back_shape = document["pages"][1]["shapes"][0]
    back_shape["has_link"] = True
    back_shape["link_key"] = "SiteVerso"
    front_links = []
    back_links = []
    values = {"SiteVerso": "https://example.com/verso"}

    front_renderer, back_renderer = renderers_for_document(document)
    front_renderer.render_to_qimage(values, values, front_links)
    back_renderer.render_to_qimage(values, values, back_links)

    assert front_links == []
    assert [entry["url"] for entry in back_links] == ["https://example.com/verso"]


def test_adapter_preserves_single_page_rendering_exactly():
    source = legacy_fixture()
    source["__model_dir"] = str(FIXTURE.parent)
    row = {"Nome": "Ada", "Cargo": "Referência", "Site": "https://example.com", "__use_signature__": True}

    legacy_image = NativeRenderer(source).render_to_qimage(row, row)
    adapted_image = NativeRenderer(adapt_model_page(normalize_model_document(source))).render_to_qimage(row, row)

    assert legacy_image == adapted_image


@pytest.mark.parametrize("mutate", [
    lambda data: data.update(pages=[]),
    lambda data: data["pages"].append(copy.deepcopy(data["pages"][0])),
    lambda data: data["pages"][0].update(page_id="back"),
    lambda data: data["pages"][0].update(canvas_size={"w": 1, "h": 1}),
    lambda data: data.update(canvas_size={"w": 0, "h": 200}),
    lambda data: data["pages"][0]["boxes"].append(copy.deepcopy(data["pages"][0]["boxes"][0])),
])
def test_invalid_v4_documents_are_rejected(mutate):
    document = two_page_document()
    mutate(document)
    with pytest.raises(ModelValidationError):
        normalize_model_document(document)


@pytest.mark.parametrize("canvas", [
    {"w": MAX_CANVAS_DIMENSION + 1, "h": 1},
    {"w": 8_001, "h": 4_000},
    {"w": 320.5, "h": 200},
])
def test_canvas_dimensions_are_bounded_before_rendering(canvas):
    document = two_page_document()
    document["canvas_size"] = canvas

    with pytest.raises(ModelValidationError, match="canvas|pixels"):
        normalize_model_document(document)


def test_canvas_accepts_the_documented_pixel_area_boundary():
    document = two_page_document()
    document["canvas_size"] = {"w": 8_000, "h": 4_000}

    normalized = normalize_model_document(document)

    assert normalized["canvas_size"]["w"] * normalized["canvas_size"]["h"] == MAX_CANVAS_PIXELS


def test_physical_dimensions_are_bounded():
    document = two_page_document()
    document["target_w_mm"] = MAX_PHYSICAL_DIMENSION_MM + 1

    with pytest.raises(ModelValidationError, match="dimensões físicas"):
        normalize_model_document(document)


@pytest.mark.parametrize("key,value", [
    ("x", float("inf")),
    ("rotation", float("nan")),
    ("w", 0),
])
def test_object_geometry_must_be_finite_and_bounded(key, value):
    document = two_page_document()
    document["pages"][0]["boxes"][0][key] = value

    with pytest.raises(ModelValidationError, match="objeto|Geometria"):
        normalize_model_document(document)


@pytest.mark.parametrize("html", [
    '<p>Texto<img src="file:///tmp/private.png"></p>',
    '<p style="background-image:url(../../private.png)">Texto</p>',
    '<link rel="stylesheet" href="file:///tmp/private.css"><p>Texto</p>',
    '<object data="https://example.invalid/content"></object>',
])
def test_model_text_rejects_external_or_graphical_resources(html):
    document = two_page_document()
    document["pages"][0]["boxes"][0]["html"] = html

    with pytest.raises(ModelValidationError, match="recurso externo"):
        normalize_model_document(document)


def test_unknown_version_is_rejected_explicitly():
    with pytest.raises(UnsupportedSchemaError, match="99"):
        normalize_model_document({"schema_version": 99})


def test_loader_prefers_v4_and_never_falls_back_when_it_is_invalid(tmp_path):
    (tmp_path / "template_v3.json").write_text(json.dumps(legacy_fixture()), encoding="utf-8")
    (tmp_path / "template_v4.json").write_text("{ inválido", encoding="utf-8")

    assert resolve_model_file(tmp_path).name == "template_v4.json"
    with pytest.raises(ModelDocumentError, match="template_v4.json"):
        load_model_document(tmp_path)


def test_loader_uses_v3_when_v4_does_not_exist_and_records_origin(tmp_path):
    legacy_path = tmp_path / "template_v3.json"
    legacy_path.write_text(json.dumps(legacy_fixture()), encoding="utf-8")

    document = load_model_document(tmp_path)

    assert document["schema_version"] == 4
    assert document["__model_dir"] == str(tmp_path.resolve())
    assert document["__model_file"] == str(legacy_path.resolve())


def test_replace_page_preserves_inactive_page_and_rebuilds_global_fields():
    document = two_page_document()
    front = adapt_model_page(document, "front")
    front["boxes"][0]["html"] = "<p>{Novo}</p>"
    front["placeholders"] = ["Novo", "Site"]

    changed = replace_model_page(document, front, "front")

    assert changed["pages"][0]["boxes"][0]["html"] == "<p>{Novo}</p>"
    assert changed["pages"][1] == document["pages"][1]
    assert changed["placeholders"] == ["Novo", "Site", "Nome", "Verso"]
    assert "__source_schema_version" not in changed


def test_persistent_document_strips_runtime_metadata_recursively():
    document = two_page_document()
    document["__model_dir"] = "/temporário"
    document["pages"][0]["boxes"][0]["__selection"] = True

    persistent = persistent_model_document(document)

    assert persistent["schema_version"] == 4
    assert "__model_dir" not in persistent
    assert "__selection" not in persistent["pages"][0]["boxes"][0]


def test_atomic_save_keeps_legacy_file_and_round_trips_two_pages(tmp_path):
    legacy = tmp_path / "template_v3.json"
    legacy.write_text(json.dumps(legacy_fixture()), encoding="utf-8")
    legacy_before = legacy.read_bytes()

    target = save_model_document(two_page_document(), tmp_path)
    loaded = load_model_document(tmp_path)

    assert target.name == "template_v4.json"
    assert legacy.read_bytes() == legacy_before
    assert page_ids(loaded) == ("front", "back")
    assert not list(tmp_path.glob(".template_v4.json.*.tmp"))


def test_failed_atomic_save_does_not_replace_previous_document(tmp_path, monkeypatch):
    first = two_page_document()
    target = save_model_document(first, tmp_path)
    original = target.read_bytes()
    changed = copy.deepcopy(first)
    changed["name"] = "Alterado"

    def fail_replace(self, _target):
        raise OSError("disco cheio")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="disco cheio"):
        save_model_document(changed, tmp_path)

    assert target.read_bytes() == original
    assert not list(tmp_path.glob(".template_v4.json.*.tmp"))


def test_successful_resave_keeps_previous_v4_as_recovery(tmp_path):
    original = two_page_document()
    save_model_document(original, tmp_path)
    changed = copy.deepcopy(original)
    changed["name"] = "Alterado"

    save_model_document(changed, tmp_path)
    recovery = load_recovery_documents(tmp_path)

    assert load_model_document(tmp_path)["name"] == "Alterado"
    assert recovery[0]["name"] == original["name"]


def test_removed_back_can_be_restored_from_recovery(tmp_path):
    original = two_page_document()
    save_model_document(original, tmp_path)
    front_only = copy.deepcopy(original)
    front_only["pages"] = front_only["pages"][:1]
    front_only["placeholders"] = front_only["pages"][0]["field_ids"]

    save_model_document(front_only, tmp_path)
    assert page_ids(load_model_document(tmp_path)) == ("front",)

    previous = load_recovery_documents(tmp_path)[0]
    assert page_ids(previous) == ("front", "back")
    save_model_document(previous, tmp_path)
    assert page_ids(load_model_document(tmp_path)) == ("front", "back")


def test_asset_inventory_includes_both_pages_and_shared_paths():
    document = two_page_document()
    document["pages"][1]["images"][0]["path"] = "assets/back-only.svg"

    assets = list(iter_page_asset_paths(document))

    assert ("front", "images", "assets/reference-image.svg") in assets
    assert ("back", "images", "assets/back-only.svg") in assets
    assert sum(path.endswith("reference-signature.svg") for _, _, path in assets) == 2


def test_link_inventory_includes_link_used_only_by_back():
    document = two_page_document()
    for page in document["pages"]:
        for collection in ("boxes", "images", "shapes"):
            for item in page[collection]:
                item["has_link"] = False
    document["pages"][1]["shapes"][0]["has_link"] = True
    document["pages"][1]["shapes"][0]["link_key"] = "SiteVerso"

    links = list(iter_page_link_items(document))

    assert len(links) == 1
    assert links[0][0:2] == ("back", "shapes")


def test_global_fields_merge_both_pages_links_and_keep_user_order():
    document = two_page_document()
    document["placeholders"] = ["Verso", "Nome", "Cargo", "Site"]
    back_shape = document["pages"][1]["shapes"][0]
    back_shape["has_link"] = True
    back_shape["link_key"] = "Link - Página institucional"

    normalized = normalize_model_document(document)

    assert normalized["placeholders"] == [
        "Verso", "Nome", "Cargo", "Site", "Link - Página institucional",
    ]
    assert normalized["placeholders"].count("Nome") == 1
    # Normalizar a união não reescreve silenciosamente a página inativa.
    assert normalized["pages"][1]["field_ids"] == ["Nome", "Verso"]


def test_replacing_one_page_keeps_fields_from_the_other_and_drops_orphans():
    document = two_page_document()
    back_shape = document["pages"][1]["shapes"][0]
    back_shape["has_link"] = True
    back_shape["link_key"] = "Link do verso"
    front = adapt_model_page(document, "front")
    front["placeholders"] = ["Verso", "Matrícula", "Nome", "Link do verso"]
    front["__page_field_ids"] = ["Matrícula"]
    front["__page_fields_authoritative"] = True

    changed = replace_model_page(document, front, "front")

    assert changed["pages"][0]["field_ids"] == ["Matrícula"]
    assert changed["pages"][1]["field_ids"] == ["Nome", "Verso"]
    assert changed["placeholders"] == ["Verso", "Matrícula", "Nome", "Link do verso", "Site"]
    assert "Cargo" not in changed["placeholders"]


def test_signatures_are_collected_from_front_and_back():
    document = two_page_document()
    document["pages"][1]["signatures"][0]["visible"] = False

    signatures = document_signatures(document)

    assert len(signatures) == 2
    assert [signature["visible"] for signature in signatures] == [True, False]


def test_signatures_receive_stable_document_wide_ids_independent_from_names():
    source = legacy_fixture()
    source["signatures"].append(copy.deepcopy(source["signatures"][0]))
    source["signatures"][0]["custom_name"] = "Diretor"
    source["signatures"][1]["custom_name"] = "Diretor"
    source["signatures"][1]["layer_id"] = 999

    first = normalize_model_document(source)
    second = normalize_model_document(source)
    first_signatures = first["pages"][0]["signatures"]
    second_signatures = second["pages"][0]["signatures"]

    assert len({item["signature_id"] for item in first_signatures}) == 2
    assert [item["signature_id"] for item in first_signatures] == [
        item["signature_id"] for item in second_signatures
    ]
    original_id = first_signatures[0]["signature_id"]
    first_signatures[0]["custom_name"] = "Reitor"
    assert first_signatures[0]["signature_id"] == original_id


def test_duplicate_signature_ids_are_rejected_across_pages():
    document = two_page_document()
    duplicated = document["pages"][0]["signatures"][0]["signature_id"]
    document["pages"][1]["signatures"][0]["signature_id"] = duplicated

    with pytest.raises(ModelValidationError, match="signature_id repetido"):
        normalize_model_document(document)


def test_font_inventory_includes_plain_and_rich_fonts_from_back():
    document = two_page_document()
    back_box = document["pages"][1]["boxes"][0]
    back_box["font_family"] = "Fonte do Verso"
    back_box["rich_text_version"] = 1
    back_box["html"] = '<span style="font-family:Fonte Rica do Verso">Verso</span>'

    fonts = template_font_families(document)

    assert "Fonte do Verso" in fonts
    assert "Fonte Rica do Verso" in fonts


def test_editor_save_of_front_preserves_back_page(tmp_path, monkeypatch):
    model_dir = tmp_path / "modelo_teste"
    document = two_page_document()
    document["name"] = "Modelo Teste"
    saved = save_model_document(document, model_dir)
    back_before = persistent_model_document(document)["pages"][1]
    monkeypatch.setattr("features.editor.editor_window.get_models_dir", lambda: tmp_path)

    window = EditorWindow()
    try:
        window.load_from_json(model_dir)
        window.export_to_json(skip_close_dialog=True)
        reloaded = load_model_document(model_dir)
    finally:
        window._last_saved_state = window.get_current_scene_state()
        window.close()

    assert saved.exists()
    assert reloaded["pages"][1] == back_before
    assert page_ids(reloaded) == ("front", "back")


def test_editor_asset_cleanup_keeps_asset_used_only_by_back(tmp_path):
    model_dir = tmp_path / "modelo_teste"
    assets_dir = model_dir / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "front.svg").write_text("<svg/>", encoding="utf-8")
    (assets_dir / "back.svg").write_text("<svg/>", encoding="utf-8")
    (assets_dir / "orphan.svg").write_text("<svg/>", encoding="utf-8")
    document = two_page_document()
    document["pages"][0]["images"][0]["path"] = "assets/front.svg"
    document["pages"][1]["images"][0]["path"] = "assets/back.svg"
    save_model_document(document, model_dir)

    window = EditorWindow()
    try:
        window._current_model_dir = model_dir
        window._cleanup_unused_assets_on_close()
    finally:
        window._last_saved_state = window.get_current_scene_state()
        window.close()

    assert (assets_dir / "front.svg").exists()
    assert (assets_dir / "back.svg").exists()
    assert not (assets_dir / "orphan.svg").exists()


def test_editor_asset_cleanup_keeps_asset_referenced_by_recovery(tmp_path):
    model_dir = tmp_path / "modelo_teste"
    assets_dir = model_dir / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "previous.svg").write_text("<svg/>", encoding="utf-8")
    previous = two_page_document()
    previous["pages"][1]["images"][0]["path"] = "assets/previous.svg"
    save_model_document(previous, model_dir)
    current = copy.deepcopy(previous)
    removed_image_id = current["pages"][1]["images"][0]["object_id"]
    current["pages"][1]["images"] = []
    current["pages"][1]["layer_order"] = [
        item for item in current["pages"][1]["layer_order"]
        if item != removed_image_id
    ]
    save_model_document(current, model_dir)

    window = EditorWindow()
    try:
        window._current_model_dir = model_dir
        window._cleanup_unused_assets_on_close()
    finally:
        window._last_saved_state = window.get_current_scene_state()
        window.close()

    assert (assets_dir / "previous.svg").exists()


def test_model_directory_install_replaces_document_and_assets_together(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "library" / "model"
    (source / "assets").mkdir(parents=True)
    (source / "assets" / "new.svg").write_text("new", encoding="utf-8")
    incoming = two_page_document()
    incoming["pages"][1]["images"][0]["path"] = "assets/new.svg"
    save_model_document(incoming, source)
    target.mkdir(parents=True)
    (target / "old.txt").write_text("old", encoding="utf-8")

    installed = install_model_directory(source, target)

    assert installed == target
    assert page_ids(load_model_document(target)) == ("front", "back")
    assert (target / "assets" / "new.svg").read_text(encoding="utf-8") == "new"
    assert not (target / "old.txt").exists()
    assert not list(target.parent.glob(".model.import-*"))
    assert not list(target.parent.glob(".model.backup-*"))


def test_background_proxies_are_isolated_by_page(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "front.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><rect width="8" height="8" fill="red"/></svg>',
        encoding="utf-8",
    )
    (assets / "back.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><rect width="8" height="8" fill="blue"/></svg>',
        encoding="utf-8",
    )
    document = two_page_document()
    front = adapt_model_page(document, "front")
    back = adapt_model_page(document, "back")
    for page, filename in ((front, "front.svg"), (back, "back.svg")):
        page["__model_dir"] = str(tmp_path)
        page["background_path"] = f"assets/{filename}"
        page["bg_props"] = {"x": 0, "y": 0, "w": 320, "h": 200, "visible": True}

    front_proxy = ensure_background_proxy(tmp_path, front)
    back_proxy = ensure_background_proxy(tmp_path, back)

    assert front_proxy and back_proxy and front_proxy != back_proxy
    assert get_background_proxy_path(tmp_path, front) == front_proxy
    assert get_background_proxy_path(tmp_path, back) == back_proxy
    assert QColor(QImage(str(front_proxy)).pixel(10, 10)).red() > 200
    assert QColor(QImage(str(back_proxy)).pixel(10, 10)).blue() > 200


def test_thumbnail_cache_uses_page_and_document_revision(tmp_path):
    source = save_model_document(two_page_document(), tmp_path)
    front_image = QImage(10, 10, QImage.Format.Format_ARGB32)
    front_image.fill(QColor("red"))
    back_image = QImage(10, 10, QImage.Format.Format_ARGB32)
    back_image.fill(QColor("blue"))

    front_path = publish_thumbnail_cache(tmp_path, source, front_image, "front")
    back_path = publish_thumbnail_cache(tmp_path, source, back_image, "back")

    assert front_path != back_path
    assert get_thumbnail_cache_path(tmp_path, source, "front") == front_path
    assert get_thumbnail_cache_path(tmp_path, source, "back") == back_path

    changed = two_page_document()
    changed["name"] = "Nova revisão"
    save_model_document(changed, tmp_path)
    assert get_thumbnail_cache_path(tmp_path, source, "front") is None
    assert get_thumbnail_cache_path(tmp_path, source, "back") is None


def test_renderer_fork_does_not_share_mutable_caches():
    renderer = NativeRenderer(adapt_model_page(two_page_document(), "front"))
    renderer.pre_render_static_base()
    fork = renderer.fork()

    assert fork._image_cache is not renderer._image_cache
    assert fork._pixmap_cache is not renderer._pixmap_cache
    assert fork._static_base_cache is not renderer._static_base_cache
    assert fork._static_base_cache == renderer._static_base_cache
