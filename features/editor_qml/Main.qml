pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window

    property real zoomValue: 100
    property bool showGrid: false
    property bool showGuides: editor.state.guidesVisible
    property bool guidesLocked: editor.state.guidesLocked
    property string selectionKind: editor.state.selected.type || ""
    property string selectionIndex: editor.state.selected.key || ""
    property string selectionName: editor.state.selected.title || "Nenhuma seleção"
    property string selectionContent: editor.state.selected.html || ""

    width: 1500
    height: 930
    minimumWidth: 1120
    minimumHeight: 700
    visible: true
    color: Theme.window
    title: "COMSOC Studio — " + editor.state.name
    onClosing: close => close.accepted = editor.canClose()
    Shortcut { sequence: "Ctrl+S"; onActivated: { canvasWorkspace.finishEditing(); editor.save(); } }
    Shortcut { sequence: "Ctrl+Shift+S"; onActivated: editor.saveAs() }
    Shortcut { sequence: "Ctrl+O"; onActivated: editor.openDialog() }
    Shortcut { sequence: "Ctrl+N"; onActivated: editor.newDocument() }
    Shortcut { sequence: "Ctrl+Z"; enabled: !canvasWorkspace.editingText; onActivated: editor.undo() }
    Shortcut { sequence: "Ctrl+Shift+Z"; enabled: !canvasWorkspace.editingText; onActivated: editor.redo() }
    Connections { target: editor; function onError(message) { errorText.text = message; errorDialog.open(); } }
    Dialog { id: errorDialog; anchors.centerIn: parent; width: 480; title: "COMSOC"; modal: true; standardButtons: Dialog.Ok; Text { id: errorText; width: parent.width; wrapMode: Text.WordWrap; color: Theme.text } }
    font.family: "Inter, Segoe UI, sans-serif"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Only the actions that truly belong to the model editor remain visible.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            color: Theme.window
            border.width: 1
            border.color: Theme.divider

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 7

                ToolButton {
                    id: backButton
                    onClicked: fileMenu.open()
                    Menu {
                        id: fileMenu
                        y: backButton.height
                        MenuItem { text: "Novo modelo  Ctrl+N"; onTriggered: editor.newDocument() }
                        MenuItem { text: "Abrir modelo…  Ctrl+O"; onTriggered: editor.openDialog() }
                        MenuItem { text: "Salvar como…  Ctrl+Shift+S"; onTriggered: editor.saveAs() }
                    }
                    Layout.preferredWidth: 84
                    Layout.preferredHeight: 32
                    hoverEnabled: true

                    contentItem: RowLayout {
                        spacing: 6

                        Text {
                            text: "‹"
                            color: backButton.hovered ? Theme.text : Theme.textMuted
                            font.pixelSize: 20
                        }

                        Text {
                            text: "Modelos"
                            color: backButton.hovered ? Theme.text : Theme.textMuted
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                    }

                    background: Rectangle {
                        radius: 6
                        color: backButton.hovered ? Theme.panelHover : "transparent"
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 24
                    color: Theme.divider
                }

                Rectangle {
                    Layout.preferredWidth: 26
                    Layout.preferredHeight: 26
                    radius: 7
                    color: Theme.accent

                    Text {
                        anchors.centerIn: parent
                        text: "C"
                        color: "#FFFFFF"
                        font.pixelSize: 13
                        font.weight: Font.Bold
                    }
                }

                ColumnLayout {
                    Layout.preferredWidth: 230
                    spacing: 0

                    RowLayout {
                        spacing: 6

                        Text {
                            text: editor.state.name
                            color: Theme.text
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }

                        Rectangle {
                            Layout.preferredWidth: 6
                            Layout.preferredHeight: 6
                            radius: 3
                            color: Theme.warning
                            visible: editor.state.dirty
                        }
                    }

                    Text {
                        text: "Editor de modelo"
                        color: Theme.textSubtle
                        font.pixelSize: 9
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                Text {
                    text: editor.state.dirty ? "Alterações não salvas" : "Salvo"
                    color: Theme.textSubtle
                    font.pixelSize: 9
                }

                ToolButton {
                    id: undoButton
                    enabled: editor.state.canUndo
                    onClicked: editor.undo()
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.text: "Desfazer  Ctrl+Z"

                    contentItem: Text {
                        text: "↶"
                        color: undoButton.hovered ? Theme.text : Theme.textMuted
                        font.pixelSize: 18
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 6
                        color: undoButton.hovered ? Theme.panelHover : "transparent"
                    }
                }

                ToolButton {
                    id: redoButton
                    enabled: editor.state.canRedo
                    onClicked: editor.redo()
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.text: "Refazer  Ctrl+Shift+Z"

                    contentItem: Text {
                        text: "↷"
                        color: redoButton.hovered ? Theme.text : Theme.textMuted
                        font.pixelSize: 18
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 6
                        color: redoButton.hovered ? Theme.panelHover : "transparent"
                    }
                }

                UiButton {
                    Layout.preferredWidth: 128
                    text: "Salvar modelo"
                    onClicked: editor.save()
                    tone: "primary"
                    compact: true
                }
            }
        }

        // Reserved page navigation. It states the current reality without promising add-page yet.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 38
            color: Theme.chrome
            border.width: 1
            border.color: Theme.divider

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 0

                Rectangle {
                    Layout.preferredWidth: 138
                    Layout.fillHeight: true
                    color: Theme.panel

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 13
                        anchors.rightMargin: 10
                        spacing: 8

                        EditorIcon {
                            Layout.preferredWidth: 14
                            Layout.preferredHeight: 14
                            name: "frame"
                            color: Theme.accentHover
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "Página 1"
                            color: Theme.text
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                        }
                    }

                    Rectangle {
                        width: parent.width
                        height: 2
                        anchors.bottom: parent.bottom
                        color: Theme.accent
                    }
                }

                Item {
                    Layout.fillWidth: true
                }
            }
        }

        // Geometry stays prominent because it is useful precision, not decorative complexity.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 45
            color: Theme.panel
            border.width: 1
            border.color: Theme.divider

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 7

                Rectangle {
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 30
                    radius: 7
                    color: Theme.accentSoft

                    Text {
                        anchors.centerIn: parent
                        text: window.selectionKind === "text" ? "T" : (window.selectionKind === "shape" ? "□" : "▧")
                        color: Theme.accentHover
                        font.pixelSize: 13
                        font.weight: Font.Bold
                    }
                }

                ColumnLayout {
                    Layout.preferredWidth: 104
                    spacing: 0

                    Text {
                        text: "SELEÇÃO"
                        color: Theme.textSubtle
                        font.pixelSize: 8
                        font.weight: Font.Bold
                        font.letterSpacing: 0.7
                    }

                    Text {
                        text: window.selectionName
                        color: Theme.text
                        font.pixelSize: 10
                        font.weight: Font.Medium
                        elide: Text.ElideRight
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 27
                    color: Theme.divider
                }

                CompactField {
                    label: "X"
                    value: Number((editor.state.selected.x || 0) * 1).toFixed(2)
                    enabled: !!editor.state.selected.key && !editor.state.selected.locked
                    onEdited: value => editor.setValue("x", Number(value.replace(",", ".")) / 1)
                    suffix: "px"
                    fieldWidth: 94
                }

                CompactField {
                    label: "Y"
                    value: Number((editor.state.selected.y || 0) * 1).toFixed(2)
                    enabled: !!editor.state.selected.key && !editor.state.selected.locked
                    onEdited: value => editor.setValue("y", Number(value.replace(",", ".")) / 1)
                    suffix: "px"
                    fieldWidth: 94
                }

                CompactField {
                    label: "L"
                    value: Number((editor.state.selected.w || 0) * 1).toFixed(2)
                    enabled: !!editor.state.selected.key && !editor.state.selected.locked
                    onEdited: value => editor.setValue("w", Number(value.replace(",", ".")) / 1)
                    suffix: "px"
                    fieldWidth: 100
                }

                CompactField {
                    label: "A"
                    value: Number((editor.state.selected.h || 0) * 1).toFixed(2)
                    enabled: !!editor.state.selected.key && !editor.state.selected.locked
                    onEdited: value => editor.setValue("h", Number(value.replace(",", ".")) / 1)
                    suffix: "px"
                    fieldWidth: 94
                }

                ToolButton {
                    id: proportionButton
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 30
                    checkable: true
                    checked: editor.state.selected.keep_proportion || false
                    enabled: !!editor.state.selected.key && !editor.state.selected.locked
                    onClicked: editor.setValue("keep_proportion", checked)
                    hoverEnabled: true
                    Accessible.name: "Manter proporção"
                    Accessible.description: checked ? "Largura e altura vinculadas" : "Largura e altura independentes"
                    ToolTip.visible: hovered
                    ToolTip.text: checked ? "Proporção vinculada — clique para desvincular" : "Proporção livre — clique para vincular"
                    ToolTip.delay: 450

                    contentItem: Item {
                        EditorIcon {
                            anchors.centerIn: parent
                            width: 19
                            height: 19
                            name: proportionButton.checked ? "link" : "unlink"
                            color: proportionButton.checked ? Theme.accentHover : Theme.textMuted
                        }
                    }

                    background: Rectangle {
                        radius: 6
                        color: proportionButton.down ? Theme.accentFaint : (proportionButton.checked ? Theme.accentSoft : (proportionButton.hovered ? Theme.panelHover : Theme.field))
                        border.width: 1
                        border.color: proportionButton.activeFocus ? Theme.accentHover : (proportionButton.checked ? Theme.accent : Theme.border)
                    }
                }

                CompactField {
                    label: "↻"
                    value: Number((editor.state.selected.rotation || 0) * 1).toFixed(2)
                    enabled: !!editor.state.selected.key && !editor.state.selected.locked && editor.state.selected.type !== "background"
                    onEdited: value => editor.setValue("rotation", Number(value.replace(",", ".")) / 1)
                    suffix: "°"
                    fieldWidth: 72
                }

                CompactField {
                    label: "α"
                    value: Number((editor.state.selected.opacity || 0) * 100).toFixed(0)
                    enabled: !!editor.state.selected.key && !editor.state.selected.locked
                    onEdited: value => editor.setValue("opacity", Number(value.replace(",", ".")) / 100)
                    suffix: "%"
                    fieldWidth: 78
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 27
                    color: Theme.divider
                }

                Text {
                    text: "GUIAS"
                    color: Theme.textSubtle
                    font.pixelSize: 8
                    font.weight: Font.Bold
                }

                Repeater {
                    model: [
                        {
                            icon: "guide-horizontal",
                            tip: "Adicionar guia horizontal"
                        },
                        {
                            icon: "guide-vertical",
                            tip: "Adicionar guia vertical"
                        },
                        {
                            icon: "eye",
                            tip: "Mostrar ou ocultar guias"
                        },
                        {
                            icon: "lock",
                            tip: "Bloquear ou desbloquear guias"
                        }
                    ]
                    delegate: ToolButton {
                        id: guideControl
                        required property var modelData
                        Layout.preferredWidth: 30
                        Layout.preferredHeight: 30
                        hoverEnabled: true
                        checkable: modelData.icon === "eye" || modelData.icon === "lock"
                        checked: modelData.icon === "eye" ? window.showGuides : (modelData.icon === "lock" && window.guidesLocked)
                        Accessible.name: modelData.tip
                        ToolTip.visible: hovered
                        ToolTip.text: modelData.tip
                        onClicked: {
                            if (modelData.icon === "eye")
                                editor.guideOption("guidelines_visible", checked);
                            else if (modelData.icon === "lock")
                                editor.guideOption("guidelines_locked", checked);
                            else editor.addGuide(modelData.icon === "guide-vertical");
                        }
                        contentItem: EditorIcon {
                            name: guideControl.modelData.icon
                            color: guideControl.checked ? Theme.guide : Theme.textMuted
                        }
                        background: Rectangle {
                            radius: 6
                            color: guideControl.checked ? Theme.accentSoft : (guideControl.hovered ? Theme.panelHover : "transparent")
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 27
                    color: Theme.divider
                }


                Item {
                    Layout.fillWidth: true
                }

                Text {
                    visible: window.width >= 1550
                    text: "Arraste o objeto ou informe medidas exatas"
                    color: Theme.textDisabled
                    font.pixelSize: 9
                }
            }
        }

        SplitView {
            id: workspaceSplit

            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            handle: Rectangle {
                id: splitHandle
                implicitWidth: 5
                color: SplitHandle.pressed ? Theme.accent : (SplitHandle.hovered ? Theme.borderStrong : Theme.divider)

                Rectangle {
                    width: 1
                    height: parent.height
                    anchors.centerIn: parent
                    color: splitHandle.color
                }
            }

            LeftDock {
                id: leftDock

                SplitView.minimumWidth: 226
                SplitView.preferredWidth: 262
                SplitView.maximumWidth: 350

            }

            CanvasWorkspace {
                id: canvasWorkspace
                SplitView.minimumWidth: 470
                SplitView.fillWidth: true
                zoomValue: window.zoomValue
                showGrid: window.showGrid
                showGuides: window.showGuides
                onZoomRequested: value => window.zoomValue = value
            }

            InspectorDock {
                selectionKind: window.selectionKind
                selectionIndex: window.selectionIndex
                selectionName: window.selectionName
                selectionContent: window.selectionContent
                SplitView.minimumWidth: 292
                SplitView.preferredWidth: 322
                SplitView.maximumWidth: 390
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 29
            color: Theme.window
            border.width: 1
            border.color: Theme.divider

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 9

                Text {
                    text: "Camada selecionada: " + window.selectionName
                    color: Theme.textMuted
                    font.pixelSize: 9
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 15
                    color: Theme.divider
                }

                Text {
                    text: "Documento " + editor.state.width + " × " + editor.state.height + " px"
                    color: Theme.textSubtle
                    font.pixelSize: 9
                }

                Item {
                    Layout.fillWidth: true
                }


                ToolButton {
                    id: gridButton
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 24
                    checkable: true
                    checked: window.showGrid
                    onClicked: window.showGrid = checked
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.text: "Grade"

                    contentItem: EditorIcon {
                        anchors.centerIn: parent
                        width: 14
                        height: 14
                        name: "grid"
                        color: gridButton.checked ? Theme.accentHover : Theme.textMuted
                    }

                    background: Rectangle {
                        radius: 5
                        color: gridButton.checked ? Theme.accentSoft : (gridButton.hovered ? Theme.panelHover : "transparent")
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 15
                    color: Theme.divider
                }

                Text {
                    text: "Página 1 de 1"
                    color: Theme.textMuted
                    font.pixelSize: 9
                }

                ToolButton {
                    id: zoomOutButton
                    Layout.preferredWidth: 25
                    Layout.preferredHeight: 24
                    text: "−"
                    onClicked: window.zoomValue = Math.max(10, window.zoomValue - 10)

                    contentItem: Text {
                        text: zoomOutButton.text
                        color: Theme.textMuted
                        font.pixelSize: 15
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 5
                        color: zoomOutButton.hovered ? Theme.panelHover : "transparent"
                    }
                }

                Slider {
                    id: zoomSlider
                    Layout.preferredWidth: 92
                    Layout.preferredHeight: 24
                    from: 10
                    to: 200
                    value: window.zoomValue
                    onMoved: window.zoomValue = value

                    background: Rectangle {
                        x: zoomSlider.leftPadding
                        y: zoomSlider.topPadding + zoomSlider.availableHeight / 2 - height / 2
                        width: zoomSlider.availableWidth
                        height: 3
                        radius: 2
                        color: Theme.borderStrong

                        Rectangle {
                            width: zoomSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 2
                            color: Theme.accent
                        }
                    }

                    handle: Rectangle {
                        x: zoomSlider.leftPadding + zoomSlider.visualPosition * (zoomSlider.availableWidth - width)
                        y: zoomSlider.topPadding + zoomSlider.availableHeight / 2 - height / 2
                        implicitWidth: 11
                        implicitHeight: 11
                        radius: 6
                        color: zoomSlider.pressed ? Theme.accentHover : Theme.text
                        border.width: 2
                        border.color: Theme.accent
                    }
                }

                Text {
                    Layout.preferredWidth: 34
                    text: Math.round(window.zoomValue) + "%"
                    color: Theme.text
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignRight
                }

                ToolButton {
                    id: zoomInButton
                    Layout.preferredWidth: 25
                    Layout.preferredHeight: 24
                    text: "+"
                    onClicked: window.zoomValue = Math.min(200, window.zoomValue + 10)

                    contentItem: Text {
                        text: zoomInButton.text
                        color: Theme.textMuted
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 5
                        color: zoomInButton.hovered ? Theme.panelHover : "transparent"
                    }
                }
            }
        }
    }
}
