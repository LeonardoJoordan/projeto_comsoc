import json
from PySide6.QtCore import QObject, Signal

class HistoryManager(QObject):
    # Sinais para atualizar a UI (ex: desabilitar botões se não puder desfazer)
    canUndoChanged = Signal(bool)
    canRedoChanged = Signal(bool)

    def __init__(self, max_steps: int = 30):
        super().__init__()
        self._max_steps = max_steps
        self._undo_stack = []
        self._current_index = -1

    def push(self, state: dict):
        """Salva um novo estado na pilha. Ignora se for idêntico ao atual."""
        # Se estamos no meio da pilha e o usuário faz uma nova ação, 
        # o futuro alternativo (redo) é destruído.
        if self._current_index < len(self._undo_stack) - 1:
            self._undo_stack = self._undo_stack[:self._current_index + 1]

        # Evita salvar snapshots duplicados (se o usuário não mudou nada)
        if self._undo_stack and self._current_index >= 0:
            current_state = self._undo_stack[self._current_index]
            # Uma forma rápida e segura de comparar dicionários complexos no Python
            if json.dumps(current_state, sort_keys=True) == json.dumps(state, sort_keys=True):
                return

        self._undo_stack.append(state)
        
        # Limpa o histórico mais antigo se exceder o limite de RAM
        if len(self._undo_stack) > self._max_steps:
            self._undo_stack.pop(0)
        else:
            self._current_index += 1

        self._emit_status()

    def undo(self) -> dict | None:
        """Retrocede um passo e retorna o estado correspondente."""
        if self.can_undo():
            self._current_index -= 1
            self._emit_status()
            return self._undo_stack[self._current_index]
        return None

    def redo(self) -> dict | None:
        """Avança um passo e retorna o estado correspondente."""
        if self.can_redo():
            self._current_index += 1
            self._emit_status()
            return self._undo_stack[self._current_index]
        return None

    def can_undo(self) -> bool:
        return self._current_index > 0

    def can_redo(self) -> bool:
        return self._current_index < len(self._undo_stack) - 1

    def clear(self):
        """Limpa todo o histórico (útil ao carregar um novo modelo do zero)."""
        self._undo_stack.clear()
        self._current_index = -1
        self._emit_status()

    def _emit_status(self):
        """Avisa a interface se é possível usar o Ctrl+Z / Ctrl+Y agora."""
        self.canUndoChanged.emit(self.can_undo())
        self.canRedoChanged.emit(self.can_redo())