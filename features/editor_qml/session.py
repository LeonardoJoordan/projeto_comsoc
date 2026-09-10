"""Janela QML reutilizável pelo launcher e pelo workspace Widgets."""
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlTypeId
from PySide6.QtQuickControls2 import QQuickStyle
from features.editor_qml.bridge import EditorBridge, PreviewProvider
from features.editor_qml.canvas_text_editor import CanvasTextEditor
from features.editor_qml.canvas_layers import CanvasLayer


class EditorSession(QObject):
    closed = Signal()
    modelSaved = Signal(str, list, str)

    def __init__(self, path=None, parent=None):
        super().__init__(parent)
        self._closed = False
        if qmlTypeId("Comsoc", 1, 0, "CanvasLayer") < 0:
            qmlRegisterType(CanvasLayer, "Comsoc", 1, 0, "CanvasLayer")
        if qmlTypeId("Comsoc", 1, 0, "CanvasTextEditor") < 0:
            QQuickStyle.setStyle("Basic")
            qmlRegisterType(CanvasTextEditor, "Comsoc", 1, 0, "CanvasTextEditor")
        self.engine = QQmlApplicationEngine(self)
        self.bridge = EditorBridge(PreviewProvider())
        self.bridge.setParent(self)
        self.bridge.modelSaved.connect(self.modelSaved)
        self.engine.addImageProvider("model", self.bridge.provider)
        self.engine.rootContext().setContextProperty("editor", self.bridge)
        if path and not self.bridge.load(str(path)):
            self.bridge.shutdown()
            self.deleteLater()
            raise ValueError(self.bridge.state["message"])
        self.engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name("Main.qml"))))
        if not self.engine.rootObjects():
            self.bridge.shutdown()
            self.deleteLater()
            raise RuntimeError("Não foi possível abrir a interface do editor QML.")
        self.window = self.engine.rootObjects()[0]
        self.window.visibleChanged.connect(self._visibility_changed)
        # A cena já foi preparada por attachCanvas; miniaturas são geradas ao salvar.

    def _visibility_changed(self):
        if not self.window.isVisible() and not self._closed:
            self._closed = True
            self.bridge.shutdown()
            self.closed.emit()
            self.deleteLater()

    def close(self):
        return self.window.close()
