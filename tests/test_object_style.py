from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath

from core.object_style import rounded_rect_path


def test_half_size_corner_radii_match_a_circle():
    bounds = QRectF(0, 0, 200, 200)
    rounded = rounded_rect_path(bounds, {
        "top_left": 100,
        "top_right": 100,
        "bottom_right": 100,
        "bottom_left": 100,
    })
    circle = QPainterPath()
    circle.addEllipse(bounds)

    # Os caminhos podem começar em pontos diferentes, então comparamos sua área.
    assert rounded.subtracted(circle).isEmpty()
    assert circle.subtracted(rounded).isEmpty()


def test_independent_corner_radii_keep_straight_edges_between_arcs():
    path = rounded_rect_path(QRectF(0, 0, 200, 100), {
        "top_left": 10,
        "top_right": 20,
        "bottom_right": 30,
        "bottom_left": 40,
    })

    assert path.contains(QRectF(100, 50, 1, 1).center())
    assert not path.contains(QRectF(0, 0, 1, 1).center())
