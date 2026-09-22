import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox

from core.dialog_buttons import (
    install_dialog_button_style,
    style_dialog_button_box,
    style_message_box,
)
from core.themes import theme_color


APP = QApplication.instance() or QApplication([])


def test_accept_and_cancel_buttons_have_equal_size_colors_and_no_icons():
    box = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok
        | QDialogButtonBox.StandardButton.Cancel
    )
    accept = box.button(QDialogButtonBox.StandardButton.Ok)
    cancel = box.button(QDialogButtonBox.StandardButton.Cancel)

    style_dialog_button_box(box)

    assert accept.size() == cancel.size()
    assert accept.icon().isNull()
    assert cancel.icon().isNull()
    assert theme_color("accent") in accept.styleSheet()
    assert theme_color("button") in cancel.styleSheet()
    assert theme_color("danger_background") in cancel.styleSheet()
    assert "text-align: center" in accept.styleSheet()
    assert "text-align: center" in cancel.styleSheet()


def test_custom_message_box_actions_follow_the_same_dimensions():
    message = QMessageBox()
    accept = message.addButton("Aceitar", QMessageBox.ButtonRole.AcceptRole)
    cancel = message.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)

    style_message_box(message)

    assert accept.size() == cancel.size()
    assert accept.icon().isNull()
    assert cancel.icon().isNull()


def test_global_filter_reaches_qt_generated_yes_no_message_boxes():
    install_dialog_button_style(APP)
    message = QMessageBox(
        QMessageBox.Icon.Question,
        "Limpar página",
        "Remover todo o conteúdo?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    message.show()
    APP.processEvents()

    accept = message.button(QMessageBox.StandardButton.Yes)
    cancel = message.button(QMessageBox.StandardButton.No)
    assert accept.size() == cancel.size()
    assert accept.icon().isNull()
    assert cancel.icon().isNull()
    assert theme_color("accent") in accept.styleSheet()
    assert theme_color("button") in cancel.styleSheet()
    assert theme_color("danger_background") in cancel.styleSheet()
    message.close()


def test_message_layout_keeps_title_and_centers_single_action():
    from PySide6.QtWidgets import QLabel
    install_dialog_button_style(APP)
    message = QMessageBox(QMessageBox.Icon.Information, 'Importação concluída',
                         'Importados: 3', QMessageBox.StandardButton.Ok)
    message.show()
    APP.processEvents()
    assert message.width() >= 480
    assert message.findChild(QLabel, 'fornaxMessageTitle').text() == 'Importação concluída'
    assert message.findChild(QDialogButtonBox).centerButtons()
    message.close()


def test_long_error_preserves_full_content_in_details():
    install_dialog_button_style(APP)
    content = 'Falha na importação\n' + 'Detalhe técnico do arquivo.\n' * 70
    message = QMessageBox(QMessageBox.Icon.Critical, 'Erro', content,
                         QMessageBox.StandardButton.Ok)
    message.show()
    APP.processEvents()
    assert message.text() == 'Falha na importação'
    assert message.detailedText() == content
    message.close()
