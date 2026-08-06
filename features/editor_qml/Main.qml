pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window

    property real zoomValue: 82
    property bool showGrid: false
    property bool showGuides: true
    property bool guidesLocked: false

    width: 1500
    height: 930
    minimumWidth: 1120
    minimumHeight: 700
    visible: true
    color: Theme.window
    title: "COMSOC Studio — Certificado editorial"
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
                            text: "Certificado editorial"
                            color: Theme.text
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }

                        Rectangle {
                            Layout.preferredWidth: 6
                            Layout.preferredHeight: 6
                            radius: 3
                            color: Theme.warning
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
                    text: "Alterações não salvas"
                    color: Theme.textSubtle
                    font.pixelSize: 9
                }

                ToolButton {
                    id: undoButton
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
                        text: "T"
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
                        text: "Nome completo"
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
                    value: "46,57"
                    suffix: "mm"
                    fieldWidth: 94
                }

                CompactField {
                    label: "Y"
                    value: "70,11"
                    suffix: "mm"
                    fieldWidth: 94
                }

                CompactField {
                    label: "L"
                    value: "107,95"
                    suffix: "mm"
                    fieldWidth: 100
                }

                CompactField {
                    label: "A"
                    value: "15,35"
                    suffix: "mm"
                    fieldWidth: 94
                }

                ToolButton {
                    id: proportionButton
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 30
                    checkable: true
                    checked: true
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.text: "Manter proporção"

                    contentItem: Text {
                        text: "⌁"
                        color: proportionButton.checked ? Theme.accentHover : Theme.textMuted
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 6
                        color: proportionButton.checked ? Theme.accentSoft : (proportionButton.hovered ? Theme.panelHover : "transparent")
                    }
                }

                CompactField {
                    label: "↻"
                    value: "0"
                    suffix: "°"
                    fieldWidth: 72
                }

                CompactField {
                    label: "α"
                    value: "100"
                    suffix: "%"
                    fieldWidth: 78
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 27
                    color: Theme.divider
                }

                UiButton {
                    Layout.preferredWidth: 88
                    text: "Alinhar  ▾"
                    compact: true
                }

                Item {
                    Layout.fillWidth: true
                }

                Text {
                    visible: window.width >= 1320
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
                guidesVisible: window.showGuides
                guidesLocked: window.guidesLocked
                onGuidesVisibilityRequested: visible => window.showGuides = visible
                onGuidesLockRequested: locked => window.guidesLocked = locked
            }

            CanvasWorkspace {
                SplitView.minimumWidth: 470
                SplitView.fillWidth: true
                zoomValue: window.zoomValue
                showGrid: window.showGrid
                showGuides: window.showGuides
                onZoomRequested: value => window.zoomValue = value
            }

            InspectorDock {
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
                    text: "Texto selecionado: Nome completo"
                    color: Theme.textMuted
                    font.pixelSize: 9
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 15
                    color: Theme.divider
                }

                Text {
                    text: "Documento 148 × 105 mm"
                    color: Theme.textSubtle
                    font.pixelSize: 9
                }

                Item {
                    Layout.fillWidth: true
                }

                ToolButton {
                    id: guidesButton
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 24
                    checkable: true
                    checked: window.showGuides
                    onClicked: window.showGuides = checked
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.text: "Guias inteligentes"

                    contentItem: EditorIcon {
                        anchors.centerIn: parent
                        width: 14
                        height: 14
                        name: "guide"
                        color: guidesButton.checked ? Theme.guide : Theme.textMuted
                    }

                    background: Rectangle {
                        radius: 5
                        color: guidesButton.checked ? "#23383E" : (guidesButton.hovered ? Theme.panelHover : "transparent")
                    }
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
