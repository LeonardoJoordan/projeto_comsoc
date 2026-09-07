pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    property bool vertical: false
    property int selectedIndex: 1
    signal chosen(int index)
    spacing: 6
    Text {
        text: root.vertical ? "Alinhamento vertical" : "Alinhamento horizontal"
        color: Theme.textMuted
        font.pixelSize: 11
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 4
        Repeater {
            model: root.vertical ? ["Topo", "Meio", "Base"] : ["Esquerda", "Centro", "Direita", "Justificado"]
            delegate: ToolButton {
                id: button
                required property int index
                required property string modelData
                Layout.fillWidth: true
                Layout.preferredHeight: 32
                hoverEnabled: true
                Accessible.name: (root.vertical ? "Alinhamento vertical: " : "Alinhamento horizontal: ") + modelData
                ToolTip.visible: hovered
                ToolTip.text: modelData
                onClicked: root.chosen(index)
                contentItem: Item {
                    EditorIcon {
                        anchors.centerIn: parent
                        width: 18
                        height: 18
                        name: (root.vertical ? "valign-" : "align-") + button.index
                        color: root.selectedIndex === button.index ? Theme.accentHover : Theme.textMuted
                    }
                }
                background: Rectangle {
                    radius: 4
                    color: root.selectedIndex === button.index ? Theme.accentSoft : (button.hovered ? Theme.panelHover : Theme.field)
                    border.width: 1
                    border.color: button.activeFocus ? Theme.accent : Theme.border
                }
            }
        }
    }
}
