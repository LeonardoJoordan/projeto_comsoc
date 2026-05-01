import math
import re
from pathlib import Path
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsRectItem, QGraphicsTextItem,
                               QGraphicsItem, QInputDialog, QLineEdit, QGraphicsPixmapItem,
                               QStyle)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (QPen, QBrush, QColor, QFont, QTextCursor,
                           QTextBlockFormat, QPixmap, QPainterPathStroker, QTextCharFormat,
                           QImageReader, QPainterPath, QFontMetrics)
from core.text_state import TextState

DPI = 300

def mm_to_px(mm):
    return (mm * DPI) / 25.4

def px_to_mm(px):
    return (px * 25.4) / DPI


def _rotated_point(position, origin, angle, point):
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    dx = point.x() - origin.x()
    dy = point.y() - origin.y()
    return QPointF(
        position.x() + origin.x() + (dx * cos_a - dy * sin_a),
        position.y() + origin.y() + (dx * sin_a + dy * cos_a),
    )


def _rotated_vector(point, angle):
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    return QPointF(
        point.x() * cos_a - point.y() * sin_a,
        point.x() * sin_a + point.y() * cos_a,
    )


def _unrotated_vector(point, angle):
    return _rotated_vector(point, -angle)


def _item_pos_for_local_scene_point(item, local_point, scene_point):
    origin = item.transformOriginPoint()
    local_from_origin = QPointF(local_point.x() - origin.x(), local_point.y() - origin.y())
    rotated_from_origin = _rotated_vector(local_from_origin, item.rotation())
    return QPointF(
        scene_point.x() - origin.x() - rotated_from_origin.x(),
        scene_point.y() - origin.y() - rotated_from_origin.y(),
    )


def _document_rect(scene):
    rect = getattr(scene, "_document_rect", None)
    if rect is not None:
        return QRectF(rect)
    return scene.sceneRect()


def _snap_targets(scene):
    vertical_targets = []
    horizontal_targets = []

    rect = _document_rect(scene)
    if not rect.isEmpty():
        vertical_targets.extend((rect.left(), rect.right()))
        horizontal_targets.extend((rect.top(), rect.bottom()))

    for item in scene.items():
        if isinstance(item, Guideline):
            if item.is_vertical:
                vertical_targets.append(item.x())
            else:
                horizontal_targets.append(item.y())

    return vertical_targets, horizontal_targets

def _get_dynamic_snap_distance(scene):
    if not scene: 
        return 15.0
    
    rect = _document_rect(scene)
    media_lados = (rect.width() + rect.height()) / 2.0
    base_dist = max(5.0, media_lados * 0.008)
    
    zoom = 1.0
    if scene.views():
        zoom = max(0.001, scene.views()[0].transform().m11())
        
    return base_dist / math.sqrt(zoom)


def _snap_position_to_guides(item, new_pos, w, h):
    # BLINDAGEM: O ímã só atua se o usuário estiver ativamente arrastando o item com o mouse
    if not getattr(item, '_is_mouse_dragging', False):
        return new_pos

    scene = item.scene()
    if not scene:
        return new_pos

    origin = item.transformOriginPoint()
    angle = item.rotation()
    local_points = [
        QPointF(0, 0),
        QPointF(w, 0),
        QPointF(w, h),
        QPointF(0, h),
    ]
    scene_points = [_rotated_point(new_pos, origin, angle, p) for p in local_points]
    center = _rotated_point(new_pos, origin, angle, QPointF(w / 2, h / 2))

    xs = [p.x() for p in scene_points]
    ys = [p.y() for p in scene_points]
    x_candidates = [min(xs), center.x(), max(xs)]
    y_candidates = [min(ys), center.y(), max(ys)]

    best_dx = 0
    best_dy = 0
    
    dynamic_snap = _get_dynamic_snap_distance(scene)
    min_dist_x = dynamic_snap
    min_dist_y = dynamic_snap

    vertical_targets, horizontal_targets = _snap_targets(scene)
    for target_x in vertical_targets:
        for x in x_candidates:
            dist = abs(x - target_x)
            if dist < min_dist_x:
                min_dist_x = dist
                best_dx = target_x - x

    for target_y in horizontal_targets:
        for y in y_candidates:
            dist = abs(y - target_y)
            if dist < min_dist_y:
                min_dist_y = dist
                best_dy = target_y - y

    return QPointF(new_pos.x() + best_dx, new_pos.y() + best_dy)


