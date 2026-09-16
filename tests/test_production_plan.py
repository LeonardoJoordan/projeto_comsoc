import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from features.generator.production_plan import build_imposition_plan
from features.preview.preview_panel import PreviewPanel


def _settings(**overrides):
    settings = {
        "target_w_mm": 50.0,
        "target_h_mm": 50.0,
        "sheet_w_mm": 100.0,
        "sheet_h_mm": 100.0,
        "crop_marks": False,
        "bleed_margin": False,
    }
    settings.update(overrides)
    return settings


def test_imposition_plan_uses_assembler_capacity_and_keeps_final_partial_page():
    plan = build_imposition_plan(list(range(10)), _settings())

    assert plan.capacity == 4
    assert plan.pages == ((0, 1, 2, 3), (4, 5, 6, 7), (8, 9))


def test_imposition_plan_reports_no_pages_when_item_does_not_fit():
    plan = build_imposition_plan([1], _settings(target_w_mm=200.0))

    assert plan.capacity == 0
    assert plan.pages == ()


def test_duplex_plan_keeps_a4_portrait_and_reverses_columns_on_back():
    plan = build_imposition_plan(
        ["A", "B", "C", "D"],
        _settings(duplex=True),
    )

    assert plan.duplex is True
    assert plan.assembler.sheet_w_mm == 100.0
    assert plan.assembler.sheet_h_mm == 100.0
    assert plan.sheets[0].front == ("A", "B", "C", "D")
    assert plan.sheets[0].back == ("B", "A", "D", "C")


def test_duplex_partial_sheet_preserves_empty_physical_slots():
    plan = build_imposition_plan(["A", "B", "C"], _settings(duplex=True))

    assert plan.sheets[0].front == ("A", "B", "C", None)
    assert plan.sheets[0].back == ("B", "A", None, "C")


def test_duplex_preserves_automatic_landscape_rotation_and_maps_back_rows():
    settings = _settings(
        target_w_mm=60.0, target_h_mm=40.0,
        sheet_w_mm=100.0, sheet_h_mm=140.0,
    )
    normal = build_imposition_plan([1], settings)
    duplex = build_imposition_plan([1], {**settings, "duplex": True})

    assert normal.assembler.sheet_w_mm == 140.0
    assert normal.assembler.sheet_h_mm == 100.0
    assert duplex.assembler.sheet_w_mm == 140.0
    assert duplex.assembler.sheet_h_mm == 100.0
    plan = build_imposition_plan(["A", "B", "C", "D"], {**settings, "duplex": True})
    assert plan.sheets[0].front == ("A", "B", "C", "D")
    assert plan.sheets[0].back == ("C", "D", "A", "B")


def test_preview_navigation_only_offers_sheet_mode_when_available():
    app = QApplication.instance() or QApplication([])
    panel = PreviewPanel()

    panel.set_navigation("sheet", 1, 3, sheet_available=False)
    assert panel.cbo_preview_mode.count() == 1
    assert panel.cbo_preview_mode.currentData() == "item"

    panel.set_navigation("sheet", 1, 3, sheet_available=True)
    assert panel.cbo_preview_mode.count() == 2
    assert panel.cbo_preview_mode.currentData() == "sheet"
    assert panel.spin_navigation.value() == 2
    assert panel.lbl_navigation_total.text() == "de 3"
    assert panel.lbl_navigation_kind.text() == "Folha"

    panel.set_navigation("item", 0, 3, sheet_available=True)
    assert panel.lbl_navigation_kind.text() == "Item"

    panel.deleteLater()
    app.processEvents()


def test_preview_page_selector_only_appears_for_front_and_back_models():
    app = QApplication.instance() or QApplication([])
    panel = PreviewPanel()
    requested = []
    panel.pageChanged.connect(requested.append)

    panel.set_page_navigation(1, 0)
    assert panel.page_selector.isHidden()

    panel.set_page_navigation(2, 1)
    assert not panel.page_selector.isHidden()
    assert panel.btn_back.isChecked()
    panel.btn_front.click()
    assert requested == [0]

    panel.deleteLater()
    app.processEvents()
