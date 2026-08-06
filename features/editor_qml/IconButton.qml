import QtQuick
import QtQuick.Controls

ToolButton {
    id: control

    property string glyph: ""
    property string label: ""
    property bool selected: false
    property color glyphColor: selected ? Theme.accent : Theme.textMuted

    implicitWidth: 36
    implicitHeight: 36
    hoverEnabled: true

    ToolTip.visible: hovered && label.length > 0
    ToolTip.text: label
    ToolTip.delay: 450

    contentItem: Text {
        text: control.glyph
        color: control.enabled ? control.glyphColor : Theme.textDisabled
        font.pixelSize: 18
        font.weight: Font.Medium
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: Theme.radiusSmall
        color: control.down ? Theme.accentSoft : (control.selected ? Theme.accentFaint : (control.hovered ? Theme.panelHover : "transparent"))
        border.width: control.selected ? 1 : 0
        border.color: control.selected ? Theme.accent : "transparent"

        Behavior on color {
            ColorAnimation {
                duration: 100
            }
        }
    }
}
