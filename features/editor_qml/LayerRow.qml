import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root

    property string kind: "T"
    property string title: "Camada"
    property string detail: "Texto"
    property bool selected: false
    property bool locked: false
    property bool visibleLayer: true

    signal activated
    signal visibilityRequested
    signal lockRequested

    implicitHeight: 46
    radius: Theme.radiusSmall
    color: selected ? Theme.accentFaint : (mouse.containsMouse ? Theme.panelHover : "transparent")
    border.width: selected ? 1 : 0
    border.color: selected ? Theme.accent : "transparent"

    Behavior on color {
        ColorAnimation {
            duration: 100
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.activated()
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        spacing: 9

        Rectangle {
            Layout.preferredWidth: 30
            Layout.preferredHeight: 30
            radius: 7
            color: root.selected ? Theme.accentSoft : Theme.panelRaised
            border.width: 1
            border.color: Theme.border

            Text {
                anchors.centerIn: parent
                text: root.kind
                color: root.selected ? Theme.accent : Theme.textMuted
                font.pixelSize: 12
                font.weight: Font.Bold
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 1

            Text {
                Layout.fillWidth: true
                text: root.title
                color: Theme.text
                font.pixelSize: 12
                font.weight: Font.Medium
                elide: Text.ElideRight
            }

            Text {
                Layout.fillWidth: true
                text: root.detail
                color: Theme.textSubtle
                font.pixelSize: 10
                elide: Text.ElideRight
            }
        }

        EditorIcon {
            Layout.preferredWidth: 14
            Layout.preferredHeight: 14
            name: "eye"
            MouseArea { anchors.fill: parent; onClicked: root.visibilityRequested() }
            color: root.visibleLayer ? Theme.textMuted : Theme.textDisabled
            opacity: root.visibleLayer ? 1 : 0.35
        }

        EditorIcon {
            Layout.preferredWidth: 13
            Layout.preferredHeight: 13
            name: "lock"
            MouseArea { anchors.fill: parent; onClicked: root.lockRequested() }
            color: root.locked ? Theme.warning : Theme.textDisabled
            opacity: root.locked ? 1 : 0.28
        }
    }
}
