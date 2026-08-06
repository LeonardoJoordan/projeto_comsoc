import QtQuick
import QtQuick.Controls

Button {
    id: control

    property string tone: "neutral"
    property bool compact: false

    implicitHeight: compact ? 32 : Theme.controlHeight
    implicitWidth: Math.max(compact ? 76 : 104, contentItem.implicitWidth + 28)
    leftPadding: 14
    rightPadding: 14
    hoverEnabled: true

    font.pixelSize: 13
    font.weight: tone === "primary" ? Font.DemiBold : Font.Medium

    contentItem: Text {
        text: control.text
        color: control.enabled ? (control.tone === "primary" ? "#FFFFFF" : Theme.text) : Theme.textDisabled
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: Theme.radiusSmall
        color: {
            if (!control.enabled)
                return Theme.field;
            if (control.tone === "primary")
                return control.down ? "#655BD8" : (control.hovered ? Theme.accentHover : Theme.accent);
            if (control.tone === "danger")
                return control.down ? "#4A242B" : (control.hovered ? "#3A242B" : "transparent");
            return control.down ? Theme.panelRaised : (control.hovered ? Theme.panelHover : Theme.panelRaised);
        }
        border.width: control.tone === "primary" ? 0 : 1
        border.color: control.tone === "danger" ? "#6B333C" : Theme.border

        Behavior on color {
            ColorAnimation {
                duration: 110
            }
        }
    }
}
