import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root

    property string label: "X"
    property string value: "0"
    property string suffix: ""
    property int fieldWidth: 78
    signal edited(string value)
    onValueChanged: input.text = value

    implicitWidth: fieldWidth
    implicitHeight: 30
    radius: 6
    color: Theme.field
    border.width: 1
    border.color: input.activeFocus ? Theme.accent : Theme.border

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 7
        spacing: 5

        Text {
            text: root.label
            color: Theme.textSubtle
            font.pixelSize: 10
            font.weight: Font.DemiBold
        }

        TextInput {
            id: input
            Layout.fillWidth: true
            text: root.value
            onEditingFinished: root.edited(text)
            color: Theme.text
            selectByMouse: true
            font.pixelSize: 11
            verticalAlignment: TextInput.AlignVCenter
            horizontalAlignment: TextInput.AlignRight
            selectionColor: Theme.accentSoft
            selectedTextColor: Theme.text
        }

        Text {
            visible: root.suffix.length > 0
            text: root.suffix
            color: Theme.textDisabled
            font.pixelSize: 9
        }
    }
}
