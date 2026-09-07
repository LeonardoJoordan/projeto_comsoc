import QtQuick
import QtQuick.Controls

Switch {
    id: control

    implicitWidth: 42
    implicitHeight: 24
    padding: 0
    hoverEnabled: true

    indicator: Rectangle {
        implicitWidth: 36
        implicitHeight: 20
        x: (control.width - width) / 2
        y: (control.height - height) / 2
        radius: 10
        color: control.checked ? Theme.accent : Theme.borderStrong
        border.width: control.activeFocus ? 1 : 0
        border.color: Theme.accentHover

        Rectangle {
            width: 14
            height: 14
            radius: 7
            x: control.checked ? parent.width - width - 3 : 3
            y: 3
            color: control.enabled ? Theme.text : Theme.textDisabled
        }
    }
    contentItem: Item {}
    background: Item {}
}
