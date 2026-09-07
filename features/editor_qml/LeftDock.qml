pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property int selectedLayer: 0
    signal layerSelected(int layerIndex, string kind, string title, string content)

    color: Theme.panel
    border.width: 1
    border.color: Theme.divider

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            color: Theme.chrome

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8

                Text {
                    Layout.fillWidth: true
                    text: "ADICIONAR AO MODELO"
                    color: Theme.text
                    font.pixelSize: 10
                    font.weight: Font.Bold
                    font.letterSpacing: 0.8
                }

                Text {
                    text: "Arraste para ajustar"
                    color: Theme.textDisabled
                    font.pixelSize: 8
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.topMargin: 10
            Layout.bottomMargin: 10
            columns: 1
            columnSpacing: 7
            rowSpacing: 7

            Repeater {
                model: [
                    {
                        icon: "text",
                        title: "Texto",
                        detail: "Campo dinâmico"
                    },
                    {
                        icon: "shape",
                        title: "Formas",
                        detail: "Preenchimento e borda"
                    },
                    {
                        icon: "image",
                        title: "Imagens",
                        detail: "Foto, logo ou QR"
                    },
                    {
                        icon: "signature",
                        title: "Assinatura",
                        detail: "Imagem opcional"
                    }
                ]

                delegate: ToolButton {
                    id: addButton

                    required property var modelData

                    Layout.fillWidth: true
                    Layout.preferredHeight: 43.5
                    enabled: modelData.icon !== "shape"
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.text: modelData.icon === "shape" ? "Formas: integração pendente" : modelData.title
                    onClicked: editor.addItem(modelData.icon === "signature" ? "signature" : modelData.icon)

                    contentItem: RowLayout {
                        spacing: 8

                        Rectangle {
                            Layout.preferredWidth: 30
                            Layout.preferredHeight: 30
                            radius: 7
                            color: addButton.hovered ? Theme.accentSoft : Theme.field
                            border.width: 1
                            border.color: addButton.hovered ? Theme.accent : Theme.border

                            EditorIcon {
                                anchors.centerIn: parent
                                width: 16
                                height: 16
                                name: addButton.modelData.icon
                                color: addButton.hovered ? Theme.accentHover : Theme.textMuted
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1

                            Text {
                                Layout.fillWidth: true
                                text: addButton.modelData.title
                                color: Theme.text
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.fillWidth: true
                                text: addButton.modelData.detail
                                color: Theme.textSubtle
                                font.pixelSize: 8
                                elide: Text.ElideRight
                            }
                        }
                    }

                    background: Rectangle {
                        radius: 8
                        color: addButton.down ? Theme.accentFaint : (addButton.hovered ? Theme.panelHover : Theme.panelRaised)
                        border.width: 1
                        border.color: addButton.hovered ? Theme.borderStrong : Theme.border
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.divider
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            color: Theme.chrome

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 7
                spacing: 3

                EditorIcon {
                    Layout.preferredWidth: 15
                    Layout.preferredHeight: 15
                    name: "layers"
                    color: Theme.textMuted
                }

                Text {
                    Layout.fillWidth: true
                    text: "CAMADAS"
                    color: Theme.text
                    font.pixelSize: 10
                    font.weight: Font.Bold
                    font.letterSpacing: 0.8
                }

                Repeater {
                    model: [
                        {
                            label: "✎",
                            tip: "Renomear camada"
                        },
                        {
                            label: "⧉",
                            tip: "Duplicar camada"
                        },
                        {
                            label: "⌫",
                            tip: "Excluir camada"
                        }
                    ]

                    delegate: ToolButton {
                        id: layerAction
                        onClicked: {
                            if (modelData.tip === "Renomear camada") editor.renameSelected();
                            else if (modelData.tip === "Duplicar camada") editor.duplicateSelected();
                            else editor.deleteSelected();
                        }

                        required property var modelData

                        Layout.preferredWidth: 28
                        Layout.preferredHeight: 28
                        hoverEnabled: true
                        ToolTip.visible: hovered
                        ToolTip.text: modelData.tip

                        contentItem: Text {
                            text: layerAction.modelData.label
                            color: layerAction.hovered ? Theme.text : Theme.textMuted
                            font.pixelSize: 14
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }

                        background: Rectangle {
                            radius: 5
                            color: layerAction.hovered ? Theme.panelHover : "transparent"
                        }
                    }
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            Column {
                width: root.width
                topPadding: 7
                leftPadding: 8
                rightPadding: 8
                spacing: 3

                Repeater {
                    model: editor.state.layers

                    delegate: LayerRow {
                        required property int index
                        required property var modelData

                        width: parent.width - 16
                        kind: modelData.kind
                        title: modelData.title
                        detail: modelData.detail
                        locked: modelData.locked
                        visibleLayer: modelData.visible
                        selected: editor.state.selected.key === modelData.key
                        onVisibilityRequested: { editor.select(modelData.key); editor.setValue("visible", !modelData.visible); }
                        onLockRequested: { editor.select(modelData.key); editor.setValue("locked", !modelData.locked); }
                        onActivated: editor.select(modelData.key)
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 28
            color: Theme.chrome

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 10

                Text {
                    Layout.fillWidth: true
                    text: editor.state.layers.length + " elementos"
                    color: Theme.textSubtle
                    font.pixelSize: 9
                }

                Text {
                    text: "Ordem de renderização"
                    color: Theme.textDisabled
                    font.pixelSize: 8
                }
            }
        }
    }
}
