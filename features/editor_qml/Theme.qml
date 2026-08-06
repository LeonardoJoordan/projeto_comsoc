pragma Singleton

import QtQuick

QtObject {
    readonly property color window: "#0F1014"
    readonly property color chrome: "#15161B"
    readonly property color panel: "#1A1B21"
    readonly property color panelRaised: "#22232B"
    readonly property color panelHover: "#2A2C35"
    readonly property color field: "#121318"
    readonly property color canvas: "#26272C"
    readonly property color canvasDeep: "#202126"

    readonly property color border: "#30323B"
    readonly property color borderStrong: "#454854"
    readonly property color divider: "#292A31"

    readonly property color text: "#F3F5F8"
    readonly property color textMuted: "#A8ABB5"
    readonly property color textSubtle: "#777B87"
    readonly property color textDisabled: "#555965"

    readonly property color accent: "#7C73F2"
    readonly property color accentHover: "#9087FF"
    readonly property color accentSoft: "#343159"
    readonly property color accentFaint: "#27253E"
    readonly property color guide: "#3AC6DD"

    readonly property color success: "#54C58A"
    readonly property color warning: "#EAB45E"
    readonly property color danger: "#EF737B"

    readonly property int radiusSmall: 6
    readonly property int radius: 9
    readonly property int radiusLarge: 13

    readonly property int space1: 4
    readonly property int space2: 8
    readonly property int space3: 12
    readonly property int space4: 16
    readonly property int space5: 20
    readonly property int space6: 24

    readonly property int controlHeight: 36
    readonly property int toolbarHeight: 48
    readonly property int headerHeight: 64
}
