pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property string selectionKind: "text"
    property string selectionIndex: ""
    property string selectionName: "Nome completo"
    readonly property bool linkAvailable: isText || selectionKind === "image" || isShape

    function collapseSections() {
        propertiesSection.expanded = false;
        textSection.expanded = false;
    }
    onSelectionIndexChanged: collapseSections()
    onSelectionKindChanged: collapseSections()
    readonly property bool isText: selectionKind === "text"
    readonly property bool isShape: selectionKind === "shape"

    color: Theme.panel
    border.width: 1
    border.color: Theme.divider

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            color: Theme.panel

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                anchors.topMargin: 8
                anchors.bottomMargin: 8
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: root.selectionName
                    color: Theme.textMuted
                    font.pixelSize: 11
                    elide: Text.ElideRight
                }
                Text {
                    text: !root.selectionKind ? "Selecione uma camada" : (root.isText ? "Texto" : (root.isShape ? "Forma" : (root.selectionKind === "signature" ? "Assinatura" : "Imagem")))
                    color: Theme.textSubtle
                    font.pixelSize: 9
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
                spacing: 0

                PanelSection {
                    id: propertiesSection
                    objectName: "propertiesSection"
                    width: parent.width
                    title: "Propriedades"
                    expanded: false
                    available: !!editor.uiState.selected.key
                    collapsible: true
                    topPadding: 0
                    bottomPadding: expanded ? 14 : 0

                    PanelSection {
                        Layout.fillWidth: true
                        topPadding: 0
                        bottomPadding: 4
                        title: "Comportamento"
                        horizontalPadding: 0

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            enabled: root.linkAvailable
                            opacity: enabled ? 1 : 0.4

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

                            CompactSwitch {
                                Layout.preferredWidth: 42
                                Layout.preferredHeight: 24
                                checked: editor.uiState.selected.has_link || false
                                enabled: !editor.uiState.selected.locked
                                onClicked: editor.setValue("has_link", checked)
                            }
                        }

                    }
                    PropertyField {
                        Layout.fillWidth: true
                        visible: root.linkAvailable && !!editor.uiState.selected.has_link
                        label: "Coluna do link"
                        value: editor.uiState.selected.link_key || ""
                        enabledField: !editor.uiState.selected.locked
                        onEdited: value => editor.setValue("link_key", value)
                    }
                    Button {
                        Layout.fillWidth: true
                        visible: root.selectionKind === "image" || root.selectionKind === "signature"
                        enabled: !editor.uiState.selected.locked
                        text: "Substituir imagem…"
                        onClicked: editor.replaceAsset()
                    }
                    ColumnLayout {
                        visible: root.isShape
                        enabled: !editor.uiState.selected.locked
                        Layout.fillWidth: true
                        spacing: 8
                        Text {
                            text: "Forma"
                            color: Theme.textMuted
                            font.pixelSize: 11
                        }
                        ComboBox {
                            id: shapeSelector
                            objectName: "shapeSelector"
                            Layout.fillWidth: true
                            model: ["Retângulo", "Quadrado", "Elipse", "Círculo"]
                            currentIndex: ["rectangle", "square", "ellipse", "circle"].indexOf(editor.uiState.selected.shape_type || "rectangle")
                            onActivated: editor.setValue("shape_type", ["rectangle", "square", "ellipse", "circle"][currentIndex])
                            Accessible.name: "Forma básica"
                            contentItem: Text {
                                text: shapeSelector.displayText
                                color: Theme.text
                                font.pixelSize: 12
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 10
                            }
                            background: Rectangle {
                                implicitHeight: 34
                                radius: Theme.radiusSmall
                                color: Theme.field
                                border.color: shapeSelector.activeFocus ? Theme.accent : Theme.border
                            }
                        }
                        ColorField {
                            label: "Preenchimento"
                            externallyManaged: true
                            value: editor.uiState.selected.fill_color || "#FFFFFF"
                            onEdited: value => editor.setValue("fill_color", value)
                        }
                    }

                    ColumnLayout {
                        visible: root.isText || root.isShape
                        enabled: !editor.uiState.selected.locked
                        opacity: enabled ? 1 : 0.4
                        Layout.fillWidth: true
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: "Contorno"
                                color: Theme.text
                                font.pixelSize: 11
                                font.weight: Font.Medium
                            }
                            CompactSwitch {
                                id: outlineSwitch
                                objectName: "outlineSwitch"
                                ToolTip.visible: hovered
                                ToolTip.text: "Aplicar contorno ao texto ou à forma"
                                checked: editor.uiState.selected.outline_enabled || false
                                onClicked: editor.setValue("outline_enabled", checked)
                                Accessible.name: "Contorno"
                                Layout.preferredWidth: 42
                                Layout.preferredHeight: 24
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            ColorField {
                                label: "Cor do contorno"
                                externallyManaged: true
                                value: editor.uiState.selected.outline_color || "#000000"
                                onEdited: value => editor.setValue("outline_color", value)
                                enabledField: outlineSwitch.checked
                            }
                            PropertyField {
                                label: "Espessura"
                                value: String(editor.uiState.selected.outline_width || 1)
                                onEdited: value => editor.setValue("outline_width", value)
                                suffix: "px"
                                enabledField: outlineSwitch.checked
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
                    id: textSection
                    objectName: "textSection"
                    width: parent.width
                    title: "Texto"
                    iconName: "text"
                    expanded: false
                    available: root.isText
                    unavailableReason: "Selecione uma camada de texto"
                    collapsible: true
                    bottomPadding: expanded ? 14 : 0
                    TypographyControls { Layout.fillWidth: true }
                }

                PanelSection {
                    width: parent.width
                    objectName: "tableFieldsSection"
                    title: "Campos da tabela"
                    caption: "Ordem na tabela"
                    iconName: "grid"
                    expanded: false
                    collapsible: true
                    bottomPadding: expanded ? 14 : 0
                    TableFieldOrder { Layout.fillWidth: true }
                }
            }
        }
    }
}
