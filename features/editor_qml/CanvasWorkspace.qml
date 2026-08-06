pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root

    property real zoomValue: 82
    property bool showGrid: false
    property bool showGuides: true

    signal zoomRequested(real value)

    clip: true

    Rectangle {
        anchors.fill: parent
        color: Theme.canvasDeep
    }

    // A faint technical grid gives the pasteboard depth without competing with the page.
    Canvas {
        anchors.fill: parent
        opacity: root.showGrid ? 0.45 : 0.13

        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            ctx.strokeStyle = "#4A4C54";
            ctx.lineWidth = 1;
            const step = root.showGrid ? 24 : 48;
            for (let x = 0.5; x < width; x += step) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
            }
            for (let y = 0.5; y < height; y += step) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }
        }
    }

    Item {
        id: viewport
        anchors.fill: parent
        anchors.leftMargin: 24
        anchors.topMargin: 24
        clip: true

        Rectangle {
            id: pageShadow
            width: page.width + 18
            height: page.height + 18
            anchors.centerIn: parent
            x: page.x + 9
            y: page.y + 11
            radius: 4
            color: "#12000000"
            border.width: 10
            border.color: "#10000000"
        }

        Rectangle {
            id: page
            width: 760
            height: 538
            anchors.centerIn: parent
            color: "#F8F6F1"
            border.width: 1
            border.color: "#D0CDC5"
            transformOrigin: Item.Center
            scale: Math.min(1.0, Math.max(0.62, Math.min((viewport.width - 120) / width, (viewport.height - 90) / height)))

            Rectangle {
                anchors.fill: parent
                anchors.margins: 34
                color: "transparent"
                border.width: 1
                border.color: "#D7D0C2"

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 5
                    color: "transparent"
                    border.width: 1
                    border.color: "#E5DFD4"
                }
            }

            // Restrained editorial decoration: intentionally code-native and replaceable.
            Rectangle {
                width: 154
                height: 6
                x: 303
                y: 78
                radius: 3
                color: "#766BDD"
            }

            Rectangle {
                width: 46
                height: 46
                x: 357
                y: 99
                radius: 23
                color: "#EEEAFB"
                border.width: 1
                border.color: "#CFC8F1"

                Text {
                    anchors.centerIn: parent
                    text: "C"
                    color: "#655BBE"
                    font.pixelSize: 22
                    font.weight: Font.DemiBold
                    font.letterSpacing: 1
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 159
                text: "CERTIFICADO"
                color: "#292833"
                font.pixelSize: 28
                font.weight: Font.Light
                font.letterSpacing: 5
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 198
                text: "DE CONCLUSÃO"
                color: "#817C76"
                font.pixelSize: 10
                font.weight: Font.DemiBold
                font.letterSpacing: 3
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 237
                text: "Certificamos que"
                color: "#77716C"
                font.pixelSize: 13
                font.italic: true
            }

            Item {
                id: selectedObject
                width: 408
                height: 58
                anchors.horizontalCenter: parent.horizontalCenter
                y: 265

                Rectangle {
                    anchors.fill: parent
                    color: "#0D766BDD"
                    border.width: 1
                    border.color: "#766BDD"
                }

                Text {
                    anchors.centerIn: parent
                    text: "{Nome completo}"
                    color: "#26232E"
                    font.family: "DejaVu Serif"
                    font.pixelSize: 31
                    font.weight: Font.Medium
                }

                Repeater {
                    model: [[-4, -4], [selectedObject.width / 2 - 4, -4], [selectedObject.width - 4, -4], [-4, selectedObject.height / 2 - 4], [selectedObject.width - 4, selectedObject.height / 2 - 4], [-4, selectedObject.height - 4], [selectedObject.width / 2 - 4, selectedObject.height - 4], [selectedObject.width - 4, selectedObject.height - 4]]

                    delegate: Rectangle {
                        required property var modelData

                        x: modelData[0]
                        y: modelData[1]
                        width: 8
                        height: 8
                        radius: 2
                        color: "#FFFFFF"
                        border.width: 1
                        border.color: "#766BDD"
                    }
                }

                Rectangle {
                    width: 1
                    height: 20
                    x: parent.width / 2
                    y: -20
                    color: "#766BDD"
                }

                Rectangle {
                    width: 10
                    height: 10
                    radius: 5
                    x: parent.width / 2 - 4.5
                    y: -29
                    color: "#FFFFFF"
                    border.width: 1
                    border.color: "#766BDD"
                }

                Rectangle {
                    x: 12
                    y: -24
                    height: 18
                    width: variableTag.implicitWidth + 16
                    radius: 4
                    color: "#766BDD"

                    Text {
                        id: variableTag
                        anchors.centerIn: parent
                        text: "TEXTO VARIÁVEL"
                        color: "#FFFFFF"
                        font.pixelSize: 8
                        font.weight: Font.Bold
                        font.letterSpacing: 0.6
                    }
                }
            }

            Rectangle {
                width: 316
                height: 1
                anchors.horizontalCenter: parent.horizontalCenter
                y: 333
                color: "#D0C9BD"
            }

            Text {
                width: 540
                anchors.horizontalCenter: parent.horizontalCenter
                y: 355
                text: "concluiu com êxito o curso de Design Editorial, realizado em agosto de 2026, com carga horária total de 24 horas."
                color: "#625E5A"
                font.pixelSize: 12
                lineHeight: 1.35
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }

            Item {
                x: 131
                y: 445
                width: 180
                height: 42

                Rectangle {
                    width: parent.width
                    height: 1
                    color: "#A8A198"
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 10
                    text: "Marina Costa"
                    color: "#3D3A38"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 26
                    text: "Coordenação"
                    color: "#8D8780"
                    font.pixelSize: 9
                }
            }

            Item {
                x: 449
                y: 445
                width: 180
                height: 42

                Rectangle {
                    width: parent.width
                    height: 1
                    color: "#A8A198"
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 10
                    text: "{Data de emissão}"
                    color: "#3D3A38"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 26
                    text: "Emissão"
                    color: "#8D8780"
                    font.pixelSize: 9
                }
            }

            Text {
                x: 55
                y: 495
                text: "COMSOC  •  DOCUMENTO 01"
                color: "#A5A09A"
                font.pixelSize: 8
                font.letterSpacing: 1
            }
        }

        // Smart guides are deliberately vivid and distinct from selection blue.
        Rectangle {
            visible: root.showGuides
            width: 1
            height: Math.min(viewport.height - 40, page.height * page.scale + 40)
            anchors.horizontalCenter: page.horizontalCenter
            anchors.verticalCenter: page.verticalCenter
            color: Theme.guide
            opacity: 0.72
        }

        Rectangle {
            visible: root.showGuides
            width: Math.min(viewport.width - 50, page.width * page.scale + 50)
            height: 1
            anchors.horizontalCenter: page.horizontalCenter
            y: page.y + (296 * page.scale)
            color: Theme.guide
            opacity: 0.58
        }
    }

    // Horizontal ruler.
    Rectangle {
        x: 24
        y: 0
        width: parent.width - 24
        height: 24
        color: "#F015161B"
        border.color: Theme.divider

        Repeater {
            model: Math.ceil(parent.width / 80)

            delegate: Item {
                id: horizontalMark

                required property int index

                x: horizontalMark.index * 80
                width: 80
                height: 24

                Text {
                    x: 4
                    y: 3
                    text: horizontalMark.index * 100
                    color: Theme.textDisabled
                    font.pixelSize: 8
                }

                Rectangle {
                    width: 1
                    height: 7
                    anchors.bottom: parent.bottom
                    color: Theme.borderStrong
                }

                Rectangle {
                    width: 1
                    height: 4
                    x: 40
                    anchors.bottom: parent.bottom
                    color: Theme.border
                }
            }
        }
    }

    // Vertical ruler.
    Rectangle {
        x: 0
        y: 24
        width: 24
        height: parent.height - 24
        color: "#F015161B"
        border.color: Theme.divider

        Repeater {
            model: Math.ceil(parent.height / 80)

            delegate: Item {
                id: verticalMark

                required property int index

                y: verticalMark.index * 80
                width: 24
                height: 80

                Text {
                    x: 4
                    y: 5
                    text: verticalMark.index * 100
                    color: Theme.textDisabled
                    font.pixelSize: 8
                    rotation: -90
                    transformOrigin: Item.TopLeft
                }

                Rectangle {
                    width: 7
                    height: 1
                    anchors.right: parent.right
                    color: Theme.borderStrong
                }

                Rectangle {
                    width: 4
                    height: 1
                    y: 40
                    anchors.right: parent.right
                    color: Theme.border
                }
            }
        }
    }

    Rectangle {
        width: 24
        height: 24
        color: Theme.chrome
        border.color: Theme.divider

        EditorIcon {
            anchors.centerIn: parent
            name: "frame"
            color: Theme.textDisabled
            implicitWidth: 12
            implicitHeight: 12
        }
    }
}
