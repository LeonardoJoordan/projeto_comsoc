import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    property string label: "Cor"
    property string value: "#000000"
    property bool enabledField: true
    property bool externallyManaged: false
    onValueChanged: hexInput.text = value
    signal edited(string value)
    spacing: 5
    Layout.fillWidth: true

    function commitHex() {
        const candidate = hexInput.text.trim();
        if (/^#?[0-9a-fA-F]{6}$/.test(candidate)) {
            const color = (candidate.startsWith("#") ? candidate : "#" + candidate).toUpperCase();
            if (!root.externallyManaged) root.value = color;
            root.edited(color);
        }
        hexInput.text = root.value;
    }

    Text {
        text: root.label
        color: root.enabledField ? Theme.textMuted : Theme.textDisabled
        font.pixelSize: 11
        font.weight: Font.Medium
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        opacity: root.enabledField ? 1 : 0.55
        ToolButton {
            id: swatch
            Layout.preferredWidth: 32
            Layout.preferredHeight: 34
            enabled: root.enabledField
            hoverEnabled: true
            Accessible.name: "Escolher " + root.label.toLowerCase()
            ToolTip.visible: hovered
            ToolTip.text: "Escolher cor"
            onClicked: {
                root.commitHex();
                picker.openFor(root.value);
            }
            contentItem: Rectangle {
                color: root.value
                radius: 3
                border.color: Theme.borderStrong
            }
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.field
                border.color: swatch.activeFocus || swatch.hovered ? Theme.accent : Theme.border
            }
        }
        TextField {
            id: hexInput
            Layout.fillWidth: true
            Layout.minimumWidth: 74
            Layout.preferredWidth: 90
            Layout.preferredHeight: 34
            enabled: root.enabledField
            text: root.value
            maximumLength: 7
            selectByMouse: true
            font.pixelSize: 11
            color: Theme.text
            selectionColor: Theme.accentSoft
            selectedTextColor: Theme.text
            Accessible.name: root.label + " em hexadecimal"
            onEditingFinished: root.commitHex()
            background: Rectangle {
                color: Theme.field
                radius: Theme.radiusSmall
                border.color: hexInput.activeFocus ? Theme.accent : Theme.border
            }
        }
    }
    ColorPicker {
        id: picker
        title: root.label
        onColorChosen: color => {
            const hex = color.toString().toUpperCase();
            if (!root.externallyManaged) root.value = hex;
            root.edited(hex);
            hexInput.text = root.value;
        }
    }
}
