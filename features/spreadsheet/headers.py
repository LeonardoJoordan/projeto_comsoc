"""Identificadores visíveis das colunas funcionais da planilha."""
from core.i18n import tr

QUANTITY_HEADER = "Cópias"
SIGNATURE_HEADER = "Ass."


def quantity_header_label():
    # Literal mantido aqui para que o lupdate inclua o cabeçalho no catálogo.
    return tr("Cópias")


def is_quantity_header(value):
    return value in (QUANTITY_HEADER, quantity_header_label())
