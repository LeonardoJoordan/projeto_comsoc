pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property int selectedLayer: 0
    property bool guidesVisible: true
    property bool guidesLocked: false

    signal guidesVisibilityRequested(bool visible)
    signal guidesLockRequested(bool locked)

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
            columns: 2
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
                        icon: "image",
                        title: "Imagem",
                        detail: "Foto, logo ou QR"
                    },
                    {
                        icon: "signature",
                        title: "Assinatura",
                        detail: "Imagem opcional"
                    },
                    {
                        icon: "image",
                        title: "Fundo",
                        detail: "Base do documento"
                    }
                ]

                delegate: ToolButton {
                    id: addButton

                    required property var modelData

                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    hoverEnabled: true

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
            Layout.preferredHeight: 82
            color: Theme.panel

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 10
                anchors.topMargin: 8
                anchors.bottomMargin: 8
                spacing: 7

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        Layout.fillWidth: true
                        text: "GUIAS"
                        color: Theme.textMuted
                        font.pixelSize: 9
                        font.weight: Font.Bold
                        font.letterSpacing: 0.7
                    }

                    ToolButton {
                        id: guideEyeButton
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 26
                        checkable: true
                        checked: root.guidesVisible
                        hoverEnabled: true
                        onClicked: root.guidesVisibilityRequested(checked)
                        ToolTip.visible: hovered
                        ToolTip.text: checked ? "Ocultar guias" : "Mostrar guias"

                        contentItem: EditorIcon {
                            anchors.centerIn: parent
                            width: 13
                            height: 13
                            name: "eye"
                            color: guideEyeButton.checked ? Theme.guide : Theme.textDisabled
                        }

                        background: Rectangle {
                            radius: 5
                            color: guideEyeButton.hovered ? Theme.panelHover : "transparent"
                        }
                    }

                    ToolButton {
                        id: guideLockButton
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 26
                        checkable: true
                        checked: root.guidesLocked
                        hoverEnabled: true
                        onClicked: root.guidesLockRequested(checked)
                        ToolTip.visible: hovered
                        ToolTip.text: checked ? "Desbloquear guias" : "Bloquear guias"

                        contentItem: EditorIcon {
                            anchors.centerIn: parent
                            width: 13
                            height: 13
                            name: "lock"
                            color: guideLockButton.checked ? Theme.warning : Theme.textDisabled
                        }

                        background: Rectangle {
                            radius: 5
                            color: guideLockButton.hovered ? Theme.panelHover : "transparent"
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 7

                    UiButton {
                        Layout.fillWidth: true
                        text: "Guia vertical"
                        compact: true
                    }

                    UiButton {
                        Layout.fillWidth: true
                        text: "Guia horizontal"
                        compact: true
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.borderStrong
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
                    model: [
                        {
                            kind: "T",
                            title: "Nome completo",
                            detail: "Texto variável",
                            locked: false
                        },
                        {
                            kind: "T",
                            title: "Descrição do curso",
                            detail: "Texto",
                            locked: false
                        },
                        {
                            kind: "T",
                            title: "Certificado",
                            detail: "Texto",
                            locked: true
                        },
                        {
                            kind: "✍",
                            title: "Assinatura da coordenação",
                            detail: "Assinatura",
                            locked: false
                        },
                        {
                            kind: "▧",
                            title: "Fundo do certificado",
                            detail: "Imagem de fundo",
                            locked: true
                        }
                    ]

                    delegate: LayerRow {
                        required property int index
                        required property var modelData

                        width: parent.width - 16
                        kind: modelData.kind
                        title: modelData.title
                        detail: modelData.detail
                        locked: modelData.locked
                        selected: root.selectedLayer === index
                        onActivated: root.selectedLayer = index
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
                    text: "5 elementos"
                    color: Theme.textSubtle
                    font.pixelSize: 9
                }

                Text {
                    text: "Arraste para reordenar"
                    color: Theme.textDisabled
                    font.pixelSize: 8
                }
            }
        }
    }
}
