pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import Comsoc 1.0

Item {
    id: root
    objectName: "canvasWorkspace"
    property real zoomValue: 100
    property bool showGrid: false
    property bool showGuides: true
    property bool editingText: editor.editingText
    focus: true
    Component.onCompleted: editor.attachCanvas()
    onZoomValueChanged: editor.cancelTransform()
    onWidthChanged: editor.cancelTransform()
    onHeightChanged: editor.cancelTransform()
    Keys.onEscapePressed: event => { editor.cancelTransform(); event.accepted = true; }
    Connections {
        target: root.Window.window
        function onActiveChanged() { if (!root.Window.window.active) editor.cancelTransform(); }
    }
    Keys.onDeletePressed: editor.deleteSelected()
    Keys.onReturnPressed: root.beginEditing(editor.uiState.selected)
    Keys.onPressed: event => {
        if (root.editingText || editor.transforming) return;
        const steps = event.modifiers & Qt.ShiftModifier ? 10 : 1;
        const delta = { [Qt.Key_Left]: [-steps, 0], [Qt.Key_Right]: [steps, 0], [Qt.Key_Up]: [0, -steps], [Qt.Key_Down]: [0, steps] }[event.key];
        if (delta && editor.uiState.selected.key) {
            editor.moveSelected(editor.uiState.selected.x + delta[0], editor.uiState.selected.y + delta[1]);
            event.accepted = true;
        }
    }
    signal zoomRequested(real value)

    function finishEditing() { editor.finishTextSession(); }
    function beginEditing(layer) {
        if (layer.type !== "text" || layer.locked) return;
        editor.startTextSession(layer.key);
        Qt.callLater(function() { liveText.forceActiveFocus(); });
    }
    clip: true
    Rectangle { anchors.fill: parent; color: Theme.canvasDeep }
    Canvas {
        objectName: "workspaceGrid"
        anchors.fill: parent
        visible: root.showGrid
        opacity: 0.45
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            ctx.strokeStyle = "#4A4C54";
            ctx.lineWidth = 1;
            for (let x=0.5; x<width; x+=24) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,height); ctx.stroke(); }
            for (let y=0.5; y<height; y+=24) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(width,y); ctx.stroke(); }
        }
    }
    Flickable {
        id: viewport
        objectName: "canvasViewport"
        interactive: !editor.transforming
        anchors.fill: parent
        clip: true
        contentWidth: Math.max(width, page.width + 80)
        contentHeight: Math.max(height, page.height + 80)
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.horizontal: ScrollBar {}
        ScrollBar.vertical: ScrollBar {}

        Item {
            id: page
            clip: true
            readonly property int editingIndex: editor.paintLayers.findIndex(layer => layer.key === editor.uiState.selected.key)
            readonly property real factor: Math.min((viewport.width-80)/editor.uiState.width, (viewport.height-80)/editor.uiState.height) * root.zoomValue/100
            width: editor.uiState.width * factor
            height: editor.uiState.height * factor
            x: (viewport.contentWidth-width)/2
            y: (viewport.contentHeight-height)/2

            Rectangle {
                anchors.fill: parent
                color: "white"
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { root.finishEditing(); editor.select(""); root.forceActiveFocus(); }
            }

            Repeater {
                model: editor.canvasLayers
                delegate: CanvasLayer {
                    required property int index
                    required property QtObject layerData
                    objectName: "paintLayer_" + layerData.uiView.key
                    source: layerData
                    z: index * 2
                    x: (layerData.uiView.x + layerData.bounds.x) * page.factor
                    y: (layerData.uiView.y + layerData.bounds.y) * page.factor
                    width: layerData.bounds.width * page.factor
                    height: layerData.bounds.height * page.factor
                    visible: layerData.uiView.visible && !(root.editingText && editor.uiState.selected.key === layerData.uiView.key)
                }
            }
            Repeater {
                model: editor.canvasLayers
                delegate: Item {
                    id: objectOverlay
                    required property int index
                    required property QtObject layerData
                    readonly property var modelData: layerData.uiView
                    z: index * 2 + 1
                    enabled: !(root.editingText && editor.uiState.selected.key === modelData.key)
                    x: modelData.x * page.factor
                    y: modelData.y * page.factor
                    width: modelData.w * page.factor
                    height: modelData.h * page.factor
                    rotation: modelData.rotation
                    visible: modelData.visible
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.width: editor.uiState.selected.key === objectOverlay.modelData.key ? 1 : 0
                        border.color: Theme.accentHover
                    }
                    MouseArea {
                        id: objectMouse
                        objectName: "moveHandle_" + objectOverlay.modelData.key
                        anchors.fill: parent
                        preventStealing: true
                        cursorShape: objectOverlay.modelData.locked ? Qt.ArrowCursor : Qt.SizeAllCursor
                        property point origin
                        property point current
                        property real gestureFactor: 1
                        onPressed: mouse => {
                            origin = mapToItem(page, mouse.x, mouse.y);
                            current = origin;
                            gestureFactor = page.factor;
                            editor.beginTransform(objectOverlay.modelData.key, false);
                            root.forceActiveFocus();
                        }
                        onPositionChanged: mouse => {
                            if (!pressed || !editor.transforming) return;
                            current = mapToItem(page, mouse.x, mouse.y);
                            editor.updateTransform((current.x-origin.x)/gestureFactor, (current.y-origin.y)/gestureFactor);
                        }
                        onReleased: editor.finishTransform()
                        onCanceled: editor.cancelTransform()
                        onDoubleClicked: root.beginEditing(objectOverlay.modelData)
                    }
                    Rectangle {
                        visible: editor.uiState.selected.key === objectOverlay.modelData.key && !objectOverlay.modelData.locked
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        width: 10
                        height: 10
                        color: Theme.accentHover
                        MouseArea {
                            objectName: "resizeHandle_" + objectOverlay.modelData.key
                            anchors.fill: parent
                            preventStealing: true
                            cursorShape: Qt.SizeFDiagCursor
                            property point origin
                            property point current
                            property real gestureFactor: 1
                            onPressed: mouse => {
                                origin = mapToItem(page, mouse.x, mouse.y);
                                current = origin;
                                gestureFactor = page.factor;
                                editor.beginTransform(objectOverlay.modelData.key, true);
                                root.forceActiveFocus();
                            }
                            onPositionChanged: mouse => {
                                if (!pressed || !editor.transforming) return;
                                current = mapToItem(page, mouse.x, mouse.y);
                                editor.updateTransform((current.x-origin.x)/gestureFactor, (current.y-origin.y)/gestureFactor);
                            }
                            onReleased: editor.finishTransform()
                            onCanceled: editor.cancelTransform()
                        }
                    }
                }
            }

            Repeater {
                model: editor.uiState.guides
                delegate: Rectangle {
                    id: guide
                    z: 1000000
                    required property int index
                    required property var modelData
                    readonly property real displayPosition: editor.guideGesture.index === index ? editor.guideGesture.position : modelData.pos
                    objectName: "canvasGuide_" + index
                    visible: root.showGuides && modelData.visible !== false
                    x: modelData.vertical ? displayPosition * page.factor : 0
                    y: modelData.vertical ? 0 : displayPosition * page.factor
                    width: modelData.vertical ? 1 : page.width
                    height: modelData.vertical ? page.height : 1
                    color: Theme.guide
                    Menu {
                        id: guideMenu
                        MenuItem { text: "Editar posição…"; onTriggered: editor.editGuide(guide.index) }
                        MenuItem { text: "Excluir guia"; onTriggered: editor.deleteGuide(guide.index) }
                    }
                    MouseArea {
                        objectName: "guideHandle_" + guide.index
                        anchors.fill: parent
                        anchors.margins: -4
                        enabled: !editor.uiState.guidesLocked
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        preventStealing: true
                        cursorShape: guide.modelData.vertical ? Qt.SplitHCursor : Qt.SplitVCursor
                        property real gestureFactor: 1
                        onPressed: mouse => {
                            gestureFactor = page.factor;
                            if (mouse.button === Qt.LeftButton) {
                                editor.beginGuideTransform(guide.index);
                                root.forceActiveFocus();
                            }
                        }
                        onPositionChanged: mouse => {
                            if (!(pressedButtons & Qt.LeftButton)) return;
                            const p = mapToItem(page, mouse.x, mouse.y);
                            const position = (guide.modelData.vertical ? p.x : p.y)/gestureFactor;
                            editor.updateGuideTransform(position);
                        }
                        onReleased: mouse => {
                            if (mouse.button === Qt.LeftButton) editor.finishGuideTransform();
                            else guideMenu.popup();
                        }
                        onCanceled: editor.cancelTransform()
                    }
                }
            }

            Item {
                id: textBox
                z: page.editingIndex * 2 + 0.5
                visible: root.editingText
                x: (editor.uiState.selected.x || 0) * page.factor
                y: (editor.uiState.selected.y || 0) * page.factor
                width: (editor.uiState.selected.w || 300) * page.factor
                height: (editor.uiState.selected.h || 100) * page.factor
                rotation: editor.uiState.selected.rotation || 0
                opacity: editor.uiState.selected.opacity === undefined ? 1 : editor.uiState.selected.opacity
                CanvasTextEditor {
                    id: liveText
                    objectName: "canvasTextEditor"
                    Component.onCompleted: editor.attachTextEditor(liveText)
                    width: (editor.uiState.selected.w || 300) - 2 * contentLeft
                    x: contentLeft * page.factor
                    height: paintHeight
                    y: contentTop * page.factor
                    scale: page.factor
                    transformOrigin: Item.TopLeft
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.RightButton
                        onClicked: textMenu.popup()
                    }
                    Menu {
                        id: textMenu
                        MenuItem { text: "Recortar"; onTriggered: liveText.command("cut") }
                        MenuItem { text: "Copiar"; onTriggered: liveText.command("copy") }
                        MenuItem { text: "Colar"; onTriggered: liveText.command("paste") }
                        MenuSeparator {}
                        MenuItem { text: "Inserir variável…  Ctrl+1"; onTriggered: liveText.promptVariable() }
                        MenuItem { text: "Trecho opcional  Ctrl+2"; enabled: liveText.formatState.hasSelection; onTriggered: liveText.wrapOptional() }
                        MenuSeparator {}
                        MenuItem { text: "Concluir edição  Ctrl+Enter"; onTriggered: editor.finishTextSession() }
                    }
                }
            }
        }
    }
    MouseArea {
        objectName: "canvasPanArea"
        anchors.fill: parent
        acceptedButtons: Qt.MiddleButton
        preventStealing: true
        property point origin
        property real startX
        property real startY
        onPressed: mouse => {
            editor.cancelTransform();
            origin = Qt.point(mouse.x, mouse.y);
            startX = viewport.contentX;
            startY = viewport.contentY;
        }
        onPositionChanged: mouse => {
            if (!pressed) return;
            viewport.contentX = Math.max(0, Math.min(viewport.contentWidth-viewport.width, startX-(mouse.x-origin.x)));
            viewport.contentY = Math.max(0, Math.min(viewport.contentHeight-viewport.height, startY-(mouse.y-origin.y)));
        }
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 8
        text: root.editingText ? "Ctrl+Enter para concluir a edição" : "Duplo clique para editar texto"
        color: Theme.textSubtle
        font.pixelSize: 10
    }
}
