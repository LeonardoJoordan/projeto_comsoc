"""Execute: .venv/bin/python features/editor_novo/main.py [--model arquivo.json]."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from features.editor_novo.editor_window import EditorWindow


def main():
    parser = argparse.ArgumentParser(description='Editor Widgets independente do COMSOC')
    parser.add_argument('--model', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--screenshot', type=Path)
    args = parser.parse_args()
    if args.model and not args.model.is_file():
        parser.error('Modelo não encontrado.')
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = EditorWindow()
    if args.model:
        window.load_from_json(args.model)
    window.show()
    if args.check or args.screenshot:
        def finish():
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                if not window.grab().save(str(args.screenshot)):
                    app.exit(1)
                    return
            app.quit()
        QTimer.singleShot(500, finish)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
