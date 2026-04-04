from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PySide6.QtCore import Qt
from core.paths import get_logs_dir
from datetime import datetime

class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Log")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout.addWidget(title)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setMinimumHeight(180)
        layout.addWidget(self.text, 1)

    def append(self, msg: str):
        self.text.append(msg)
        
        log_file = get_logs_dir() / "app.log"
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{time_str}] {msg}\n")
        except Exception:
            pass # Falha silenciosa para não quebrar a UI se o disco estiver bloqueado/cheio

    def clear(self):
        self.text.clear()