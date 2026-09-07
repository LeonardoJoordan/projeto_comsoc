import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

Item {
    id: root

    property string title: ""
    property string caption: ""
    property string iconName: "sliders"
    property bool collapsible: false
    property bool expanded: true
    property bool available: true
    property string unavailableReason: ""

    onAvailableChanged: {
        if (!available)
            expanded = false;
    }
    property int horizontalPadding: 14
    property int topPadding: 0
    property int bottomPadding: 0
    default property alias sectionData: contentColumn.data

    implicitHeight: layout.implicitHeight + topPadding + bottomPadding
    Layout.fillWidth: true

    ColumnLayout {
        id: layout
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: root.horizontalPadding
        anchors.rightMargin: root.horizontalPadding
        y: root.topPadding
        spacing: Theme.space3

        ToolButton {
            id: sectionHeader
            Layout.fillWidth: true
            implicitHeight: root.collapsible ? (root.caption.length > 0 ? 50 : 40) : 26
            enabled: root.collapsible && root.available
            hoverEnabled: true
            padding: 0
            Accessible.name: root.title
            Accessible.description: !root.available ? root.unavailableReason : (root.expanded ? "Seção expandida" : "Seção recolhida")
            onClicked: root.expanded = !root.expanded

            contentItem: RowLayout {
                spacing: Theme.space2
                EditorIcon {
                    visible: root.collapsible
                    Layout.preferredWidth: 15
                    Layout.preferredHeight: 15
                    name: root.iconName
                    color: root.available ? Theme.textMuted : Theme.textDisabled
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    Text {
                        Layout.fillWidth: true
                        text: root.title.toUpperCase()
                        color: root.available ? Theme.textMuted : Theme.textDisabled
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                        font.letterSpacing: 0.7
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: root.caption.length > 0
                        text: root.caption
                        color: Theme.textSubtle
                        font.pixelSize: 9
                    }
                }
                Text {
                    visible: root.collapsible
                    text: !root.available ? "—" : (root.expanded ? "⌄" : "›")
                    color: Theme.textSubtle
                    font.pixelSize: 16
                }
            }
            background: Rectangle {
                x: root.collapsible ? -root.horizontalPadding : 0
                width: sectionHeader.width + (root.collapsible ? root.horizontalPadding * 2 : 0)
                color: root.collapsible ? Theme.chrome : "transparent"
                Rectangle {
                    visible: root.collapsible
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: sectionHeader.activeFocus ? Theme.accent : Theme.divider
                }
            }
        }

        ColumnLayout {
            id: contentColumn
            visible: root.expanded && root.available
            enabled: root.available
            Layout.fillWidth: true
            spacing: Theme.space2
        }
    }
}
