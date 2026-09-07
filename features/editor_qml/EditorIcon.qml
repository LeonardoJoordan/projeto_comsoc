import QtQuick

Item {
    id: root

    property string name: "select"
    property color color: Theme.textMuted
    property real strokeWidth: 1.65

    implicitWidth: 20
    implicitHeight: 20

    onNameChanged: canvas.requestPaint()
    onColorChanged: canvas.requestPaint()
    onStrokeWidthChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent

        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            const ctx = getContext("2d");
            const w = width;
            const h = height;
            const c = root.color;
            ctx.clearRect(0, 0, w, h);
            ctx.strokeStyle = c;
            ctx.fillStyle = c;
            ctx.lineWidth = root.strokeWidth;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";

            function line(x1, y1, x2, y2) {
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
            }

            function rect(x, y, rw, rh) {
                ctx.strokeRect(x, y, rw, rh);
            }

            function circle(x, y, r) {
                ctx.beginPath();
                ctx.arc(x, y, r, 0, Math.PI * 2);
                ctx.stroke();
            }

            if (root.name.indexOf("align-") === 0) {
                const alignment = Number(root.name.slice(6));
                for (let i = 0; i < 4; i++) {
                    const length = alignment === 3 || i % 2 === 0 ? 0.72 : 0.45;
                    const left = alignment === 2 ? 0.86 - length : (alignment === 1 ? (1 - length) / 2 : 0.14);
                    line(w * left, h * (0.2 + i * 0.2), w * (left + length), h * (0.2 + i * 0.2));
                }
            } else if (root.name.indexOf("valign-") === 0) {
                const alignment = Number(root.name.slice(7));
                const top = [0.26, 0.38, 0.5][alignment];
                line(w * 0.12, h * 0.12, w * 0.88, h * 0.12);
                line(w * 0.12, h * 0.88, w * 0.88, h * 0.88);
                for (let i = 0; i < 3; i++)
                    line(w * 0.26, h * (top + i * 0.12), w * (i === 1 ? 0.62 : 0.74), h * (top + i * 0.12));
            } else if (root.name === "select") {
                ctx.beginPath();
                ctx.moveTo(w * 0.24, h * 0.16);
                ctx.lineTo(w * 0.72, h * 0.55);
                ctx.lineTo(w * 0.49, h * 0.59);
                ctx.lineTo(w * 0.65, h * 0.86);
                ctx.lineTo(w * 0.54, h * 0.92);
                ctx.lineTo(w * 0.39, h * 0.65);
                ctx.lineTo(w * 0.24, h * 0.82);
                ctx.closePath();
                ctx.stroke();
            } else if (root.name === "node") {
                line(w * 0.2, h * 0.72, w * 0.48, h * 0.28);
                line(w * 0.48, h * 0.28, w * 0.8, h * 0.66);
                rect(w * 0.13, h * 0.65, w * 0.14, h * 0.14);
                rect(w * 0.41, h * 0.21, w * 0.14, h * 0.14);
                rect(w * 0.73, h * 0.59, w * 0.14, h * 0.14);
            } else if (root.name === "frame") {
                rect(w * 0.18, h * 0.19, w * 0.64, h * 0.62);
                line(w * 0.18, h * 0.35, w * 0.82, h * 0.35);
                line(w * 0.34, h * 0.19, w * 0.34, h * 0.81);
            } else if (root.name === "text") {
                ctx.font = "600 " + Math.round(h * 0.72) + "px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText("T", w / 2, h / 2 + 1);
            } else if (root.name === "image") {
                rect(w * 0.16, h * 0.2, w * 0.68, h * 0.6);
                circle(w * 0.65, h * 0.36, w * 0.07);
                ctx.beginPath();
                ctx.moveTo(w * 0.2, h * 0.7);
                ctx.lineTo(w * 0.4, h * 0.49);
                ctx.lineTo(w * 0.53, h * 0.62);
                ctx.lineTo(w * 0.64, h * 0.51);
                ctx.lineTo(w * 0.8, h * 0.7);
                ctx.stroke();
            } else if (root.name === "shape") {
                rect(w * 0.14, h * 0.24, w * 0.43, h * 0.53);
                circle(w * 0.66, h * 0.43, w * 0.2);
            } else if (root.name === "pen") {
                ctx.beginPath();
                ctx.moveTo(w * 0.5, h * 0.12);
                ctx.lineTo(w * 0.78, h * 0.44);
                ctx.lineTo(w * 0.54, h * 0.86);
                ctx.lineTo(w * 0.24, h * 0.56);
                ctx.closePath();
                ctx.stroke();
                circle(w * 0.5, h * 0.51, w * 0.07);
                line(w * 0.5, h * 0.58, w * 0.5, h * 0.84);
            } else if (root.name === "signature") {
                ctx.beginPath();
                ctx.moveTo(w * 0.12, h * 0.68);
                ctx.bezierCurveTo(w * 0.28, h * 0.2, w * 0.34, h * 0.82, w * 0.47, h * 0.43);
                ctx.bezierCurveTo(w * 0.56, h * 0.22, w * 0.53, h * 0.78, w * 0.68, h * 0.5);
                ctx.bezierCurveTo(w * 0.76, h * 0.37, w * 0.75, h * 0.7, w * 0.9, h * 0.54);
                ctx.stroke();
                line(w * 0.13, h * 0.8, w * 0.88, h * 0.8);
            } else if (root.name === "guide-horizontal" || root.name === "guide-vertical") {
                ctx.setLineDash([2, 2]);
                if (root.name === "guide-horizontal")
                    line(w * 0.12, h * 0.65, w * 0.88, h * 0.65);
                else
                    line(w * 0.35, h * 0.12, w * 0.35, h * 0.88);
                ctx.setLineDash([]);
                line(w * 0.65, h * 0.15, w * 0.65, h * 0.4);
                line(w * 0.52, h * 0.275, w * 0.78, h * 0.275);
            } else if (root.name === "guide") {
                ctx.setLineDash([3, 3]);
                line(w * 0.5, h * 0.08, w * 0.5, h * 0.92);
                line(w * 0.08, h * 0.5, w * 0.92, h * 0.5);
                ctx.setLineDash([]);
            } else if (root.name === "hand") {
                ctx.beginPath();
                ctx.moveTo(w * 0.28, h * 0.52);
                ctx.lineTo(w * 0.28, h * 0.31);
                ctx.quadraticCurveTo(w * 0.28, h * 0.22, w * 0.35, h * 0.22);
                ctx.quadraticCurveTo(w * 0.42, h * 0.22, w * 0.42, h * 0.31);
                ctx.lineTo(w * 0.42, h * 0.18);
                ctx.quadraticCurveTo(w * 0.42, h * 0.1, w * 0.5, h * 0.1);
                ctx.quadraticCurveTo(w * 0.57, h * 0.1, w * 0.57, h * 0.19);
                ctx.lineTo(w * 0.57, h * 0.29);
                ctx.quadraticCurveTo(w * 0.59, h * 0.2, w * 0.66, h * 0.21);
                ctx.quadraticCurveTo(w * 0.73, h * 0.22, w * 0.72, h * 0.32);
                ctx.lineTo(w * 0.69, h * 0.62);
                ctx.quadraticCurveTo(w * 0.65, h * 0.87, w * 0.46, h * 0.88);
                ctx.quadraticCurveTo(w * 0.3, h * 0.88, w * 0.2, h * 0.7);
                ctx.lineTo(w * 0.13, h * 0.57);
                ctx.quadraticCurveTo(w * 0.09, h * 0.47, w * 0.18, h * 0.43);
                ctx.quadraticCurveTo(w * 0.24, h * 0.41, w * 0.28, h * 0.52);
                ctx.stroke();
            } else if (root.name === "zoom") {
                circle(w * 0.43, h * 0.42, w * 0.25);
                line(w * 0.61, h * 0.61, w * 0.84, h * 0.84);
            } else if (root.name === "layers") {
                ctx.beginPath();
                ctx.moveTo(w * 0.5, h * 0.12);
                ctx.lineTo(w * 0.88, h * 0.34);
                ctx.lineTo(w * 0.5, h * 0.56);
                ctx.lineTo(w * 0.12, h * 0.34);
                ctx.closePath();
                ctx.stroke();
                line(w * 0.16, h * 0.5, w * 0.5, h * 0.7);
                line(w * 0.5, h * 0.7, w * 0.84, h * 0.5);
                line(w * 0.16, h * 0.66, w * 0.5, h * 0.87);
                line(w * 0.5, h * 0.87, w * 0.84, h * 0.66);
            } else if (root.name === "sliders") {
                line(w * 0.16, h * 0.25, w * 0.84, h * 0.25);
                line(w * 0.16, h * 0.5, w * 0.84, h * 0.5);
                line(w * 0.16, h * 0.75, w * 0.84, h * 0.75);
                circle(w * 0.38, h * 0.25, w * 0.07);
                circle(w * 0.66, h * 0.5, w * 0.07);
                circle(w * 0.46, h * 0.75, w * 0.07);
            } else if (root.name === "grid") {
                rect(w * 0.15, h * 0.16, w * 0.7, h * 0.68);
                line(w * 0.15, h * 0.39, w * 0.85, h * 0.39);
                line(w * 0.15, h * 0.62, w * 0.85, h * 0.62);
                line(w * 0.39, h * 0.16, w * 0.39, h * 0.84);
                line(w * 0.63, h * 0.16, w * 0.63, h * 0.84);
            } else if (root.name === "swatches") {
                circle(w * 0.44, h * 0.5, w * 0.31);
                circle(w * 0.62, h * 0.36, w * 0.18);
            } else if (root.name === "assets") {
                rect(w * 0.13, h * 0.22, w * 0.74, h * 0.58);
                line(w * 0.13, h * 0.4, w * 0.87, h * 0.4);
                line(w * 0.35, h * 0.22, w * 0.35, h * 0.8);
                line(w * 0.59, h * 0.4, w * 0.59, h * 0.8);
            } else if (root.name === "search") {
                circle(w * 0.42, h * 0.42, w * 0.24);
                line(w * 0.59, h * 0.59, w * 0.82, h * 0.82);
            } else if (root.name === "grip") {
                for (let row = 0; row < 3; row++) {
                    for (let column = 0; column < 2; column++) {
                        ctx.beginPath();
                        ctx.arc(w * (0.35 + column * 0.3), h * (0.25 + row * 0.25), w * 0.065, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }
            } else if (root.name === "more") {
                circle(w * 0.25, h * 0.5, w * 0.04);
                circle(w * 0.5, h * 0.5, w * 0.04);
                circle(w * 0.75, h * 0.5, w * 0.04);
                ctx.fill();
            } else if (root.name === "close") {
                line(w * 0.25, h * 0.25, w * 0.75, h * 0.75);
                line(w * 0.75, h * 0.25, w * 0.25, h * 0.75);
            } else if (root.name === "plus") {
                line(w * 0.5, h * 0.2, w * 0.5, h * 0.8);
                line(w * 0.2, h * 0.5, w * 0.8, h * 0.5);
            } else if (root.name === "eye") {
                ctx.beginPath();
                ctx.moveTo(w * 0.12, h * 0.5);
                ctx.quadraticCurveTo(w * 0.5, h * 0.15, w * 0.88, h * 0.5);
                ctx.quadraticCurveTo(w * 0.5, h * 0.85, w * 0.12, h * 0.5);
                ctx.stroke();
                circle(w * 0.5, h * 0.5, w * 0.11);
            } else if (root.name === "link" || root.name === "unlink") {
                ctx.save();
                ctx.scale(w / 24, h / 24);
                ctx.lineWidth = root.strokeWidth * 24 / w;
                ctx.translate(12, 12);
                ctx.rotate(-Math.PI / 4);
                ctx.translate(-12, -12);
                ctx.beginPath();
                ctx.moveTo(10, 8);
                ctx.lineTo(7, 8);
                ctx.bezierCurveTo(1.5, 8, 1.5, 16, 7, 16);
                ctx.lineTo(10, 16);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(14, 8);
                ctx.lineTo(17, 8);
                ctx.bezierCurveTo(22.5, 8, 22.5, 16, 17, 16);
                ctx.lineTo(14, 16);
                ctx.stroke();
                if (root.name === "link") {
                    line(8, 12, 16, 12);
                } else {
                    line(12, 4, 12, 6);
                    line(12, 18, 12, 20);
                }
                ctx.restore();
            } else if (root.name === "lock") {
                rect(w * 0.23, h * 0.43, w * 0.54, h * 0.42);
                ctx.beginPath();
                ctx.arc(w * 0.5, h * 0.43, w * 0.2, Math.PI, 0);
                ctx.stroke();
            } else {
                circle(w * 0.5, h * 0.5, w * 0.3);
            }
        }
    }
}