class ResizeHandle(QGraphicsRectItem):
    MIN_WIDTH = 40
    MIN_HEIGHT = 30

    def __init__(self, parent, name, x_dir, y_dir, cursor):
        super().__init__(-6, -6, 12, 12, parent)
        self.name = name
        self.x_dir = x_dir
        self.y_dir = y_dir
        self.setBrush(QBrush(QColor("#27ae60")))
        self.setPen(QPen(Qt.GlobalColor.white, 2))
        self.setAcceptHoverEvents(True)
        self.setCursor(cursor)
        self.setZValue(1000)
        self._is_resizing = False
        self._anchor_scene = None
        self._initial_w = 1.0
        self._initial_h = 1.0
        self.initial_ratio = 1.0

    def _anchor_local_point(self, w, h):
        if self.x_dir < 0:
            anchor_x = w
        elif self.x_dir > 0:
            anchor_x = 0
        else:
            anchor_x = w / 2

        if self.y_dir < 0:
            anchor_y = h
        elif self.y_dir > 0:
            anchor_y = 0
        else:
            anchor_y = h / 2

        return QPointF(anchor_x, anchor_y)

    def _resize_from_local_delta(self, local_delta):
        ratio = self.initial_ratio if self.initial_ratio > 0 else 1.0
        keep_proportion = getattr(self.parentItem(), 'keep_proportion', True)

        if self.x_dir and self.y_dir:
            raw_w = local_delta.x() * self.x_dir
            raw_h = local_delta.y() * self.y_dir
            if keep_proportion:
                diagonal = QPointF(1.0, 1.0 / ratio)
                diagonal_len_sq = diagonal.x() ** 2 + diagonal.y() ** 2
                projected_w = (
                    (raw_w * diagonal.x() + raw_h * diagonal.y())
                    / diagonal_len_sq
                )
                min_w = max(self.MIN_WIDTH, self.MIN_HEIGHT * ratio)
                new_w = max(min_w, projected_w)
                new_h = new_w / ratio
            else:
                new_w = max(self.MIN_WIDTH, raw_w)
                new_h = max(self.MIN_HEIGHT, raw_h)

        elif self.x_dir:
            raw_w = local_delta.x() * self.x_dir
            if keep_proportion:
                min_w = max(self.MIN_WIDTH, self.MIN_HEIGHT * ratio)
                new_w = max(min_w, raw_w)
                new_h = new_w / ratio
            else:
                new_w = max(self.MIN_WIDTH, raw_w)
                new_h = self._initial_h

        elif self.y_dir:
            raw_h = local_delta.y() * self.y_dir
            if keep_proportion:
                min_h = max(self.MIN_HEIGHT, self.MIN_WIDTH / ratio)
                new_h = max(min_h, raw_h)
                new_w = new_h * ratio
            else:
                new_w = self._initial_w
                new_h = max(self.MIN_HEIGHT, raw_h)

        else:
            new_w = self._initial_w
            new_h = self._initial_h

        return new_w, new_h

    def _active_point_factors(self):
        if self.x_dir and self.y_dir:
            fx = 1.0 if self.x_dir > 0 else 0.0
            fy = 1.0 if self.y_dir > 0 else 0.0
            return [(fx, fy)]

        if self.x_dir:
            fx = 1.0 if self.x_dir > 0 else 0.0
            return [(fx, 0.5)]

        if self.y_dir:
            fy = 1.0 if self.y_dir > 0 else 0.0
            return [(0.5, fy)]

        return []

    def _scene_point_from_factors(self, parent, anchor_scene, w, h, fx, fy):
        anchor_local = self._anchor_local_point(w, h)
        local_point = QPointF(w * fx, h * fy)
        local_delta = QPointF(
            local_point.x() - anchor_local.x(),
            local_point.y() - anchor_local.y(),
        )
        rotated_delta = _rotated_vector(local_delta, parent.rotation())
        return QPointF(
            anchor_scene.x() + rotated_delta.x(),
            anchor_scene.y() + rotated_delta.y(),
        )

    def _size_for_control(self, control_axis, control_value, base_w, base_h):
        ratio = self.initial_ratio if self.initial_ratio > 0 else 1.0
        keep_proportion = getattr(self.parentItem(), 'keep_proportion', True)

        if keep_proportion:
            if control_axis == "w":
                min_w = max(self.MIN_WIDTH, self.MIN_HEIGHT * ratio)
                w = max(min_w, control_value)
                return w, w / ratio

            min_h = max(self.MIN_HEIGHT, self.MIN_WIDTH / ratio)
            h = max(min_h, control_value)
            return h * ratio, h

        if control_axis == "w":
            return max(self.MIN_WIDTH, control_value), base_h
        return base_w, max(self.MIN_HEIGHT, control_value)

    def _control_axis_for_snap(self, is_vertical_guide):
        if self.x_dir and self.y_dir:
            return "w" if is_vertical_guide else "h"
        if self.x_dir:
            return "w"
        if self.y_dir:
            return "h"
        return None

    def _solve_snap_size(self, parent, anchor_scene, base_w, base_h, factors, target, coord_axis, control_axis):
        fx, fy = factors
        base_point = self._scene_point_from_factors(parent, anchor_scene, base_w, base_h, fx, fy)
        base_coord = base_point.x() if coord_axis == "x" else base_point.y()
        base_control = base_w if control_axis == "w" else base_h
        epsilon = max(1.0, abs(base_control) * 0.001)

        test_w, test_h = self._size_for_control(control_axis, base_control + epsilon, base_w, base_h)
        test_point = self._scene_point_from_factors(parent, anchor_scene, test_w, test_h, fx, fy)
        test_coord = test_point.x() if coord_axis == "x" else test_point.y()
        coefficient = (test_coord - base_coord) / epsilon
        if abs(coefficient) < 1e-6:
            return None

        snapped_control = base_control + (target - base_coord) / coefficient
        snapped_w, snapped_h = self._size_for_control(control_axis, snapped_control, base_w, base_h)
        snapped_point = self._scene_point_from_factors(parent, anchor_scene, snapped_w, snapped_h, fx, fy)
        snapped_coord = snapped_point.x() if coord_axis == "x" else snapped_point.y()
        final_distance = abs(snapped_coord - target)

        return {
            "axis": control_axis,
            "w": snapped_w,
            "h": snapped_h,
            "final_distance": final_distance,
        }

    def _solve_corner_snap_size(self, parent, anchor_scene, base_w, base_h, width_option, height_option):
        if not (self.x_dir and self.y_dir):
            return None

        factors = width_option["factors"]
        if factors != height_option["factors"]:
            return None

        base_point = self._scene_point_from_factors(parent, anchor_scene, base_w, base_h, *factors)
        epsilon_w = max(1.0, abs(base_w) * 0.001)
        epsilon_h = max(1.0, abs(base_h) * 0.001)

        point_w = self._scene_point_from_factors(
            parent,
            anchor_scene,
            base_w + epsilon_w,
            base_h,
            *factors,
        )
        point_h = self._scene_point_from_factors(
            parent,
            anchor_scene,
            base_w,
            base_h + epsilon_h,
            *factors,
        )

        dx_dw = (point_w.x() - base_point.x()) / epsilon_w
        dx_dh = (point_h.x() - base_point.x()) / epsilon_h
        dy_dw = (point_w.y() - base_point.y()) / epsilon_w
        dy_dh = (point_h.y() - base_point.y()) / epsilon_h
        determinant = dx_dw * dy_dh - dx_dh * dy_dw
        if abs(determinant) < 1e-6:
            return None

        target_x = width_option["target"]
        target_y = height_option["target"]
        rhs_x = target_x - base_point.x()
        rhs_y = target_y - base_point.y()

        delta_w = (rhs_x * dy_dh - dx_dh * rhs_y) / determinant
        delta_h = (dx_dw * rhs_y - rhs_x * dy_dw) / determinant
        snapped_w = max(self.MIN_WIDTH, base_w + delta_w)
        snapped_h = max(self.MIN_HEIGHT, base_h + delta_h)

        snapped_point = self._scene_point_from_factors(
            parent,
            anchor_scene,
            snapped_w,
            snapped_h,
            *factors,
        )
        
        snap_distance = _get_dynamic_snap_distance(parent.scene())
        if abs(snapped_point.x() - target_x) >= snap_distance:
            return None
        if abs(snapped_point.y() - target_y) >= snap_distance:
            return None

        return snapped_w, snapped_h

    def _snap_size_to_guides(self, parent, anchor_scene, w, h):
        scene = parent.scene()
        if not scene:
            return w, h

        snap_distance = _get_dynamic_snap_distance(scene)
        keep_proportion = getattr(parent, 'keep_proportion', True)
        active_points = self._active_point_factors()
        best = None
        best_w = None
        best_h = None

        vertical_targets, horizontal_targets = _snap_targets(scene)
        targets = [(True, target) for target in vertical_targets]
        targets.extend((False, target) for target in horizontal_targets)

        for is_vertical, target in targets:
            coord_axis = "x" if is_vertical else "y"
            control_axis = self._control_axis_for_snap(is_vertical)
            if control_axis is None:
                continue

            for factors in active_points:
                scene_point = self._scene_point_from_factors(parent, anchor_scene, w, h, *factors)
                coord = scene_point.x() if coord_axis == "x" else scene_point.y()
                distance = abs(coord - target)
                if distance >= snap_distance:
                    continue

                solved = self._solve_snap_size(
                    parent,
                    anchor_scene,
                    w,
                    h,
                    factors,
                    target,
                    coord_axis,
                    control_axis,
                )
                if not solved or solved["final_distance"] >= snap_distance:
                    continue

                option = {
                    "distance": distance,
                    "factors": factors,
                    "target": target,
                    "coord_axis": coord_axis,
                    **solved,
                }
                if keep_proportion:
                    if best is None or option["distance"] < best["distance"]:
                        best = option
                elif control_axis == "w":
                    if best_w is None or option["distance"] < best_w["distance"]:
                        best_w = option
                elif best_h is None or option["distance"] < best_h["distance"]:
                    best_h = option

        if keep_proportion:
            if best:
                return best["w"], best["h"]
            return w, h

        if best_w and best_h:
            solved_corner = self._solve_corner_snap_size(parent, anchor_scene, w, h, best_w, best_h)
            if solved_corner:
                return solved_corner

        snapped_w = best_w["w"] if best_w else w
        snapped_h = best_h["h"] if best_h else h
        return snapped_w, snapped_h

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = True
            parent = self.parentItem()
            if parent:
                self._initial_w, self._initial_h = _item_size(parent)
                self.initial_ratio = self._initial_w / self._initial_h if self._initial_h > 0 else 1.0
                anchor_local = self._anchor_local_point(self._initial_w, self._initial_h)
                self._anchor_scene = parent.mapToScene(anchor_local)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_resizing:
            parent = self.parentItem()
            if parent:
                anchor_scene = self._anchor_scene or parent.mapToScene(
                    self._anchor_local_point(self._initial_w, self._initial_h)
                )
                scene_delta = QPointF(
                    event.scenePos().x() - anchor_scene.x(),
                    event.scenePos().y() - anchor_scene.y(),
                )
                local_delta = _unrotated_vector(scene_delta, parent.rotation())
                new_w, new_h = self._resize_from_local_delta(local_delta)
                new_w, new_h = self._snap_size_to_guides(parent, anchor_scene, new_w, new_h)

                if hasattr(parent, 'resize_from_handle'):
                    parent.resize_from_handle(new_w, new_h)
                    new_anchor_local = self._anchor_local_point(new_w, new_h)
                    new_pos = _item_pos_for_local_scene_point(parent, new_anchor_local, anchor_scene)
                    parent._resizing_from_handle = True
                    try:
                        parent.setPos(new_pos)
                    finally:
                        parent._resizing_from_handle = False
                
                if parent.scene():
                    parent.scene().update() 
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_resizing:
            self._is_resizing = False
            self._anchor_scene = None
            # Gatilho do Undo/Redo
            if self.scene() and self.scene().views():
                win = self.scene().views()[0].window()
                if hasattr(win, 'save_snapshot'):
                    win.save_snapshot()
            event.accept()
            return
        super().mouseReleaseEvent(event)


