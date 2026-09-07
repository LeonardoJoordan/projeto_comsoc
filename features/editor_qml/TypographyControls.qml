pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    readonly property var selected: editor.state.selected
    enabled: selected.type === "text" && !selected.locked
    spacing: 12
    Text {
        text: "Fonte"
        color: Theme.textMuted
        font.pixelSize: 11
    }
    ComboBox {
        id: fontSelector
        objectName: "fontSelector"
        Layout.fillWidth: true
        model: Qt.fontFamilies()
        currentIndex: Math.max(0, find(editor.state.selected.font_family || "Arial"))
        onActivated: editor.setValue("font_family", currentText)
        Accessible.name: "Fonte"
        contentItem: Text {
            text: fontSelector.displayText
            font.family: fontSelector.displayText
            font.pixelSize: 12
            color: Theme.text
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            leftPadding: 10
            rightPadding: 28
        }
        indicator: Text {
            x: fontSelector.width - width - 10
            anchors.verticalCenter: parent.verticalCenter
            text: "⌄"
            color: Theme.textMuted
        }
        background: Rectangle {
            implicitHeight: 34
            color: Theme.field
            radius: 5
            border.color: fontSelector.activeFocus ? Theme.accent : Theme.border
        }
        delegate: ItemDelegate {
            required property string modelData
            width: fontSelector.width
            height: 32
            contentItem: Text {
                text: modelData
                font.family: modelData
                font.pixelSize: 12
                color: Theme.text
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle { color: parent.hovered ? Theme.panelHover : Theme.panel }
        }
        popup: Popup {
            y: fontSelector.height + 4
            width: fontSelector.width
            height: Math.min(280, fontList.contentHeight + 8)
            padding: 4
            contentItem: ListView {
                id: fontList
                clip: true
                model: fontSelector.popup.visible ? fontSelector.delegateModel : null
                currentIndex: fontSelector.highlightedIndex
                ScrollBar.vertical: ScrollBar {}
            }
            background: Rectangle { color: Theme.panel; border.color: Theme.borderStrong; radius: 5 }
        }
    }
    RowLayout {
        spacing: 8
        PropertyField { label: "Tamanho"; value: String(editor.state.selected.font_size || 16); suffix: "pt"; onEdited: value => editor.setValue("font_size", value) }
        ColorField { label: "Cor do texto"; externallyManaged: true; value: editor.state.selected.font_color || "#000000"; onEdited: value => editor.setValue("font_color", value) }
    }
    RowLayout {
        spacing: 5
        Repeater {
            model: ["Negrito", "Itálico", "Sublinhado"]
            delegate: ToolButton {
                id: styleButton
                required property int index
                required property string modelData
                Layout.preferredWidth: 34
                Layout.preferredHeight: 32
                onClicked: editor.formatText(modelData)
                readonly property bool active: !!editor.state.selected[["bold", "italic", "underline"][index]]
                hoverEnabled: true
                Accessible.name: modelData
                ToolTip.visible: hovered
                ToolTip.text: modelData
                contentItem: Text {
                    text: ["B", "I", "U"][styleButton.index]
                    font.pixelSize: 14
                    font.bold: styleButton.index === 0
                    font.italic: styleButton.index === 1
                    font.underline: styleButton.index === 2
                    color: styleButton.active ? Theme.accentHover : Theme.textMuted
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 4
                    color: styleButton.active ? Theme.accentSoft : Theme.field
                    border.color: styleButton.activeFocus ? Theme.accent : Theme.border
                }
            }
        }
    }
    AlignmentControl { Layout.fillWidth: true; selectedIndex: ["left","center","right","justify"].indexOf(editor.state.selected.align || "left"); onChosen: index => editor.setValue("align", ["left","center","right","justify"][index]) }
    AlignmentControl { Layout.fillWidth: true; vertical: true; selectedIndex: ["top","center","bottom"].indexOf(editor.state.selected.vertical_align || "top"); onChosen: index => editor.setValue("vertical_align", ["top","center","bottom"][index]) }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        PropertyField { Layout.preferredWidth: 1; label: "Entrelinha"; value: String(editor.state.selected.line_height || 1.15); onEdited: value => editor.setValue("line_height", value) }
        PropertyField { Layout.preferredWidth: 1; label: "Recuo"; value: String(editor.state.selected.indent_px || 0); suffix: "px"; onEdited: value => editor.setValue("indent_px", value) }
    }
}
