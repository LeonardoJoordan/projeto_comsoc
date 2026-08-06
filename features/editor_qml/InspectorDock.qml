pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    color: Theme.panel
    border.width: 1
    border.color: Theme.divider

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            color: Theme.chrome

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8

                EditorIcon {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    name: "sliders"
                    color: Theme.accentHover
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Text {
                        text: "PROPRIEDADES"
                        color: Theme.text
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        font.letterSpacing: 0.9
                    }

                    Text {
                        text: "Texto selecionado"
                        color: Theme.textSubtle
                        font.pixelSize: 9
                    }
                }

                ToolButton {
                    id: collapseButton
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.text: "Recolher propriedades"

                    contentItem: Text {
                        text: "»"
                        color: collapseButton.hovered ? Theme.text : Theme.textMuted
                        font.pixelSize: 15
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 5
                        color: collapseButton.hovered ? Theme.panelHover : "transparent"
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.borderStrong
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            Column {
                width: root.width
                spacing: 0

                Rectangle {
                    width: parent.width
                    height: 67
                    color: Theme.panelRaised

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 10

                        Rectangle {
                            Layout.preferredWidth: 36
                            Layout.preferredHeight: 36
                            radius: 8
                            color: Theme.accentSoft

                            Text {
                                anchors.centerIn: parent
                                text: "T"
                                color: Theme.accentHover
                                font.pixelSize: 16
                                font.weight: Font.Bold
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                Layout.fillWidth: true
                                text: "Nome completo"
                                color: Theme.text
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "Caixa de texto dinâmica"
                                color: Theme.textSubtle
                                font.pixelSize: 9
                                elide: Text.ElideRight
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: 64
                            Layout.preferredHeight: 22
                            radius: 11
                            color: "#273D35"
                            border.width: 1
                            border.color: "#365E4D"

                            Text {
                                anchors.centerIn: parent
                                text: "VARIÁVEL"
                                color: Theme.success
                                font.pixelSize: 8
                                font.weight: Font.Bold
                            }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    height: 1
                    color: Theme.divider
                }

                PanelSection {
                    width: parent.width
                    topPadding: 14
                    bottomPadding: 14
                    title: "Conteúdo"
                    caption: "Campo dinâmico"

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 70
                        radius: 7
                        color: Theme.field
                        border.width: 1
                        border.color: Theme.border

                        TextEdit {
                            anchors.fill: parent
                            anchors.margins: 10
                            text: "{Nome completo}"
                            color: Theme.text
                            font.pixelSize: 12
                            selectByMouse: true
                            wrapMode: TextEdit.Wrap
                            selectionColor: Theme.accentSoft
                            selectedTextColor: Theme.text
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 7

                        UiButton {
                            Layout.fillWidth: true
                            text: "Inserir variável"
                            compact: true
                        }

                        UiButton {
                            Layout.fillWidth: true
                            text: "Trecho opcional"
                            compact: true
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    height: 1
                    color: Theme.divider
                }

                PanelSection {
                    width: parent.width
                    topPadding: 14
                    bottomPadding: 14
                    title: "Tipografia"
                    caption: "Aplicada à seleção"

                    PropertyField {
                        Layout.fillWidth: true
                        label: "Fonte"
                        value: "DejaVu Serif"
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 8
                        rowSpacing: 8

                        PropertyField {
                            Layout.fillWidth: true
                            label: "Peso"
                            value: "Medium"
                        }

                        PropertyField {
                            Layout.fillWidth: true
                            label: "Tamanho"
                            value: "31 px"
                        }

                        PropertyField {
                            Layout.fillWidth: true
                            label: "Entrelinha"
                            value: "Automática"
                        }

                        PropertyField {
                            Layout.fillWidth: true
                            label: "Recuo"
                            value: "0 px"
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 5

                        Repeater {
                            model: [
                                {
                                    label: "B",
                                    tip: "Negrito"
                                },
                                {
                                    label: "I",
                                    tip: "Itálico"
                                },
                                {
                                    label: "U",
                                    tip: "Sublinhado"
                                }
                            ]

                            delegate: ToolButton {
                                id: styleButton

                                required property var modelData

                                Layout.preferredWidth: 34
                                Layout.preferredHeight: 31
                                checkable: true
                                hoverEnabled: true
                                ToolTip.visible: hovered
                                ToolTip.text: modelData.tip

                                contentItem: Text {
                                    text: styleButton.modelData.label
                                    color: styleButton.checked ? Theme.accentHover : Theme.textMuted
                                    font.pixelSize: 12
                                    font.bold: styleButton.modelData.label === "B"
                                    font.italic: styleButton.modelData.label === "I"
                                    font.underline: styleButton.modelData.label === "U"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                background: Rectangle {
                                    radius: 5
                                    color: styleButton.checked ? Theme.accentSoft : (styleButton.hovered ? Theme.panelHover : Theme.field)
                                    border.width: 1
                                    border.color: styleButton.checked ? Theme.accent : Theme.border
                                }
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: 1
                            Layout.preferredHeight: 22
                            Layout.leftMargin: 2
                            Layout.rightMargin: 2
                            color: Theme.divider
                        }

                        Repeater {
                            model: [
                                {
                                    label: "≡",
                                    tip: "Alinhar texto à esquerda"
                                },
                                {
                                    label: "≣",
                                    tip: "Centralizar texto"
                                },
                                {
                                    label: "≡",
                                    tip: "Alinhar texto à direita",
                                    mirror: true
                                },
                                {
                                    label: "☷",
                                    tip: "Justificar texto"
                                }
                            ]

                            delegate: ToolButton {
                                id: textAlignButton

                                required property int index
                                required property var modelData

                                Layout.fillWidth: true
                                Layout.preferredHeight: 31
                                checkable: true
                                checked: index === 1
                                hoverEnabled: true
                                ToolTip.visible: hovered
                                ToolTip.text: modelData.tip

                                contentItem: Text {
                                    text: textAlignButton.modelData.label
                                    color: textAlignButton.checked ? Theme.accentHover : Theme.textMuted
                                    font.pixelSize: 13
                                    horizontalAlignment: textAlignButton.modelData.mirror ? Text.AlignRight : (textAlignButton.index === 1 ? Text.AlignHCenter : Text.AlignLeft)
                                    verticalAlignment: Text.AlignVCenter
                                }

                                background: Rectangle {
                                    radius: 5
                                    color: textAlignButton.checked ? Theme.accentSoft : (textAlignButton.hovered ? Theme.panelHover : Theme.field)
                                    border.width: 1
                                    border.color: textAlignButton.checked ? Theme.accent : Theme.border
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        PropertyField {
                            Layout.fillWidth: true
                            label: "Alinhamento vertical"
                            value: "Meio"
                        }

                        Rectangle {
                            Layout.preferredWidth: 36
                            Layout.preferredHeight: 34
                            Layout.alignment: Qt.AlignBottom
                            radius: 6
                            color: "#26232E"
                            border.width: 1
                            border.color: Theme.borderStrong
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    height: 1
                    color: Theme.divider
                }

                PanelSection {
                    width: parent.width
                    topPadding: 14
                    bottomPadding: 14
                    title: "Comportamento"

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                text: "Link no PDF"
                                color: Theme.text
                                font.pixelSize: 11
                                font.weight: Font.Medium
                            }

                            Text {
                                text: "Usar valor informado na tabela"
                                color: Theme.textSubtle
                                font.pixelSize: 9
                            }
                        }

                        Switch {
                            Layout.preferredWidth: 42
                            Layout.preferredHeight: 24
                            checked: false
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                text: "Manter proporção"
                                color: Theme.text
                                font.pixelSize: 11
                                font.weight: Font.Medium
                            }

                            Text {
                                text: "Preservar largura e altura ao redimensionar"
                                color: Theme.textSubtle
                                font.pixelSize: 9
                            }
                        }

                        Switch {
                            Layout.preferredWidth: 42
                            Layout.preferredHeight: 24
                            checked: true
                        }
                    }
                }
            }
        }
    }
}
