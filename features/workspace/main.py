"""Execute: .venv/bin/python features/workspace/main.py"""
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

os.environ.setdefault('QT_IM_MODULE', 'ibus')
os.environ.setdefault('GTK_IM_MODULE', 'ibus')
os.environ.setdefault('XMODIFIERS', '@im=ibus')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from core.custom_tooltip import CustomTooltipManager
from core.paths import APP_ID, get_logs_dir
from core.settings import SETTINGS_APPLICATION, SETTINGS_ORGANIZATION
from core.resources import app_icon_path
from features.workspace.main_window import MainWindow


def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log_file = get_logs_dir() / 'crash_log.txt'
    try:
        with log_file.open('a', encoding='utf-8') as stream:
            stream.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] CRASH OCORRIDO:\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=stream)
            stream.write('-' * 50 + '\n')
    except OSError:
        pass
    message = QMessageBox()
    message.setIcon(QMessageBox.Icon.Critical)
    message.setWindowTitle('Erro fatal')
    message.setText('Ocorreu um erro inesperado e o sistema precisa ser encerrado.')
    message.setInformativeText(f'Os detalhes técnicos foram salvos em:\n{log_file}')
    message.setDetailedText(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    message.exec()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(SETTINGS_ORGANIZATION)
    app.setApplicationName(SETTINGS_APPLICATION)
    app.setApplicationDisplayName('FORNAX Forge')
    app.setDesktopFileName(APP_ID)
    app.setWindowIcon(QIcon(str(app_icon_path())))
    app.setStyle('Fusion')
    sys.excepthook = global_exception_handler
    CustomTooltipManager.install(delay_ms=1500)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
