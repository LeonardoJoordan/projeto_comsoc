import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: root
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 340
    padding: 18
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape
    property real hue: 0
    property real saturation: 0
    property real brightness: 0
    property color originalColor: "#000000"
    readonly property color chosenColor: Qt.hsva(hue, saturation, brightness, 1)
    signal colorChosen(color color)

    function openFor(color) {
        originalColor = color;
        hue = Math.max(0, originalColor.hsvHue);
        saturation = originalColor.hsvSaturation;
        brightness = originalColor.hsvValue;
        open();
    }
    onAccepted: colorChosen(chosenColor)
    background: Rectangle {
        color: Theme.panel
        radius: 10
        border.color: Theme.borderStrong
    }
    header: Text {
        text: root.title
        color: Theme.text
        font.pixelSize: 13
        font.weight: Font.DemiBold
        padding: 18
        bottomPadding: 0
    }
    contentItem: ColumnLayout {
        spacing: 14
        Rectangle {
            id: square
            objectName: "saturationBrightnessSquare"
            Layout.fillWidth: true
            Layout.preferredHeight: 220
            color: Qt.hsva(root.hue, 1, 1, 1)
            activeFocusOnTab: true
            Accessible.name: "Saturação e brilho"
            Keys.onLeftPressed: root.saturation = Math.max(0, root.saturation - 0.01)
            Keys.onRightPressed: root.saturation = Math.min(1, root.saturation + 0.01)
            Keys.onUpPressed: root.brightness = Math.min(1, root.brightness + 0.01)
            Keys.onDownPressed: root.brightness = Math.max(0, root.brightness - 0.01)
            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: "#FFFFFF" }
                    GradientStop { position: 1; color: "#00FFFFFF" }
                }
            }
            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0; color: "#00000000" }
                    GradientStop { position: 1; color: "#FF000000" }
                }
            }
            Rectangle {
                width: 12
                height: 12
                radius: 6
                x: root.saturation * square.width - width / 2
                y: (1 - root.brightness) * square.height - height / 2
                color: "transparent"
                border.width: 2
                border.color: "white"
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 2
                    radius: 4
                    color: "transparent"
                    border.color: "#66000000"
                }
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.CrossCursor
                function updateColor(mouse) {
                    root.saturation = Math.max(0, Math.min(1, mouse.x / width));
                    root.brightness = 1 - Math.max(0, Math.min(1, mouse.y / height));
                }
                onPressed: mouse => { square.forceActiveFocus(); updateColor(mouse); }
                onPositionChanged: mouse => { if (pressed) updateColor(mouse); }
            }
        }
        Slider {
            id: hueSlider
            objectName: "hueSlider"
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            from: 0
            to: 1
            value: root.hue
            onMoved: root.hue = value
            Accessible.name: "Tom da cor"
            background: Rectangle {
                x: hueSlider.leftPadding
                y: (hueSlider.height - height) / 2
                width: hueSlider.availableWidth
                height: 12
                radius: 3
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: "#FF0000" }
                    GradientStop { position: 0.1667; color: "#FFFF00" }
                    GradientStop { position: 0.3333; color: "#00FF00" }
                    GradientStop { position: 0.5; color: "#00FFFF" }
                    GradientStop { position: 0.6667; color: "#0000FF" }
                    GradientStop { position: 0.8333; color: "#FF00FF" }
                    GradientStop { position: 1; color: "#FF0000" }
                }
            }
            handle: Rectangle {
                x: hueSlider.leftPadding + hueSlider.visualPosition * (hueSlider.availableWidth - width)
                y: (hueSlider.height - height) / 2
                width: 8
                height: 20
                radius: 3
                color: "transparent"
                border.width: 2
                border.color: Theme.text
            }
        }
        RowLayout {
            spacing: 8
            ColumnLayout {
                Text { text: "Atual"; color: Theme.textSubtle; font.pixelSize: 10 }
                Rectangle { width: 48; height: 28; radius: 4; color: root.originalColor; border.color: Theme.borderStrong }
            }
            ColumnLayout {
                Text { text: "Nova"; color: Theme.textSubtle; font.pixelSize: 10 }
                Rectangle { width: 48; height: 28; radius: 4; color: root.chosenColor; border.color: Theme.borderStrong }
            }
            Text {
                Layout.fillWidth: true
                text: root.chosenColor.toString().toUpperCase()
                color: Theme.text
                font.pixelSize: 12
                horizontalAlignment: Text.AlignRight
            }
        }
        RowLayout {
            Layout.topMargin: 4
            spacing: 8
            UiButton { Layout.fillWidth: true; text: "Cancelar"; compact: true; onClicked: root.reject() }
            UiButton { Layout.fillWidth: true; text: "Aplicar"; compact: true; tone: "primary"; onClicked: root.accept() }
        }
    }
}
