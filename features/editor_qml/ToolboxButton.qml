import QtQuick
import QtQuick.Controls

ToolButton {
    id: control

    property string iconName: "select"
    property string title: "Ferramenta"
    property string shortcut: ""
    property bool selected: false
    property bool grouped: false

    implicitWidth: 40
    implicitHeight: 40
    hoverEnabled: true

    ToolTip.visible: hovered
    ToolTip.text: shortcut.length > 0 ? title + "  (" + shortcut + ")" : title
    ToolTip.delay: 420

    contentItem: EditorIcon {
        name: control.iconName
        color: control.selected ? "#FFFFFF" : (control.hovered ? Theme.text : Theme.textMuted)
        anchors.centerIn: parent
        width: 20
        height: 20
    }

    background: Rectangle {
        radius: 7
        color: control.down ? Theme.accentSoft : (control.selected ? Theme.accent : (control.hovered ? Theme.panelHover : "transparent"))

        Behavior on color {
            ColorAnimation {
                duration: 90
            }
        }
    }

    Rectangle {
        visible: control.grouped
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 4
        anchors.bottomMargin: 4
        width: 4
        height: 4
        color: control.selected ? "#FFFFFF" : Theme.textSubtle
        rotation: 45
    }
}
