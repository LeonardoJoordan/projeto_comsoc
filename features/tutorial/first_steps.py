"""Tutorial interativo de primeiros passos do FORNAX Forge."""

from __future__ import annotations

from pathlib import Path
import re

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QTimer
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox

from core.i18n import tr
from features.spreadsheet.headers import table_column_key
from .coach_marks import CoachMark


MODEL_TEXT = (
    "Este cartão foi feito de forma muito rápida e eficiente para "
    "{nome}| com a ajuda de {programa}|!"
)
NAMES = (
    "Ana Silva", "Bruno Costa", "Carla Souza", "Daniel Lima", "Elisa Rocha",
    "Felipe Alves", "Gabriela Nunes", "Henrique Melo", "Isabela Martins",
    "João Ribeiro",
)
PROGRAM = "FORNAX Forge"
TOTAL_STEPS = 35


class FirstStepsTutorial(QObject):
    """Conduz um trabalho real, validando cada ação antes de avançar."""

    def __init__(self, workspace):
        super().__init__(workspace)
        self.workspace = workspace
        self.editor = None
        self.coach = None
        self.step = 1
        self._phase = 0
        self.text_box = None
        self._initial_box_size = None
        self._connections = []
        self._seen_rows = set()
        self._model_saved = False
        self._last_output_dir = None
        self._clipboard_backup = QApplication.clipboard().text()
        self._poll = QTimer(self)
        self._poll.setInterval(120)
        self._poll.timeout.connect(self._poll_current_step)

    def start(self):
        QApplication.instance().installEventFilter(self)
        self._show_step()

    def _replace_coach(self, host):
        if self.coach is not None:
            self.coach.close()
        self.coach = CoachMark(host)
        self.coach.card.nextRequested.connect(self.next)
        self.coach.card.backRequested.connect(self.back)
        self.coach.card.skipRequested.connect(self.finish)

    def _ensure_coach(self, host):
        if self.coach is None or self.coach.host is not host:
            self._replace_coach(host)

    def _disconnect_stage(self):
        self._poll.stop()
        while self._connections:
            signal, callback = self._connections.pop()
            try:
                signal.disconnect(callback)
            except (RuntimeError, TypeError):
                pass

    def _connect(self, signal, callback):
        signal.connect(callback)
        self._connections.append((signal, callback))

    def _show(self, host, *, target=None, provider=None, title, body,
              wait=False, next_text=None, back=True):
        self._ensure_coach(host)
        self.coach.show_step(
            target=target,
            target_rect_provider=provider,
            title=title,
            body=body,
            current=self.step,
            total=TOTAL_STEPS,
            can_go_back=back,
            next_text=next_text or tr("Continuar"),
            wait_for_action=wait,
        )

    def _advance(self, expected=None):
        if expected is not None and self.step != expected:
            return
        self._disconnect_stage()
        self.step += 1
        self._phase = 0
        self._show_step()

    def next(self):
        phase_steps = {15: 1, 19: 1, 21: 1, 23: 2, 26: 2}
        if self.step in phase_steps and self._phase < phase_steps[self.step]:
            self._disconnect_stage()
            self._phase += 1
            self._show_step()
            return
        if self.step >= TOTAL_STEPS:
            self.finish()
        else:
            self._advance(self.step)

    def back(self):
        self._disconnect_stage()
        self.step = max(1, self.step - 1)
        self._phase = 0
        self._show_step()

    def _menu_action_rect(self, menu, action):
        def provider():
            rect = menu.actionGeometry(action)
            point = menu.mapTo(self.workspace, rect.topLeft())
            return QRect(point, rect.size()).adjusted(-4, -3, 4, 3)
        return provider

    def _menubar_action_rect(self, menu):
        def provider():
            bar = self.workspace.menuBar()
            rect = bar.actionGeometry(menu.menuAction())
            point = bar.mapTo(self.workspace, rect.topLeft())
            return QRect(point, rect.size()).adjusted(-4, -3, 4, 3)
        return provider

    def _graphics_rect(self, item):
        def provider():
            if self.editor is None or item is None or item.scene() is None:
                return QRect()
            polygon = self.editor.view.mapFromScene(item.sceneBoundingRect())
            rect = polygon.boundingRect()
            point = self.editor.view.viewport().mapTo(self.editor, rect.topLeft())
            return QRect(point, rect.size()).adjusted(-7, -7, 7, 7)
        return provider

    @staticmethod
    def _widget_rect(widget, host):
        def provider():
            point = widget.mapTo(host, QPoint(0, 0))
            return QRect(point, widget.size()).adjusted(-7, -7, 7, 7)
        return provider

    def _document_rect(self):
        def provider():
            rect = self.editor.view.mapFromScene(self.editor._document_rect).boundingRect()
            point = self.editor.view.viewport().mapTo(self.editor, rect.topLeft())
            return QRect(point, rect.size())
        return provider

    def _table_column(self, name):
        table = self.workspace.table_panel.table
        for column in range(table.columnCount()):
            if table_column_key(table.horizontalHeaderItem(column)) == name:
                return column
        return -1

    def _table_range_rect(self, columns=("nome", "programa"), rows=10):
        def provider():
            table = self.workspace.table_panel.table
            logical = [self._table_column(name) for name in columns]
            logical = [column for column in logical if column >= 0]
            if not logical or not table.isVisible():
                return QRect()
            rect = QRect()
            for row in range(min(rows, table.rowCount())):
                for column in logical:
                    cell = table.visualRect(table.model().index(row, column))
                    rect = cell if rect.isNull() else rect.united(cell)
            point = table.viewport().mapTo(self.workspace, rect.topLeft())
            return QRect(point, rect.size()).adjusted(-3, -3, 3, 3)
        return provider

    def _set_clipboard_text(self, text):
        QApplication.clipboard().setText(text)

    def _plain_box_text(self):
        if self.text_box is None:
            return ""
        document = QTextDocument()
        document.setHtml(self.text_box.state.html_content)
        return document.toPlainText()

    def _tutorial_values_ok(self, names=True, programs=True):
        table = self.workspace.table_panel.table
        name_col = self._table_column("nome")
        program_col = self._table_column("programa")
        if table.rowCount() < 10 or name_col < 0 or program_col < 0:
            return False
        for row in range(10):
            if names:
                item = table.item(row, name_col)
                if item is None or item.text().strip() != NAMES[row]:
                    return False
            if programs:
                item = table.item(row, program_col)
                if item is None or item.text().strip() != PROGRAM:
                    return False
        return True

    def _tutorial_data_empty(self):
        table = self.workspace.table_panel.table
        for name in ("nome", "programa"):
            column = self._table_column(name)
            if column < 0:
                continue
            for row in range(table.rowCount()):
                item = table.item(row, column)
                if item is not None and item.text().strip():
                    return False
        return True

    def _prepare_workspace_table(self):
        panel = self.workspace.table_panel
        if not panel.isVisible() and self.workspace._workspace_data_toggle.isVisible():
            self.workspace._workspace_data_toggle.click()

    def _show_step(self):
        self._disconnect_stage()
        if self.step <= 3 or self.step >= 19:
            self._show_workspace_step()
        else:
            self._show_editor_step()

    def _show_workspace_step(self):
        w = self.workspace
        if self.step == 1:
            self._show(w, title=tr("Primeiros passos"), back=False,
                       next_text=tr("Começar"), body=tr(
                "Você criará um modelo, preencherá dez itens e gerará o primeiro trabalho. "
                "O tutorial acompanhará suas ações diretamente nos controles do programa."))
        elif self.step == 2:
            menu = w._model_menu
            self._show(w, provider=self._menubar_action_rect(menu), wait=True,
                       title=tr("Abra o menu Modelo"), body=tr(
                "Os modelos definem o visual e os campos personalizados. Clique em Modelo."))
            self._connect(menu.aboutToShow, lambda: QTimer.singleShot(0, lambda: self._advance(2)))
        elif self.step == 3:
            menu, action = w._model_menu, w._new_model_action
            menu.setActiveAction(action)
            self._show(w, provider=self._menu_action_rect(menu, action), wait=True,
                       title=tr("Crie um modelo"), body=tr(
                "Clique em Novo modelo para abrir um documento vazio no editor."))
            self._connect(action.triggered, self._new_editor_opened)
        elif self.step == 19:
            self._prepare_workspace_table()
            if self._phase == 0:
                self._show(w, target=w.preview_panel.cbo_models,
                           title=tr("Modelo salvo"), body=tr(
                    "O novo modelo está selecionado na biblioteca."))
            else:
                self._show(w, provider=self._table_range_rect(("nome", "programa"), 1),
                           title=tr("Campos criados"), body=tr(
                    "Os placeholders criaram as colunas nome e programa. Um placeholder obrigatório "
                    "vazio oculta a caixa; um trecho opcional pode desaparecer sem ocultar o restante."))
        elif self.step == 20:
            self._prepare_workspace_table()
            self._set_clipboard_text("\n".join(NAMES))
            self._show(w, provider=self._table_range_rect(("nome",), 1), wait=True,
                       title=tr("Cole dez nomes"), body=tr(
                "Dez nomes foram copiados. Clique na primeira célula de nome e pressione Ctrl+V."))
            self._poll.start()
        elif self.step == 21:
            if self._phase == 0:
                self._show(w, provider=self._table_range_rect(("nome",), 10),
                           title=tr("Dez linhas de uma vez"), body=tr(
                    "Uma única colagem preencheu dez linhas. O FORNAX preserva a estrutura copiada de uma planilha."))
            else:
                self._show(w, target=w.preview_panel, title=tr("Trecho opcional em ação"), body=tr(
                    "O preview já mostra os nomes porque programa está dentro de um trecho opcional. "
                    "Esse trecho permanece oculto até a segunda coluna ser preenchida."))
        elif self.step == 22:
            self._set_clipboard_text("\n".join([PROGRAM] * 10))
            self._show(w, provider=self._table_range_rect(("programa",), 1), wait=True,
                       title=tr("Complete a segunda coluna"), body=tr(
                "FORNAX Forge foi copiado dez vezes. Clique na primeira célula de programa e pressione Ctrl+V."))
            self._poll.start()
        elif self.step == 23:
            if self._phase == 0:
                self._show(w, provider=self._table_range_rect(("nome", "programa"), 10),
                           title=tr("Duas colunas preenchidas"), body=tr(
                    "As dez linhas agora possuem nome e programa."))
            elif self._phase == 1:
                self._seen_rows = set()
                self._show(w, target=w.preview_panel, wait=True,
                           title=tr("Confira o preview"), body=tr(
                    "Selecione uma linha diferente para ver o preview acompanhar o item."))
                self._connect(w.table_panel.table.itemSelectionChanged, self._workspace_row_changed)
            else:
                self._show(w, target=w.preview_panel, title=tr("Preview atualizado"), body=tr(
                    "O preview mostra o conteúdo da linha selecionada antes da geração."))
        elif self.step == 24:
            table = w.table_panel.table
            self._show(w, target=w.table_panel.btn_delete_rows, wait=True,
                       title=tr("Exclua as linhas"), body=tr(
                "Clique no cabeçalho da primeira linha e, com Shift, clique no da última. Depois clique em Excluir."))
            self._connect(w.table_panel.btn_delete_rows.clicked,
                          lambda: QTimer.singleShot(0, self._after_delete))
            table.setFocus()
        elif self.step == 25:
            combined = "\n".join(f"{name}\t{PROGRAM}" for name in NAMES)
            self._set_clipboard_text(combined)
            self._show(w, provider=self._table_range_rect(("nome",), 1), wait=True,
                       title=tr("Cole duas colunas"), body=tr(
                "Os nomes e o programa foram copiados juntos. Clique na primeira célula de nome e pressione Ctrl+V."))
            self._poll.start()
        elif self.step == 26:
            if self._phase == 0:
                self._show(w, provider=self._table_range_rect(("nome", "programa"), 10),
                           title=tr("Use seus dados existentes"), body=tr(
                    "Você pode copiar várias linhas e colunas do Excel, Google Sheets ou LibreOffice, evitando redigitação."))
            elif self._phase == 1:
                self._seen_rows = set()
                self._show(w, target=w.preview_panel, wait=True,
                           title=tr("Navegue pelos itens"), body=tr(
                    "Selecione dois itens diferentes para conferir a atualização do preview."))
                self._connect(w.table_panel.table.itemSelectionChanged, self._workspace_row_changed)
            else:
                self._show(w, target=w.preview_panel, title=tr("Dados conferidos"), body=tr(
                    "O preview acompanhou os itens escolhidos. Agora o trabalho está pronto para ser gerado."))
        elif self.step == 27:
            self._show(w, target=w.btn_sel_out, wait=True,
                       title=tr("Escolha o destino"), body=tr(
                "Clique nos três pontos e escolha a pasta onde os trabalhos serão armazenados."))
            self._connect(w.btn_sel_out.clicked,
                          lambda: QTimer.singleShot(0, self._output_folder_selected))
        elif self.step == 28:
            self._show(w, target=w.txt_output_path,
                       title=tr("Pasta principal"), body=tr(
                "Cada geração será guardada dentro desta pasta em uma pasta exclusiva."))
        elif self.step == 29:
            menu = w._view_menu
            self._show(w, provider=self._menubar_action_rect(menu), wait=True,
                       title=tr("Abra o menu Exibir"), body=tr(
                "Antes de gerar, vamos abrir o log. Clique em Exibir."))
            self._connect(menu.aboutToShow, lambda: QTimer.singleShot(0, lambda: self._advance(29)))
        elif self.step == 30:
            menu, action = w._view_menu, w._workspace_log_toggle
            menu.setActiveAction(action)
            already_visible = action.isChecked()
            self._show(w, provider=self._menu_action_rect(menu, action),
                       wait=not already_visible, title=tr("Mostre o log"), body=(
                tr("O log já está visível. Continue para conhecê-lo.") if already_visible
                else tr("Clique em Log de processamento para exibi-lo.")))
            if not already_visible:
                self._connect(action.toggled, self._log_toggled)
        elif self.step == 31:
            self._show(w, target=w.log_panel, title=tr("Log de processamento"), body=tr(
                "O log mostra andamento, avisos e resultados. Ele ajuda a acompanhar trabalhos maiores e identificar dados que precisam de atenção."))
        elif self.step == 32:
            self._show(w, target=w.btn_generate_cards, wait=True,
                       title=tr("Gere o material"), body=tr(
                "Clique em Gerar material. As dez linhas produzirão dez cartões personalizados."))
            self._connect(w.btn_generate_cards.clicked,
                          lambda: QTimer.singleShot(0, self._generation_started))
        elif self.step == 33:
            self._show(w, target=w.log_panel, wait=True, back=False,
                       title=tr("Acompanhe a velocidade"), body=tr(
                "Acompanhe o tempo real no log. Um trabalho que exigiria editar dez cartões individualmente é concluído automaticamente em poucos segundos."))
        elif self.step == 34:
            self._show(w, target=w.log_panel, title=tr("Geração concluída"), body=tr(
                "Os dez itens foram gerados. O log é opcional: mantenha-o visível para acompanhar detalhes ou oculte-o para ampliar a área de trabalho."))
        elif self.step == 35:
            folder = self._last_output_dir or getattr(w, "_last_forge_output_dir", None)
            name = Path(folder).name if folder else tr("a nova pasta da Forja")
            self._show(w, target=w.log_panel, title=tr("Trabalho organizado"),
                       next_text=tr("Concluir"), body=tr(
                "Os arquivos foram reunidos em {pasta}. Cada geração cria uma nova Forja numerada, "
                "evitando misturar arquivos de trabalhos diferentes.").format(pasta=name))

    def _show_editor_step(self):
        e = self.editor
        if e is None:
            return
        if self.step == 4:
            self._show(e, provider=self._document_rect(), title=tr("Área do documento"), body=tr(
                "Tudo que permanecer dentro da página fará parte do material gerado. A área externa pode ser usada para organizar objetos."))
        elif self.step == 5:
            self._show(e, target=e.btn_add, wait=True, title=tr("Adicione texto"), body=tr(
                "Clique em Texto para adicionar o primeiro conteúdo personalizado."))
            self._connect(e.btn_add.clicked, lambda: QTimer.singleShot(0, self._text_added))
        elif self.step == 6:
            self._show(e, provider=self._graphics_rect(self.text_box), title=tr("Texto adicionado"), body=tr(
                "A caixa está selecionada. Os marcadores ao redor dela permitem mudar seu tamanho."))
        elif self.step == 7:
            self._initial_box_size = (self.text_box.rect().width(), self.text_box.rect().height())
            self._show(e, provider=self._graphics_rect(self.text_box), wait=True,
                       title=tr("Redimensione a caixa"), body=tr(
                "Arraste um marcador para deixar a caixa mais larga. O texto se adapta ao novo espaço."))
            self._poll.start()
        elif self.step == 8:
            self._show(e, provider=self._graphics_rect(self.text_box), title=tr("Novo tamanho"), body=tr(
                "A caixa agora possui mais espaço. Textos e outros objetos podem ser redimensionados dessa forma."))
        elif self.step == 9:
            e._text_section.header.setChecked(True)
            self._show(e, target=e._text_section.header,
                       title=tr("Menu Texto"), body=tr(
                "Este é o menu Texto da barra lateral direita. Nele você ajusta fonte, tamanho, cor, estilo, alinhamento, entrelinha e recuo."))
        elif self.step == 10:
            button = e.editor_texto_panel.alignment_buttons[1]
            self._show(e, target=button,
                       provider=self._widget_rect(e.editor_texto_panel.alignment_widget, e),
                       wait=True, title=tr("Centralize horizontalmente"), body=tr(
                "Clique em Centralizar para alinhar as linhas no centro da caixa."))
            self._connect(button.clicked, lambda: QTimer.singleShot(0, self._horizontal_aligned))
        elif self.step == 11:
            self._show(e, provider=self._graphics_rect(self.text_box), title=tr("Alinhamento horizontal"), body=tr(
                "O conteúdo agora está centralizado entre as laterais da caixa."))
        elif self.step == 12:
            button = e.editor_texto_panel.alignment_buttons[5]
            self._show(e, target=button,
                       provider=self._widget_rect(e.editor_texto_panel.alignment_widget, e),
                       wait=True, title=tr("Centralize verticalmente"), body=tr(
                "Clique em Meio para posicionar o texto no centro vertical da caixa."))
            self._connect(button.clicked, lambda: QTimer.singleShot(0, self._vertical_aligned))
        elif self.step == 13:
            self._show(e, provider=self._graphics_rect(self.text_box), title=tr("Centralizado nos dois sentidos"), body=tr(
                "Os alinhamentos horizontal e vertical são independentes e agora estão centralizados."))
        elif self.step == 14:
            self._set_clipboard_text(MODEL_TEXT)
            self._show(e, provider=self._graphics_rect(self.text_box), wait=True,
                       title=tr("Cole o conteúdo do exercício"), body=tr(
                "O texto foi copiado. Dê dois cliques na caixa, pressione Ctrl+A e depois Ctrl+V."))
            self._poll.start()
        elif self.step == 15:
            if self._phase == 0:
                self._show(e, provider=self._graphics_rect(self.text_box),
                           title=tr("Placeholders"), body=tr(
                    "nome e programa são placeholders. Cada linha da tabela poderá fornecer conteúdos diferentes para eles."))
            else:
                self._show(e, target=e.lst_placeholders,
                           title=tr("Trecho opcional"), body=tr(
                    "Os dois campos aparecem aqui. O trecho entre barras verticais só aparece quando programa possui conteúdo; um placeholder obrigatório vazio oculta a caixa inteira."))
        elif self.step == 16:
            self._show(e, target=e.btn_save, wait=True, title=tr("Salve o modelo"), body=tr(
                "Clique em Salvar modelo para adicioná-lo à biblioteca."))
        elif self.step == 17:
            # O QInputDialog modal contém a orientação e mantém o foco correto.
            if self.coach is not None:
                self.coach.card.hide()
                self.coach.spotlight.hide()
        elif self.step == 18:
            if self.coach is not None:
                self.coach.card.hide()
                self.coach.spotlight.hide()

    def _new_editor_opened(self):
        self._disconnect_stage()
        self.editor = getattr(self.workspace, "editor_window", None)
        if self.editor is None:
            return
        self.editor.modelSaved.connect(self._model_was_saved)
        self.step = 4
        QTimer.singleShot(0, self._show_step)

    def _text_added(self):
        from features.editor.canvas_items import DesignerBox
        selected = [item for item in self.editor.scene.selectedItems() if isinstance(item, DesignerBox)]
        if not selected:
            return
        self.text_box = selected[0]
        self._advance(5)

    def _horizontal_aligned(self):
        if self.text_box is not None and self.text_box.state.align == "center":
            self._advance(10)

    def _vertical_aligned(self):
        if self.text_box is not None and self.text_box.state.vertical_align == "center":
            self._advance(12)

    def _model_was_saved(self, *_args):
        self._model_saved = True

    def _workspace_row_changed(self):
        row = self.workspace.table_panel.table.currentRow()
        if row >= 0:
            self._seen_rows.add(row)
        required = 1 if self.step == 23 else 2
        if len(self._seen_rows) >= required:
            expected = self.step
            self._disconnect_stage()
            def show_result():
                if self.step != expected:
                    return
                self._phase = 2
                self._show_step()
            QTimer.singleShot(180, show_result)

    def _after_delete(self):
        if self.step == 24 and self._tutorial_data_empty():
            self._advance(24)

    def _output_folder_selected(self):
        if self.step == 27 and Path(self.workspace.txt_output_path.text().strip()).is_dir():
            self._advance(27)

    def _log_toggled(self, checked):
        if checked:
            QTimer.singleShot(0, lambda: self._advance(30))

    def _generation_started(self):
        if self.step != 32:
            return
        manager = getattr(self.workspace, "manager", None)
        if manager is None or self.workspace.btn_generate_cards.isEnabled():
            return
        self._disconnect_stage()
        self.step = 33
        self._show_step()
        self._connect(manager.finished_process, self._generation_finished)

    def _generation_finished(self):
        if getattr(self.workspace, "_generation_failed", False):
            self._disconnect_stage()
            self.step = 32
            self._show_step()
            return
        self._last_output_dir = getattr(self.workspace, "_last_forge_output_dir", None)
        self._advance(33)

    def _poll_current_step(self):
        if self.step == 7 and self.text_box is not None:
            size = (self.text_box.rect().width(), self.text_box.rect().height())
            if self._initial_box_size and (
                abs(size[0] - self._initial_box_size[0]) > 1
                or abs(size[1] - self._initial_box_size[1]) > 1
            ):
                self._advance(7)
        elif self.step == 14:
            text = re.sub(r"\s+", " ", self._plain_box_text()).strip()
            expected = re.sub(r"\s+", " ", MODEL_TEXT).strip()
            if text == expected and {"nome", "programa"}.issubset(
                {self.editor.lst_placeholders.item(i).text()
                 for i in range(self.editor.lst_placeholders.count())}
            ):
                self._advance(14)
        elif self.step == 20 and self._tutorial_values_ok(programs=False):
            self._advance(20)
        elif self.step == 22 and self._tutorial_values_ok():
            self._advance(22)
        elif self.step == 25 and self._tutorial_values_ok():
            self._advance(25)

    def _name_dialog_finished(self, result):
        if result == 0 and self.step == 17:
            self.step = 16
            QTimer.singleShot(0, self._show_step)

    def _save_message_finished(self, _result):
        QTimer.singleShot(200, self._after_save_message)

    def _after_save_message(self):
        if self.step != 18:
            return
        if self.workspace.isVisible():
            self.step = 19
            self._show_step()
        elif self.editor is not None and self.editor.isVisible():
            self.step = 16
            self._show_step()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Show:
            if isinstance(watched, QInputDialog) and self.step == 16:
                self._disconnect_stage()
                self.step = 17
                self._show_editor_step()
                watched.setLabelText(tr(
                    "Digite um nome para reconhecer este modelo. Você pode usar “Meu primeiro modelo”."
                ))
                line_edit = watched.findChild(QLineEdit)
                if line_edit is not None:
                    line_edit.setPlaceholderText(tr("Meu primeiro modelo"))
                self._connect(watched.finished, self._name_dialog_finished)
            elif (isinstance(watched, QMessageBox) and self.step in (16, 17, 18)
                  and self._model_saved and watched.windowTitle() == tr("Sucesso")):
                self._disconnect_stage()
                self.step = 18
                self._show_editor_step()
                watched.setInformativeText(tr(
                    "Escolha Encerrar edição para continuar o tutorial na tela principal."
                ))
                self._connect(watched.finished, self._save_message_finished)
            elif watched is self.workspace and self.step == 18:
                QTimer.singleShot(150, self._after_save_message)
        return False

    def finish(self):
        self._disconnect_stage()
        try:
            QApplication.instance().removeEventFilter(self)
        except RuntimeError:
            pass
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._clipboard_backup)
        if self.coach is not None:
            self.coach.close()
            self.coach = None
        if getattr(self.workspace, "_active_tutorial", None) is self:
            self.workspace._active_tutorial = None
        self.deleteLater()


def start_first_steps_tutorial(workspace):
    current = getattr(workspace, "_active_tutorial", None)
    if current is not None:
        current.finish()
    tutorial = FirstStepsTutorial(workspace)
    workspace._active_tutorial = tutorial
    tutorial.start()
    return tutorial
