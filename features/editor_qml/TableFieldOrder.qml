pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    spacing: 8
    property int draggedIndex: -1
    property int dropIndex: -1
    ListModel { id: fields }
    function syncFields() {
        fields.clear();
        for (const label of editor.state.fields) fields.append({label: label});
    }
    Component.onCompleted: syncFields()
    Connections { target: editor; function onChanged() { root.syncFields(); } }
    Text {
        Layout.fillWidth: true
        text: "Segure e arraste os campos para mudar a ordem."
        color: Theme.textSubtle
        font.pixelSize: 10
        wrapMode: Text.WordWrap
    }
    Column {
        id: fieldList
        Layout.fillWidth: true
        spacing: 8

        Repeater {
            model: fields
            delegate: Item {
                id: fieldRow
                required property int index
                required property string label
                width: fieldList.width
                height: 40
                z: root.draggedIndex === index ? 1 : 0

                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    color: Theme.field
                    border.width: root.dropIndex === fieldRow.index ? 1 : 0
                    border.color: Theme.accent
                }

                Rectangle {
                    id: card
                    width: parent.width
                    height: parent.height
                    radius: 5
                    color: mouse.drag.active ? Theme.accentFaint : (mouse.containsMouse ? Theme.panelHover : Theme.panelRaised)
                    border.width: mouse.drag.active ? 1 : 0
                    border.color: Theme.accent
                    opacity: mouse.drag.active ? 0.9 : 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 8
                        EditorIcon {
                            Layout.preferredWidth: 14
                            Layout.preferredHeight: 16
                            name: "grip"
                            color: Theme.textSubtle
                        }
                        Text { text: fieldRow.index + 1; color: Theme.textSubtle; font.pixelSize: 10 }
                        Text {
                            Layout.fillWidth: true
                            text: fieldRow.label
                            color: Theme.textMuted
                            font.pixelSize: 11
                            elide: Text.ElideRight
                        }
                    }

                    MouseArea {
                        id: mouse
                        anchors.fill: parent
                        hoverEnabled: true
                        preventStealing: true
                        cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                        drag.target: card
                        drag.axis: Drag.YAxis
                        drag.minimumY: -fieldRow.y
                        drag.maximumY: fieldList.height - fieldRow.y - card.height
                        onPositionChanged: {
                            if (drag.active) {
                                root.draggedIndex = fieldRow.index;
                                const center = card.mapToItem(fieldList, 0, card.height / 2).y;
                                root.dropIndex = Math.max(0, Math.min(fields.count - 1, Math.floor(center / (fieldRow.height + fieldList.spacing))));
                            }
                        }
                        onReleased: {
                            const destination = root.dropIndex;
                            card.y = 0;
                            root.draggedIndex = -1;
                            root.dropIndex = -1;
                            if (destination >= 0 && destination !== fieldRow.index)
                                editor.moveField(fieldRow.index, destination);
                        }
                        onCanceled: {
                            card.y = 0;
                            root.draggedIndex = -1;
                            root.dropIndex = -1;
                        }
                    }
                }
            }
        }
    }
}
