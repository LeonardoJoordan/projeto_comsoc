import os
import sys
import traceback
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QApplication
from core.custom_tooltip import CustomTooltipManager
from core.paths import get_logs_dir
from features.workspace.main_window import MainWindow

# --- FIX teclado PT-BR no Qt (Linux) ---
os.environ.setdefault("QT_IM_MODULE", "ibus")
os.environ.setdefault("GTK_IM_MODULE", "ibus")
os.environ.setdefault("XMODIFIERS", "@im=ibus")


def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log_file = get_logs_dir() / "crash_log.txt"
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{time_str}] CRASH OCORRIDO:\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            f.write("-" * 50 + "\n")
    except:
        pass

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Erro Fatal")
    msg.setText("Ocorreu um erro inesperado e o sistema precisa ser encerrado.")
    msg.setInformativeText(f"Os detalhes técnicos foram salvos em:\n{log_file}")
    msg.setDetailedText("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    msg.exec()
    sys.exit(1)

sys.excepthook = global_exception_handler

def main():
    app = QApplication(sys.argv)
    
    # Ativa o motor global de Tooltips Customizados (Substitui os nativos do Linux/Windows)
    CustomTooltipManager.install(delay_ms=1500)
    
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()