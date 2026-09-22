import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QImage

from core.dynamic_images import dynamic_image_fields, resolve_dynamic_image
from core.model_document import normalize_model_document
from features.generator.renderer import NativeRenderer


def _shape(field="Foto", fit="cover"):
    return {
        "object_id": "shape:1", "layer_id": 1, "custom_name": "Foto",
        "shape_type": "rectangle", "x": 0, "y": 0,
        "width": 100, "height": 100, "rotation": 0, "z_value": 1,
        "visible": True, "opacity": 1.0, "locked": False,
        "fill_color": "#ffffff", "fill_opacity": 1.0,
        "outline_enabled": False, "outline_color": "#000000",
        "outline_opacity": 1.0, "outline_width": 1.0,
        "outline_position": "inside", "outline_join": "miter",
        "corner_radius": 0.0, "corner_radii": {},
        "corner_radii_linked": True,
        "dynamic_image_field": field, "dynamic_image_fit": fit,
    }


def _template(shape):
    return {
        "name": "Dinâmico", "canvas_size": {"w": 100, "h": 100},
        "target_w_mm": 10.0, "target_h_mm": 10.0,
        "placeholders": [shape["dynamic_image_field"]],
        "shapes": [shape], "images": [], "boxes": [], "signatures": [],
        "background_path": None, "layer_order": [shape["object_id"]],
    }


def test_resolver_accepts_filename_with_or_without_extension_and_rejects_ambiguity(tmp_path):
    (tmp_path / "ana.png").write_bytes(b"png")
    assert resolve_dynamic_image(tmp_path, "ana").path == tmp_path / "ana.png"
    assert resolve_dynamic_image(tmp_path, "ana.png").path == tmp_path / "ana.png"

    (tmp_path / "ana.jpg").write_bytes(b"jpg")
    assert resolve_dynamic_image(tmp_path, "ana").status == "ambiguous"
    assert resolve_dynamic_image(tmp_path, "../ana.png").status == "invalid"


def test_resolver_rejects_symlink_that_leaves_selected_directory(tmp_path):
    root = tmp_path / "selected"
    root.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")
    link = root / "photo.png"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("O ambiente não permite links simbólicos.")

    result = resolve_dynamic_image(root, "photo.png")

    assert result.path is None
    assert result.status == "invalid"


def test_resolver_accepts_subdirectory_and_internal_symlink(tmp_path):
    photos = tmp_path / "photos"
    photos.mkdir()
    actual = photos / "inside.png"
    actual.write_bytes(b"inside")
    link = tmp_path / "alias.png"
    try:
        link.symlink_to(actual)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("O ambiente não permite links simbólicos.")

    assert resolve_dynamic_image(tmp_path, "photos/inside.png").path == actual
    assert resolve_dynamic_image(tmp_path, "alias.png").path == actual


def test_dynamic_field_enters_document_placeholder_union():
    shape = _shape()
    source = _template(shape)
    source.update({
        "schema_version": 4,
        "pages": [{
            "page_id": "front", "field_ids": [], "shapes": [shape],
            "images": [], "boxes": [], "signatures": [], "guidelines": [],
            "background_path": None, "layer_order": [shape["object_id"]],
        }],
    })
    for key in ("shapes", "images", "boxes", "signatures", "background_path", "layer_order"):
        source.pop(key, None)

    document = normalize_model_document(source)

    assert dynamic_image_fields(document) == ["Foto"]
    assert "Foto" in document["placeholders"]


def test_renderer_uses_external_image_for_the_selected_row(tmp_path):
    image = QImage(40, 20, QImage.Format.Format_ARGB32)
    image.fill(QColor("#d92727"))
    assert image.save(str(tmp_path / "ana.png"), "PNG")
    renderer = NativeRenderer(_template(_shape())).set_dynamic_image_directory(tmp_path)

    rendered = renderer.render_to_qimage({"Foto": "ana"}, {"Foto": "ana"})

    assert rendered.pixelColor(50, 50).red() > 180
    assert rendered.pixelColor(50, 50).green() < 80


def test_dynamic_shape_is_not_baked_into_static_preview_cache(tmp_path):
    first = QImage(20, 20, QImage.Format.Format_ARGB32)
    first.fill(QColor("#d92727"))
    second = QImage(20, 20, QImage.Format.Format_ARGB32)
    second.fill(QColor("#27b35a"))
    assert first.save(str(tmp_path / "primeira.png"), "PNG")
    assert second.save(str(tmp_path / "segunda.png"), "PNG")
    renderer = NativeRenderer(_template(_shape())).set_dynamic_image_directory(tmp_path)
    renderer.pre_render_static_base()

    rendered_first = renderer.render_to_qimage({"Foto": "primeira"}, {"Foto": "primeira"})
    rendered_second = renderer.render_to_qimage({"Foto": "segunda"}, {"Foto": "segunda"})

    assert rendered_first.pixelColor(50, 50).red() > 180
    assert rendered_second.pixelColor(50, 50).green() > 130


def test_contain_preserves_empty_area_while_cover_fills_the_shape(tmp_path):
    image = QImage(80, 20, QImage.Format.Format_ARGB32)
    image.fill(QColor("#2367d1"))
    assert image.save(str(tmp_path / "faixa.png"), "PNG")
    contain = NativeRenderer(_template(_shape(fit="contain"))).set_dynamic_image_directory(tmp_path)
    cover = NativeRenderer(_template(_shape(fit="cover"))).set_dynamic_image_directory(tmp_path)

    contained = contain.render_to_qimage({"Foto": "faixa"}, {"Foto": "faixa"})
    covered = cover.render_to_qimage({"Foto": "faixa"}, {"Foto": "faixa"})

    assert contained.pixelColor(50, 5) == QColor("#ffffff")
    assert covered.pixelColor(50, 5).blue() > 150
