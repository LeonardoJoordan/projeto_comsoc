import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root

    property string label: ""
    property string value: ""
    property string suffix: ""
    property bool enabledField: true
    signal edited(string value)
    onValueChanged: field.text = value

    spacing: 5
    Layout.fillWidth: true

    Text {
        text: root.label
        color: root.enabledField ? Theme.textMuted : Theme.textDisabled
        font.pixelSize: 11
        font.weight: Font.Medium
    }

    Rectangle {
        Layout.fillWidth: true
        implicitHeight: 34
        radius: Theme.radiusSmall
        color: Theme.field
        border.width: 1
        border.color: field.activeFocus ? Theme.accent : Theme.border
        opacity: root.enabledField ? 1 : 0.55

        TextInput {
            id: field
            anchors.left: parent.left
            anchors.right: suffixText.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.leftMargin: 10
            anchors.rightMargin: 6
            text: root.value
            onEditingFinished: root.edited(text)
            color: Theme.text
            selectByMouse: true
            enabled: root.enabledField
            font.pixelSize: 12
            verticalAlignment: TextInput.AlignVCenter
            selectionColor: Theme.accentSoft
            selectedTextColor: Theme.text
        }

        Text {
            id: suffixText
            anchors.right: parent.right
            anchors.rightMargin: 9
            anchors.verticalCenter: parent.verticalCenter
            text: root.suffix
            color: Theme.textSubtle
            font.pixelSize: 11
        }
    }
}
