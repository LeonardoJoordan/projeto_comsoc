"""Inicializador independente do editor QML integrado ao backend existente."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickControls2 import QQuickStyle


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Abre o editor QML do COMSOC.")
    parser.add_argument("--model", type=Path, help="Arquivo template_v3.json a abrir")
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
    app = QApplication(sys.argv)
    app.setApplicationName("C.O.M.S.O.C. — Editor QML")
    app.setOrganizationName("C.O.M.S.O.C.")

    from features.editor_qml.session import EditorSession
    try:
        session = EditorSession(args.model)
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    window = session.window
    app.aboutToQuit.connect(session.bridge.shutdown)

    if args.screenshot:
        destination = args.screenshot.expanduser().resolve()

        def save_screenshot() -> None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            image = window.grabWindow()
            if image.isNull() or not image.save(str(destination)):
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
