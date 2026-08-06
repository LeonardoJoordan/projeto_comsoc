"""Inicializador independente do protótipo visual do editor QML."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Abre o protótipo visual do editor QML.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="carrega a interface, verifica erros QML e encerra automaticamente",
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        help="salva uma captura da janela e encerra automaticamente",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("C.O.M.S.O.C. — Protótipo do Editor QML")
    app.setOrganizationName("C.O.M.S.O.C.")

    engine = QQmlApplicationEngine()
    engine.addImportPath(os.fspath(ROOT))
    engine.load(QUrl.fromLocalFile(os.fspath(ROOT / "Main.qml")))

    if not engine.rootObjects():
        return 1

    window = engine.rootObjects()[0]

    if args.screenshot:
        destination = args.screenshot.expanduser().resolve()

        def save_screenshot() -> None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            image = window.grabWindow()
            if image.isNull() or not image.save(os.fspath(destination)):
                app.exit(2)
                return
            print(destination)
            app.quit()

        QTimer.singleShot(900, save_screenshot)
    elif args.check:
        QTimer.singleShot(250, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

