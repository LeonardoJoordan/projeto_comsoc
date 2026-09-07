pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls

Item {
    id: root
    property real zoomValue: 100
    property bool showGrid: false
    property bool showGuides: true
    property bool editingText: false
    property string editingKey: ""
    focus: true
    Keys.onDeletePressed: editor.deleteSelected()
    Keys.onReturnPressed: root.beginEditing(editor.state.selected)
    signal zoomRequested(real value)

    function finishEditing() {
        if (!editingText) return;
        const key = editingKey;
        const content = textEditor.text;
        editingText = false;
        editor.select(key);
        editor.setValue("html", content);
    }
    function beginEditing(layer) {
        if (layer.type !== "text" || layer.locked) return;
        editor.select(layer.key);
        editingKey = layer.key;
        textEditor.text = layer.html;
        editingText = true;
        textEditor.forceActiveFocus();
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
        anchors.fill: parent
        clip: true
        contentWidth: Math.max(width, page.width + 80)
        contentHeight: Math.max(height, page.height + 80)
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.horizontal: ScrollBar {}
        ScrollBar.vertical: ScrollBar {}

        Item {
            id: page
            readonly property real factor: Math.min((viewport.width-80)/editor.state.width, (viewport.height-80)/editor.state.height) * root.zoomValue/100
            width: editor.state.width * factor
            height: editor.state.height * factor
            x: (viewport.contentWidth-width)/2
            y: (viewport.contentHeight-height)/2

            Image {
                anchors.fill: parent
                source: editor.previewUrl
                cache: false
                asynchronous: false
                smooth: true
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { root.finishEditing(); editor.select(""); }
            }

            Repeater {
                model: editor.state.paintLayers
                delegate: Item {
                    id: objectOverlay
                    required property var modelData
                    x: modelData.x * page.factor
                    y: modelData.y * page.factor
                    width: modelData.w * page.factor
                    height: modelData.h * page.factor
                    rotation: modelData.rotation
                    visible: modelData.visible
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.width: editor.state.selected.key === objectOverlay.modelData.key ? 1 : 0
                        border.color: Theme.accentHover
                    }
                    MouseArea {
                        id: objectMouse
                        anchors.fill: parent
                        preventStealing: true
                        cursorShape: objectOverlay.modelData.locked ? Qt.ArrowCursor : Qt.SizeAllCursor
                        property point origin
                        property point current
                        onPressed: mouse => {
                            origin = mapToItem(page, mouse.x, mouse.y);
                            current = origin;
                        }
                        onPositionChanged: mouse => { if (pressed) current = mapToItem(page, mouse.x, mouse.y); }
                        onReleased: {
                            root.forceActiveFocus();
                            const layer = objectOverlay.modelData;
                            const dx = (current.x-origin.x)/page.factor;
                            const dy = (current.y-origin.y)/page.factor;
                            if (!layer.locked && Math.abs(dx)+Math.abs(dy)>2)
                                editor.moveItem(layer.key, layer.x+dx, layer.y+dy);
                            else editor.select(layer.key);
                        }
                        onDoubleClicked: root.beginEditing(objectOverlay.modelData)
                    }
                    Rectangle {
                        visible: editor.state.selected.key === objectOverlay.modelData.key && !objectOverlay.modelData.locked
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        width: 10
                        height: 10
                        color: Theme.accentHover
                        MouseArea {
                            anchors.fill: parent
                            preventStealing: true
                            cursorShape: Qt.SizeFDiagCursor
                            property point origin
                            property point current
                            onPressed: mouse => { origin = mapToItem(objectOverlay, mouse.x, mouse.y); current = origin; }
                            onPositionChanged: mouse => { if (pressed) current = mapToItem(objectOverlay, mouse.x, mouse.y); }
                            onReleased: {
                                const data = objectOverlay.modelData;
                                editor.resizeItem(data.key, Math.max(1, data.w + (current.x-origin.x)/page.factor), Math.max(1, data.h + (current.y-origin.y)/page.factor));
                            }
                        }
                    }
                }
            }

            Repeater {
                model: editor.state.guides
                delegate: Rectangle {
                    id: guide
                    required property int index
                    required property var modelData
                    visible: root.showGuides && modelData.visible !== false
                    x: modelData.vertical ? modelData.pos * page.factor : 0
                    y: modelData.vertical ? 0 : modelData.pos * page.factor
                    width: modelData.vertical ? 1 : page.width
                    height: modelData.vertical ? page.height : 1
                    color: Theme.guide
                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -4
                        enabled: !editor.state.guidesLocked
                        preventStealing: true
                        cursorShape: guide.modelData.vertical ? Qt.SplitHCursor : Qt.SplitVCursor
                        property real position
                        onPressed: position = guide.modelData.pos
                        onPositionChanged: mouse => {
                            if (!pressed) return;
                            const p = mapToItem(page, mouse.x, mouse.y);
                            position = (guide.modelData.vertical ? p.x : p.y)/page.factor;
                        }
                        onReleased: editor.moveGuide(guide.index, position)
                    }
                }
            }

            Rectangle {
                id: textBox
                visible: root.editingText
                x: (editor.state.selected.x || 0) * page.factor
                y: (editor.state.selected.y || 0) * page.factor
                width: (editor.state.selected.w || 300) * page.factor
                height: Math.max(100, (editor.state.selected.h || 100) * page.factor)
                color: "#FFFFFF"
                border.color: Theme.accent
                TextEdit {
                    id: textEditor
                    objectName: "canvasTextEditor"
                    anchors.fill: parent
                    anchors.margins: 6
                    clip: true
                    textFormat: TextEdit.RichText
                    color: editor.state.selected.font_color || Theme.text
                    font.family: editor.state.selected.font_family || "Arial"
                    font.pointSize: Math.max(8, (editor.state.selected.font_size || 16) * page.factor)
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
                    onActiveFocusChanged: { if (!activeFocus && root.editingText) root.finishEditing(); }
                    Keys.onEscapePressed: root.finishEditing()
                    Keys.onPressed: event => {
                        if (event.key === Qt.Key_Return && (event.modifiers & Qt.ControlModifier)) {
                            root.finishEditing();
                            event.accepted = true;
                        }
                    }
                }
            }
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
