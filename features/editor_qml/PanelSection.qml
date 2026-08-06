import QtQuick
import QtQuick.Layouts

Item {
    id: root

    property string title: ""
    property string caption: ""
    property bool collapsible: false
    property bool expanded: true
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

        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.space2

            Text {
                Layout.fillWidth: true
                text: root.title.toUpperCase()
                color: Theme.textMuted
                font.pixelSize: 11
                font.weight: Font.DemiBold
                font.letterSpacing: 0.7
            }

            Text {
                visible: root.caption.length > 0
                text: root.caption
                color: Theme.textSubtle
                font.pixelSize: 11
            }

            Text {
                visible: root.collapsible
                text: root.expanded ? "−" : "+"
                color: Theme.textSubtle
                font.pixelSize: 15
            }
        }

        ColumnLayout {
            id: contentColumn
            visible: root.expanded
            Layout.fillWidth: true
            spacing: Theme.space2
        }
    }
}
