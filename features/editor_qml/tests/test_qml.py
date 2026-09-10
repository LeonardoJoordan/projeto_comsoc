from copy import deepcopy
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QObject, QPointF, Qt, QUrl, QCoreApplication, QEvent, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from PySide6.QtGui import QMouseEvent, QKeyEvent

from features.editor_qml.bridge import EditorBridge, PreviewProvider
from features.editor_qml.canvas_text_editor import CanvasTextEditor
from features.editor_qml.canvas_layers import CanvasLayer

qmlRegisterType(CanvasTextEditor, "Comsoc", 1, 0, "CanvasTextEditor")
qmlRegisterType(CanvasLayer, "Comsoc", 1, 0, "CanvasLayer")

APP = QApplication.instance() or QApplication([])
QQuickStyle.setStyle("Basic")
QML_ROOT = Path(__file__).resolve().parents[1]


def wait_frames(milliseconds):
    # exec libera o GIL para os callbacks Python da QSGRenderThread.
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def visual_items(item):
    yield item
    for child in item.childItems():
        yield from visual_items(child)


def variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


class QmlIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.provider = PreviewProvider()
        self.bridge = EditorBridge(self.provider)
        self.bridge.addItem("text")
        self.bridge.setValue("custom_name", "Primeiro")
        self.bridge.setValue("html", "<p>{Nome}</p>")
        self.bridge.setValue("font_color", "#123456")
        self.bridge.addItem("text")
        self.bridge.moveSelected(400, 250)
        self.bridge.setValue("custom_name", "Segundo")
        self.bridge.setValue("html", "<p>{Cargo}</p>")
        self.bridge.select("")
        self.bridge.render()
        self.engine = QQmlApplicationEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda errors: self.warnings.extend(e.toString() for e in errors))
        self.engine.addImageProvider("model", self.provider)
        self.engine.rootContext().setContextProperty("editor", self.bridge)
        self.engine.load(QUrl.fromLocalFile(str(QML_ROOT / "Main.qml")))
        self.assertTrue(self.engine.rootObjects(), self.warnings)
        self.window = self.engine.rootObjects()[0]
        wait_frames(80)

    def tearDown(self):
        self.bridge._saved = deepcopy(self.bridge._data)
        self.window.close()
        self.bridge.shutdown()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def items(self, parent=None):
        return list(visual_items(parent or self.window.contentItem()))

    def click(self, item, x=None, y=None):
        point = item.mapToScene(QPointF(item.width()/2 if x is None else x, item.height()/2 if y is None else y)).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, point)
        wait_frames(60)

    def post_mouse(self, event_type, point, button, buttons):
        global_point = QPointF(self.window.mapToGlobal(point.toPoint()))
        QCoreApplication.postEvent(self.window, QMouseEvent(event_type, point, global_point,
                                                          button, buttons, Qt.NoModifier))
        wait_frames(35)

    def post_key(self, key, modifiers=Qt.NoModifier):
        QCoreApplication.postEvent(self.window, QKeyEvent(QEvent.KeyPress, key, modifiers))
        QCoreApplication.postEvent(self.window, QKeyEvent(QEvent.KeyRelease, key, modifiers))
        wait_frames(40)

    def test_live_guide_drag_and_zoom_cancellation(self):
        self.window.requestActivate()
        wait_frames(150)
        self.bridge.addGuide(True)
        wait_frames(40)
        guide = next(o for o in self.items() if o.objectName() == 'canvasGuide_0')
        origin = guide.mapToScene(QPointF(0, 20))
        x = guide.x()
        before = deepcopy(self.bridge._data)
        records = self.bridge.canvasLayers.cache.recordings
        self.post_mouse(QEvent.MouseButtonPress, origin, Qt.LeftButton, Qt.LeftButton)
        self.post_mouse(QEvent.MouseMove, origin+QPointF(35, 0), Qt.NoButton, Qt.LeftButton)
        self.assertAlmostEqual(guide.x()-x, 35, delta=.1)
        self.assertEqual(self.bridge._data, before)
        self.post_mouse(QEvent.MouseButtonRelease, origin+QPointF(35, 0), Qt.LeftButton, Qt.NoButton)
        self.assertNotEqual(self.bridge._data, before)
        self.assertEqual(self.bridge.canvasLayers.cache.recordings, records)
        self.bridge.undo()
        wait_frames(40)
        guide = next(o for o in self.items() if o.objectName() == 'canvasGuide_0')
        origin = guide.mapToScene(QPointF(0, 20))
        self.post_mouse(QEvent.MouseButtonPress, origin, Qt.LeftButton, Qt.LeftButton)
        self.post_mouse(QEvent.MouseMove, origin+QPointF(25, 0), Qt.NoButton, Qt.LeftButton)
        self.window.findChild(QObject, 'canvasWorkspace').setProperty('zoomValue', 120)
        self.assertFalse(self.bridge.transforming)
        self.post_mouse(QEvent.MouseButtonRelease, origin+QPointF(25, 0), Qt.LeftButton, Qt.NoButton)
        self.assertEqual(self.bridge._data, before)
        self.assertFalse(self.warnings, self.warnings)

    def test_canvas_arrows_and_input_shortcuts_do_not_conflict(self):
        self.window.requestActivate()
        wait_frames(100)
        key = self.bridge._data['boxes'][0]['object_id']
        self.bridge.select(key)
        canvas = self.window.findChild(QObject, 'canvasWorkspace')
        canvas.forceActiveFocus()
        start = self.bridge.state['selected']['x']
        self.post_key(Qt.Key_Right)
        self.post_key(Qt.Key_Right, Qt.ShiftModifier)
        self.assertEqual(self.bridge.state['selected']['x'], start+11)
        field = next(o for o in self.items() if o.property('label') == 'X' and o.property('fieldWidth') is not None)
        input_item = next(o for o in self.items(field) if o.property('selectByMouse') is True)
        input_item.forceActiveFocus()
        wait_frames(40)
        self.assertTrue(self.window.property('inputHasFocus'))
        before = deepcopy(self.bridge._data)
        self.post_key(Qt.Key_Left)
        self.post_key(Qt.Key_D, Qt.ControlModifier)
        self.post_key(Qt.Key_Z, Qt.ControlModifier)
        self.assertEqual(self.bridge._data, before)
        self.assertFalse(self.warnings, self.warnings)

    def test_middle_button_pans_without_changing_document(self):
        self.window.requestActivate()
        wait_frames(100)
        canvas = self.window.findChild(QObject, 'canvasWorkspace')
        canvas.setProperty('zoomValue', 200)
        wait_frames(40)
        viewport = self.window.findChild(QObject, 'canvasViewport')
        x, y = viewport.property('contentX'), viewport.property('contentY')
        before = deepcopy(self.bridge._data)
        origin = canvas.mapToScene(QPointF(canvas.width()/2, canvas.height()/2))
        self.post_mouse(QEvent.MouseButtonPress, origin, Qt.MiddleButton, Qt.MiddleButton)
        self.post_mouse(QEvent.MouseMove, origin-QPointF(60, 40), Qt.NoButton, Qt.MiddleButton)
        self.post_mouse(QEvent.MouseButtonRelease, origin-QPointF(60, 40), Qt.MiddleButton, Qt.NoButton)
        self.assertGreater(viewport.property('contentX'), x)
        self.assertGreater(viewport.property('contentY'), y)
        self.assertEqual(self.bridge._data, before)
        self.assertFalse(self.warnings, self.warnings)

    def test_live_drag_at_zoom_commits_once_and_escape_restores(self):
        self.window.requestActivate()
        wait_frames(150)
        key = self.bridge._data['boxes'][0]['object_id']
        canvas = self.window.findChild(QObject, 'canvasWorkspace')
        canvas.setProperty('zoomValue', 140)
        wait_frames(35)
        handle = next(o for o in self.items() if o.objectName() == 'moveHandle_'+key)
        visual = next(o for o in self.items() if o.objectName() == 'paintLayer_'+key)
        original = deepcopy(self.bridge._data)
        x, y = visual.x(), visual.y()
        origin = handle.mapToScene(QPointF(15, 15))
        index, records = self.bridge.history._current_index, self.bridge.canvasLayers.cache.recordings
        self.post_mouse(QEvent.MouseButtonPress, origin, Qt.LeftButton, Qt.LeftButton)
        self.assertTrue(self.bridge.transforming)
        target = origin + QPointF(40, 30)
        self.post_mouse(QEvent.MouseMove, target, Qt.NoButton, Qt.LeftButton)
        self.assertTrue(self.bridge.transforming, 'Gesto cancelado antes da confirmação')
        self.assertAlmostEqual(visual.x()-x, 40, delta=.1)
        self.assertAlmostEqual(visual.y()-y, 30, delta=.1)
        self.assertEqual(self.bridge._data, original)
        self.assertEqual(self.bridge.canvasLayers.cache.recordings, records)
        self.post_mouse(QEvent.MouseButtonRelease, target, Qt.LeftButton, Qt.NoButton)
        self.assertFalse(self.bridge.transforming)
        self.assertEqual(self.bridge.history._current_index, index+1)
        self.bridge.undo()
        wait_frames(35)
        self.assertEqual(self.bridge._data, original)
        origin = handle.mapToScene(QPointF(15, 15))
        self.post_mouse(QEvent.MouseButtonPress, origin, Qt.LeftButton, Qt.LeftButton)
        self.post_mouse(QEvent.MouseMove, origin+QPointF(20, 10), Qt.NoButton, Qt.LeftButton)
        QCoreApplication.postEvent(self.window, QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
        wait_frames(35)
        self.assertFalse(self.bridge.transforming)
        self.post_mouse(QEvent.MouseButtonRelease, origin+QPointF(20, 10), Qt.LeftButton, Qt.NoButton)
        self.assertEqual(self.bridge._data, original)
        self.assertTrue(self.bridge.history.can_redo())
        self.assertFalse(self.warnings, self.warnings)

    def test_live_resize_reflows_text_before_release(self):
        key = self.bridge._data['boxes'][0]['object_id']
        self.bridge.select(key)
        self.bridge.setValue('keep_proportion', False)
        self.bridge.setValue('html', '<p>Texto para conferir a quebra de linha durante o redimensionamento.</p>')
        wait_frames(35)
        handle = next(o for o in self.items() if o.objectName() == 'resizeHandle_'+key)
        layer = self.bridge.canvasLayers.objects[key]
        original = deepcopy(self.bridge._data)
        before = dict(layer.view)
        picture = layer.picture
        origin = handle.mapToScene(QPointF(5, 5))
        self.post_mouse(QEvent.MouseButtonPress, origin, Qt.LeftButton, Qt.LeftButton)
        self.assertTrue(self.bridge.transforming)
        target = origin + QPointF(-30, 20)
        self.post_mouse(QEvent.MouseMove, target, Qt.NoButton, Qt.LeftButton)
        self.assertLess(layer.view['w'], before['w'])
        self.assertGreater(layer.view['h'], before['h'])
        self.assertIsNot(layer.picture, picture)
        self.assertEqual(self.bridge._data, original)
        final_width = layer.view['w']
        self.post_mouse(QEvent.MouseButtonRelease, target, Qt.LeftButton, Qt.NoButton)
        self.assertEqual(self.bridge.state['selected']['w'], final_width)
        self.bridge.undo()
        self.assertEqual(self.bridge._data, original)
        self.assertFalse(self.warnings, self.warnings)

    def select_first(self):
        row = next(o for o in self.items() if o.property("visibleLayer") is not None and o.property("title") == "Primeiro")
        self.click(row)
        self.assertEqual(self.bridge.state["selected"]["key"], self.bridge._data["boxes"][0]["object_id"])

    def test_canvas_keeps_visual_identity_and_text_layer_order(self):
        first, second = [box['object_id'] for box in self.bridge._data['boxes']]
        def find(key):
            return next(o for o in self.items() if o.objectName() == 'paintLayer_' + key)
        original = find(first)
        original_row = next(o for o in self.items() if o.property('visibleLayer') is not None and o.property('title') == 'Primeiro')
        self.bridge.moveItem(first, 100, 120)
        wait_frames(30)
        self.assertIs(find(first), original)
        self.assertIs(next(o for o in self.items() if o.property('visibleLayer') is not None and o.property('title') == 'Primeiro'), original_row)
        self.bridge.startTextSession(first)
        wait_frames(30)
        self.assertFalse(original.isVisible())
        live = next(o for o in self.items() if o.objectName() == 'canvasTextEditor')
        self.assertLess(live.parentItem().z(), find(second).z())
        self.bridge.finishTextSession()
        self.bridge.moveLayer(first, second)
        wait_frames(30)
        self.assertIs(find(first), original)
        self.assertTrue(original.isVisible())
        self.assertEqual(original.z(), self.bridge._data['layer_order'].index(first)*2)

    def test_layer_selection_geometry_color_and_undo(self):
        self.select_first()
        field = next(o for o in self.items() if o.property("label") == "X" and o.property("fieldWidth") is not None)
        input_item = next(o for o in self.items(field) if o.property("selectByMouse") is True)
        self.click(input_item)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for ch in "125": QTest.keyClick(self.window, ch)
        QTest.keyClick(self.window, Qt.Key_Return)
        wait_frames(60)
        self.assertEqual(self.bridge.state["selected"]["x"], 125)
        section = self.window.findChild(QObject, "textSection")
        self.click(section, 40, 20)
        self.assertTrue(section.property("expanded"))
        color_field = next(o for o in self.items(section) if o.property("label") == "Cor do texto")
        self.assertEqual(color_field.property("value"), "#123456")
        hex_input = next(o for o in self.items(color_field) if o.property("maximumLength") == 7)
        self.click(hex_input)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for ch in "#ABCDEF": QTest.keyClick(self.window, ch)
        QTest.keyClick(self.window, Qt.Key_Return)
        wait_frames(60)
        self.assertEqual(self.bridge.state["selected"]["font_color"], "#ABCDEF")
        self.bridge.select(self.bridge._data["boxes"][1]["object_id"])
        wait_frames(60)
        self.assertEqual(color_field.property("value"), "#000000")
        self.bridge.undo()
        self.assertEqual(self.bridge._data["boxes"][0]["font_color"], "#123456")
        self.assertFalse(self.warnings, self.warnings)

    def test_canvas_double_click_edits_real_html(self):
        canvas = self.window.findChild(QObject, "canvasWorkspace")
        overlay = next(o for o in self.items(canvas) if isinstance(variant(o.property("modelData")), dict) and variant(o.property("modelData")).get("key") == self.bridge._data["boxes"][0]["object_id"])
        point = overlay.mapToScene(QPointF(overlay.width()/2, overlay.height()/2)).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, point)
        QTest.mouseDClick(self.window, Qt.LeftButton, Qt.NoModifier, point)
        wait_frames(100)
        self.assertTrue(canvas.property("editingText"), self.warnings)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for ch in "{Aluno}": QTest.keyClick(self.window, ch)
        QTest.keyClick(self.window, Qt.Key_Return, Qt.ControlModifier)
        wait_frames(80)
        self.assertFalse(canvas.property("editingText"))
        self.assertIn("{Aluno}", self.bridge._data["boxes"][0]["html"])
        self.assertIn("Aluno", self.bridge.state["fields"])
        self.assertFalse(self.warnings, self.warnings)

    def test_add_button_and_field_drag_are_connected(self):
        button = next(o for o in self.items() if o.property("hoverEnabled") is True and isinstance(variant(o.property("modelData")), dict) and variant(o.property("modelData")).get("title") == "Texto")
        self.click(button)
        self.assertEqual(len(self.bridge.state["layers"]), 3)
        section = self.window.findChild(QObject, "tableFieldsSection")
        self.click(section, 40, 20)
        rows = sorted([o for o in self.items(section) if o.property("label") in ("Nome", "Cargo") and o.property("index") is not None], key=lambda o: o.property("index"))
        start = rows[0].mapToScene(QPointF(60,20)).toPoint()
        end = rows[1].mapToScene(QPointF(60,20)).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, Qt.NoModifier, start)
        for step in range(1,9): QTest.mouseMove(self.window, start+(end-start)*step/8, 15)
        QTest.mouseRelease(self.window, Qt.LeftButton, Qt.NoModifier, end)
        wait_frames(60)
        self.assertEqual(self.bridge.state["fields"], ["Cargo", "Nome"])
        self.assertFalse(self.warnings, self.warnings)

    def test_inspector_preserves_text_selection_and_keyboard_undo(self):
        self.select_first()
        self.bridge.setValue("html", "<p>Alpha Beta</p>")
        self.bridge.startTextSession(self.bridge._selected)
        live = self.window.findChild(QObject, "canvasTextEditor")
        live.selectRange(0, 5)
        section = self.window.findChild(QObject, "textSection")
        self.click(section, 40, 20)
        bold = next(o for o in self.items(section) if o.property("modelData") == "Negrito")
        self.click(bold)
        self.assertTrue(self.bridge.editingText)
        self.assertTrue(self.bridge.textFormat["hasSelection"])
        self.assertTrue(self.bridge.textFormat["bold"])
        live.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_I, Qt.ControlModifier)
        self.assertTrue(self.bridge.textFormat["italic"])
        QTest.keyClick(self.window, Qt.Key_Z, Qt.ControlModifier)
        self.assertFalse(self.bridge.textFormat["italic"])
        self.assertTrue(self.bridge.textFormat["bold"])
        QTest.keyClick(self.window, Qt.Key_Return, Qt.ControlModifier)
        self.assertFalse(self.bridge.editingText)
        self.assertFalse(self.warnings, self.warnings)

    def test_layer_drag_changes_real_order(self):
        rows = {o.property("title"): o for o in self.items() if o.property("visibleLayer") is not None}
        start = rows["Segundo"].mapToScene(QPointF(70, 20)).toPoint()
        end = rows["Primeiro"].mapToScene(QPointF(70, 20)).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, Qt.NoModifier, start)
        for step in range(1, 9): QTest.mouseMove(self.window, start+(end-start)*step/8, 15)
        QTest.mouseRelease(self.window, Qt.LeftButton, Qt.NoModifier, end)
        wait_frames(60)
        self.assertEqual([layer["title"] for layer in self.bridge.layers], ["Primeiro", "Segundo"])
        self.assertFalse(self.warnings, self.warnings)

    def test_shapes_and_outline_controls_change_document(self):
        button = next(o for o in self.items() if o.property("hoverEnabled") is True and isinstance(variant(o.property("modelData")), dict) and variant(o.property("modelData")).get("title") == "Formas")
        self.assertTrue(button.isEnabled())
        self.click(button)
        self.assertEqual(self.bridge.state["selected"]["type"], "shape")
        section = self.window.findChild(QObject, "propertiesSection")
        self.click(section, 40, 20)
        toggle = self.window.findChild(QObject, "outlineSwitch")
        self.click(toggle)
        self.assertTrue(self.bridge.state["selected"]["outline_enabled"])
        color = next(o for o in self.items(section) if o.property("label") == "Preenchimento")
        field = next(o for o in self.items(color) if o.property("maximumLength") == 7)
        self.click(field)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for ch in "#123456": QTest.keyClick(self.window, ch)
        QTest.keyClick(self.window, Qt.Key_Return)
        wait_frames(80)
        self.assertEqual(self.bridge.state["selected"]["fill_color"], "#123456")
        selector = self.window.findChild(QObject, "shapeSelector")
        self.click(selector)
        QTest.keyClick(self.window, Qt.Key_Down)
        QTest.keyClick(self.window, Qt.Key_Return)
        wait_frames(60)
        self.assertEqual(self.bridge.state["selected"]["shape_type"], "square")
        self.assertEqual(self.bridge.state["selected"]["w"], self.bridge.state["selected"]["h"])
        self.assertFalse(self.warnings, self.warnings)


if __name__ == "__main__":
    unittest.main()