RESIZE_HANDLE_SPECS = (
    ("top_left", -1, -1, Qt.CursorShape.SizeFDiagCursor),
    ("top", 0, -1, Qt.CursorShape.SizeVerCursor),
    ("top_right", 1, -1, Qt.CursorShape.SizeBDiagCursor),
    ("right", 1, 0, Qt.CursorShape.SizeHorCursor),
    ("bottom_right", 1, 1, Qt.CursorShape.SizeFDiagCursor),
    ("bottom", 0, 1, Qt.CursorShape.SizeVerCursor),
    ("bottom_left", -1, 1, Qt.CursorShape.SizeBDiagCursor),
    ("left", -1, 0, Qt.CursorShape.SizeHorCursor),
)


def _item_size(item):
    if hasattr(item, 'rect'):
        rect = item.rect()
    else:
        rect = item.pixmap().rect()
    return float(rect.width()), float(rect.height())


def _handle_position(name, w, h):
    positions = {
        "top_left": QPointF(0, 0),
        "top": QPointF(w / 2, 0),
        "top_right": QPointF(w, 0),
        "right": QPointF(w, h / 2),
        "bottom_right": QPointF(w, h),
        "bottom": QPointF(w / 2, h),
        "bottom_left": QPointF(0, h),
        "left": QPointF(0, h / 2),
    }
    return positions[name]


