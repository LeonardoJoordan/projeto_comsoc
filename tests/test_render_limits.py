import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from core.model_document import MAX_CANVAS_DIMENSION, ModelValidationError
from features.generator.imposition import SheetAssembler
from features.generator.manager import _bounded_worker_count
from features.generator.renderer import NativeRenderer


class _Renderer:
    def __init__(self, width, height):
        self.tpl = {"canvas_size": {"w": width, "h": height}}


def test_renderer_rejects_oversized_legacy_input_before_qimage_allocation():
    source = {
        "canvas_size": {"w": MAX_CANVAS_DIMENSION + 1, "h": 1},
        "boxes": [], "images": [], "signatures": [], "shapes": [],
    }

    with pytest.raises(ModelValidationError, match="limite seguro"):
        NativeRenderer(source)


def test_imposition_rejects_a_sheet_that_exceeds_the_raster_budget():
    with pytest.raises(ModelValidationError, match="folha de impressão"):
        SheetAssembler(100, 150, sheet_w_mm=5_000, sheet_h_mm=5_000)


def test_worker_count_is_reduced_for_large_canvases():
    renderers = [_Renderer(8_000, 4_000), _Renderer(8_000, 4_000)]

    assert _bounded_worker_count(30, renderers) == 4


def test_worker_count_keeps_requested_parallelism_for_normal_canvas():
    assert _bounded_worker_count(6, [_Renderer(1_000, 1_000)]) == 6
