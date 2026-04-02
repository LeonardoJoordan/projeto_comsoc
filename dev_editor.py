import os
import sys

# --- FIX teclado PT-BR no Qt (Linux) ---
os.environ.setdefault("QT_IM_MODULE", "ibus")
os.environ.setdefault("GTK_IM_MODULE", "ibus")
os.environ.setdefault("XMODIFIERS", "@im=ibus")

from PySide6.QtWidgets import QApplication
from features.editor.editor_window import EditorWindow

def main():
    app = QApplication(sys.argv)
    
    editor = EditorWindow()
    editor.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()