def _init_resize_handles(item):
    item.resize_handles = {}
    for name, x_dir, y_dir, cursor in RESIZE_HANDLE_SPECS:
        handle = ResizeHandle(item, name, x_dir, y_dir, cursor)
        handle.hide()
        item.resize_handles[name] = handle
    item.handle_br = item.resize_handles["bottom_right"]
    _update_resize_handles(item)


def _update_resize_handles(item):
    if not hasattr(item, 'resize_handles'):
        return
    w, h = _item_size(item)
    for name, handle in item.resize_handles.items():
        handle.setPos(_handle_position(name, w, h))


def _set_resize_handles_visible(item, visible):
    if not hasattr(item, 'resize_handles'):
        return
    for handle in item.resize_handles.values():
        handle.setVisible(visible)


class Guideline(QGraphicsLineItem):
    def __init__(self, position_px, is_vertical=True):
        super().__init__()
        self.is_vertical = is_vertical
        
        if is_vertical:
            self.setLine(0, -10000, 0, 10000)
            self.setPos(position_px, 0)
        else:
            self.setLine(-10000, 0, 10000, 0)
            self.setPos(0, position_px)

        pen = QPen(QColor("#00bcd4"), 1, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        self.setPen(pen)

        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setZValue(10)

    def shape(self):
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(15) 
        return stroker.createStroke(path)
    
    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            if getattr(self, '_keyboard_move', False):
                return value
            new_pos = value
            rect = _document_rect(self.scene())
            snap_dist = _get_dynamic_snap_distance(self.scene())
            
            if self.is_vertical:
                x = new_pos.x()
                candidates = [0, rect.width() / 2, rect.width()]
                for c in candidates:
                    if abs(x - c) < snap_dist:
                        x = c
                        break 
                return QPointF(x, 0)
            else:
                y = new_pos.y()
                candidates = [0, rect.height() / 2, rect.height()]
                for c in candidates:
                    if abs(y - c) < snap_dist:
                        y = c
                        break
                return QPointF(0, y)
            
        # --- Feedback visual: Muda apenas a cor quando selecionada ---
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            is_selected = bool(value)
            color = "#ff9800" if is_selected else "#00bcd4"
            
            pen = QPen(QColor(color), 1, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            self.setPen(pen)
                
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Salva snapshot após mover a guia, igual aos outros itens
        scene = self.scene()
        if scene and scene.views():
            win = scene.views()[0].window()
            if hasattr(win, 'save_snapshot'):
                win.save_snapshot()


class ImageItem(QGraphicsPixmapItem):
    SNAP_DISTANCE = 15

    def __init__(self, pixmap_path=None, parent=None):
        if pixmap_path:
            reader = QImageReader(pixmap_path)
            reader.setAutoTransform(True)
            size = reader.size()        
            img = reader.read()
            pixmap = QPixmap.fromImage(img) if not img.isNull() else QPixmap(pixmap_path)
        else:
            pixmap = QPixmap(1000, 1000)
            pixmap.fill(Qt.GlobalColor.transparent)
            
        super().__init__(pixmap)
        self._original_path = pixmap_path or ""
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._original_pixmap = pixmap
        self.setZValue(1) 
        
        self.keep_proportion = True
        self.has_link = False
        _init_resize_handles(self)
        self.update_center()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            can_resize = self.isSelected() and bool(
                self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            )
            _set_resize_handles_visible(self, can_resize)

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            rect = self.pixmap().rect()
            w, h = rect.width(), rect.height()
            return _snap_position_to_guides(self, new_pos, w, h)
        return super().itemChange(change, value)

    def update_center(self):
        rect = self.pixmap().rect()
        self.setTransformOriginPoint(rect.width() / 2, rect.height() / 2)

    def resize_by_longest_side(self, size_px):
        w = self._original_pixmap.width()
        h = self._original_pixmap.height()
        if w > h:
            new_w = size_px
            new_h = (h * size_px) / w
        else:
            new_h = size_px
            new_w = (w * size_px) / h
            
        scaled = self._original_pixmap.scaled(
            new_w, new_h, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        if hasattr(self, 'handle_br'):
            _update_resize_handles(self)
        self.update_center()

    def resize_custom(self, w, h):
        if w <= 0 or h <= 0: return
        scaled = self._original_pixmap.scaled(
            w, h, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        if hasattr(self, 'handle_br'):
            _update_resize_handles(self)
        self.update_center()

    def resize_from_handle(self, w, h):
        self.resize_custom(w, h)

    def hide_resize_handles(self):
        _set_resize_handles_visible(self, False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_mouse_dragging = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_mouse_dragging = False
        super().mouseReleaseEvent(event)
        # Gatilho do Undo/Redo
        if self.scene() and self.scene().views():
            win = self.scene().views()[0].window()
            if hasattr(win, 'save_snapshot'):
                win.save_snapshot()

class BackgroundItem(ImageItem):
    """
    Herdando de ImageItem, o fundo atua como um PowerClip (Máscara de Corte).
    Ele ganha alças de redimensionamento e vira uma camada livre (Z-Value -100), 
    mas é renderizado estritamente dentro da área da prancheta.
    """
    def __init__(self, pixmap_path=None, parent=None):
        super().__init__(pixmap_path, parent)
        self.setZValue(-100)

    def paint(self, painter, option, widget=None):
        """MÁGICA VISUAL: Corta a pintura da imagem nas bordas exatas do documento."""
        if self.scene():
            path = QPainterPath()
            path.addRect(_document_rect(self.scene()))
            local_path = self.mapFromScene(path) # Traduz as coordenadas do documento para as da imagem
            
            # Aplica a máscara (PowerClip)
            painter.setClipPath(local_path)
            
        super().paint(painter, option, widget)

    def shape(self):
        """MÁGICA DE UX: Impede que o usuário selecione a parte invisível da imagem clicando no nada."""
        base_shape = super().shape()
        if self.scene():
            path = QPainterPath()
            path.addRect(_document_rect(self.scene()))
            local_path = self.mapFromScene(path)
            
            # O formato "clicável" é apenas a interseção entre o tamanho real da imagem e o tamanho do documento
            return base_shape.intersected(local_path)
            
        return base_shape
    
class SignatureItem(QGraphicsPixmapItem):
    SNAP_DISTANCE = 15

    def __init__(self, pixmap_path, parent=None):
        reader = QImageReader(pixmap_path)
        reader.setAutoTransform(True) # Lê metadados EXIF e rotaciona corretamente
        size = reader.size()        
        img = reader.read()
        pixmap = QPixmap.fromImage(img) if not img.isNull() else QPixmap(pixmap_path)
        
        super().__init__(pixmap)
        self._original_path = pixmap_path
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._original_pixmap = pixmap
        self.setZValue(201)
        
        self.keep_proportion = True
        _init_resize_handles(self)
        self.update_center()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            can_resize = self.isSelected() and bool(
                self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            )
            _set_resize_handles_visible(self, can_resize)

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            rect = self.pixmap().rect()
            w, h = rect.width(), rect.height()
            return _snap_position_to_guides(self, new_pos, w, h)
        return super().itemChange(change, value)

    def update_center(self):
        rect = self.pixmap().rect()
        self.setTransformOriginPoint(rect.width() / 2, rect.height() / 2)

    def resize_by_longest_side(self, size_px):
        w = self._original_pixmap.width()
        h = self._original_pixmap.height()
        if w > h:
            new_w = size_px
            new_h = (h * size_px) / w
        else:
            new_h = size_px
            new_w = (w * size_px) / h
            
        scaled = self._original_pixmap.scaled(
            new_w, new_h, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        if hasattr(self, 'handle_br'):
            _update_resize_handles(self)
        self.update_center()

    def resize_custom(self, w, h):
        if w <= 0 or h <= 0: return
        scaled = self._original_pixmap.scaled(
            w, h, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        if hasattr(self, 'handle_br'):
            _update_resize_handles(self)
        self.update_center()

    def resize_from_handle(self, w, h):
        self.resize_custom(w, h)

    def hide_resize_handles(self):
        _set_resize_handles_visible(self, False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_mouse_dragging = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_mouse_dragging = False
        super().mouseReleaseEvent(event)
        # Gatilho do Undo/Redo
        if self.scene() and self.scene().views():
            win = self.scene().views()[0].window()
            if hasattr(win, 'save_snapshot'):
                win.save_snapshot()


class BleedTextItem(QGraphicsTextItem):
    """Subclasse para evitar o corte visual de letras massivas que vazam a caixa lógica (ex: perna do j)."""
    def boundingRect(self):
        rect = super().boundingRect()
        # Expande a área de repintura em 200px para cima e para baixo. 
        # Isso afeta apenas o motor de vídeo da tela, não altera posições ou exportações.
        rect.adjust(0, -200, 0, 200)
        return rect


class DesignerBox(QGraphicsRectItem):
    SNAP_DISTANCE = 15

    def __init__(self, x=0, y=0, w=300, h=60, text="Placeholder"):
        super().__init__(0, 0, w, h)
        self.setPos(x, y)
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        self.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(255, 255, 255, 50)))
        self.setZValue(101)

        self.state = TextState(html_content=text)
        
        self.text_item = BleedTextItem("", self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.black)
        
        # CORREÇÃO CRÍTICA: Zera a margem fantasma nativa do Editor para equiparar ao Gerador
        self.text_item.document().setDocumentMargin(0)
        
        self.text_item.document().contentsChanged.connect(self.recalculate_text_position)

        self.text_item.setTextWidth(w)
        self.text_item.setPos(0, 0)
        
        self.apply_state()
        self.update_center()
        
        # --- Instanciar Alças de Redimensionamento ---
        self.keep_proportion = True
        _init_resize_handles(self)

    def setRect(self, *args):
        super().setRect(*args)
        if hasattr(self, 'handle_br'):
            _update_resize_handles(self)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            can_resize = self.isSelected() and bool(
                self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            )
            _set_resize_handles_visible(self, can_resize)

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            rect = self.rect()
            w, h = rect.width(), rect.height()
            return _snap_position_to_guides(self, new_pos, w, h)
        return super().itemChange(change, value)
    
    def paint(self, painter, option, widget=None):
        if self.isSelected():
            self.setPen(QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine))
            self.setBrush(QBrush(QColor(0, 100, 255, 30)))
        else:
            self.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DotLine))
            self.setBrush(QBrush(QColor(255, 255, 255, 10)))
        super().paint(painter, option, widget)

    
    def resize_from_handle(self, w, h):
        self.setRect(0, 0, w, h)
        self.recalculate_text_position()
        self.update_center()

    def hide_resize_handles(self):
        _set_resize_handles_visible(self, False)
    
    def set_alignment(self, align_str):
        self.state.align = align_str
        self.apply_state()

    def set_vertical_alignment(self, align_str):
        self.state.vertical_align = align_str
        self.apply_state()

    def set_block_format(self, indent=None, line_height=None):
        if indent is not None: self.state.indent_px = indent
        if line_height is not None: self.state.line_height = line_height
        self.apply_state()

    def get_placeholders(self):
        text = self.text_item.toPlainText()
        return re.findall(r"\{([a-zA-Z0-9_]+)\}", text)
    

    def apply_state(self):
        """Reconstrói todo o documento visual com base na Fonte da Verdade."""
        self.text_item.blockSignals(True)
        
        # 1. Limpeza Retroativa e Injeção de Conteúdo (conserta JSONs antigos já infectados)
        html = re.sub(r"font-family\s*:[^;\"]+;?", "", self.state.html_content)
        html = re.sub(r"font-size\s*:[^;\"]+;?", "", html)
        html = re.sub(r"color\s*:[^;\"]+;?", "", html)
        html = re.sub(r"background-color\s*:[^;\"]+;?", "", html)
        html = re.sub(r"text-decoration\s*:[^;\"]+;?", "", html)
        html = re.sub(r"(?i)<a\b[^>]*>", "", html)
        html = re.sub(r"(?i)</a>", "", html)
        html = re.sub(r"(?i)<h[1-6]([^>]*)>", r"<p\1>", html)
        html = re.sub(r"(?i)</h[1-6]>", "</p>", html)
        
        self.text_item.setHtml(html)
        
        # 2. Aplicar Fonte Global e Cor NATIVA (SEMPRE após o setHtml, pois ele reseta o documento)
        font = QFont(self.state.font_family, self.state.font_size)
        font.setStyleStrategy(QFont.StyleStrategy.ForceOutline)
        self.text_item.setFont(font)
        self.text_item.document().setDefaultFont(font)
        
        color = QColor(getattr(self.state, 'font_color', '#000000'))
        
        cursor_color = QTextCursor(self.text_item.document())
        cursor_color.select(QTextCursor.SelectionType.Document)
        char_fmt = QTextCharFormat()
        char_fmt.setForeground(QBrush(color))
        cursor_color.mergeCharFormat(char_fmt)
        
        # 3. Aplicar Alinhamento Horizontal
        opt = self.text_item.document().defaultTextOption()
        if self.state.align == "center": opt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif self.state.align == "right": opt.setAlignment(Qt.AlignmentFlag.AlignRight)
        elif self.state.align == "justify": opt.setAlignment(Qt.AlignmentFlag.AlignJustify)
        else: opt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.text_item.document().setDefaultTextOption(opt)
        
        # 4. Aplicar Margens e Entrelinhas
        cursor = QTextCursor(self.text_item.document())
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextBlockFormat()
        fmt.setTextIndent(self.state.indent_px)
        fmt.setLineHeight(self.state.line_height * 100.0, 1)
        cursor.mergeBlockFormat(fmt)

        # 5. Zerar margens para sistema de ancoragem livre
        root_frame = self.text_item.document().rootFrame()
        frame_fmt = root_frame.frameFormat()
        frame_fmt.setMargin(0)
        root_frame.setFrameFormat(frame_fmt)
        
        self.text_item.blockSignals(False)
        self.recalculate_text_position()

    def recalculate_text_position(self):
        self.text_item.setTextWidth(self.rect().width())
        doc = self.text_item.document()
        layout = doc.documentLayout()
        logical_h = layout.documentSize().height()
        box_h = self.rect().height()
        
        # --- CÁLCULO DA TINTA REAL (Ignorando Ascender/Descender invisível) ---
        font = self.text_item.font()
        fm = QFontMetrics(font)
        real_top = 0
        real_bottom = logical_h
        
        first_block = doc.begin()
        if first_block.isValid():
            text_layout = first_block.layout()
            if text_layout.lineCount() > 0:
                first_line = text_layout.lineAt(0)
                text_str = first_block.text()[first_line.textStart() : first_line.textStart() + first_line.textLength()]
                if text_str.strip():
                    tight_rect = fm.tightBoundingRect("AÇgjpqy|{}")
                    real_top = first_line.y() + first_line.ascent() + tight_rect.top()

        last_block = doc.begin()
        last_valid_block = last_block
        while last_block.isValid():
            if last_block.text().strip(): last_valid_block = last_block
            last_block = last_block.next()
            
        if last_valid_block.isValid():
            text_layout = last_valid_block.layout()
            if text_layout.lineCount() > 0:
                last_line = text_layout.lineAt(text_layout.lineCount() - 1)
                text_str = last_valid_block.text()[last_line.textStart() : last_line.textStart() + last_line.textLength()]
                if text_str.strip():
                    tight_rect = fm.tightBoundingRect("AÇgjpqy|{}")
                    block_y = layout.blockBoundingRect(last_valid_block).y()
                    real_bottom = block_y + last_line.y() + last_line.ascent() + tight_rect.bottom()
                    
        content_h = real_bottom - real_top
        
        y = 0
        if self.state.vertical_align == "center":
            y = (box_h - content_h) / 2 - real_top
        elif self.state.vertical_align == "bottom":
            y = box_h - content_h - real_top
        else: # Top
            y = -real_top
            
        self.text_item.setPos(0, y)

    def update_center(self):
        rect = self.rect()
        self.setTransformOriginPoint(rect.center())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_mouse_dragging = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_mouse_dragging = False
        super().mouseReleaseEvent(event)
        # Gatilho do Undo/Redo
        if self.scene() and self.scene().views():
            win = self.scene().views()[0].window()
            if hasattr(win, 'save_snapshot'):
                win.save_snapshot()
