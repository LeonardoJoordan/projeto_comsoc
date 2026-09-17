# Revisão independente após o roadmap

Revisão da branch `novo_main`, iniciada no commit `e1449dc`, em 17/09/2026. O item 1 foi corrigido após sua confirmação; os demais itens continuam apenas documentados.

## Conclusão

Ainda há pontas soltas. A conclusão anterior de limpeza integral foi abrangente demais. A suíte existente continua passando, mas verificações adicionais reproduziram falhas que ela não cobre. Algumas são anteriores ao roadmap e permaneceram após a auditoria; não se deve atribuir todas à refatoração.

## Problemas encontrados

### 1. Callbacks acessam widgets destruídos — corrigido

- **Local:** `features/editor/frontend.py`, `FooterSaveAlignment.schedule/align` e conexões ao sinal `theme_manager().changed`.
- **Evidência:** criar um editor, executar `deleteLater()`, processar `DeferredDelete` e trocar o tema reproduziu erros `Internal C++ object already deleted` em widgets, labels e botões. Destruir imediatamente após a criação também reproduziu acesso à sidebar destruída pelo alinhamento do rodapé.
- **Limite:** o teste de fechar normalmente e trocar o tema não reproduziu o erro. O problema confirmado está na destruição efetiva da janela e nas callbacks remanescentes, não em todo fechamento.
- **Correção aplicada:** timers adiados agora pertencem aos widgets que os utilizam e são cancelados com sua destruição. Callbacks locais do tema são desconectados quando o widget responsável é destruído, e o alinhamento do rodapé valida seus objetos antes de acessá-los.
- **Regressão:** destruir efetivamente o editor com alinhamento pendente, processar `DeferredDelete` e trocar o tema não produz exceções. A suíte específica do editor passou com 61 testes.

### 2. Colagem em seleção múltipla pode atingir colunas erradas — prioridade alta

- **Local:** `features/spreadsheet/table_panel.py`, `_paste_from_clipboard`, ramo de uma célula para várias selecionadas.
- **Evidência:** colunas lógicas A/B/C; mover A para o final; selecionar A e B; colar `X`. Resultado observado: A conserva o valor anterior e B/C recebem `X`.
- **Causa:** `QModelIndex.column()` já é lógico, mas é convertido novamente por `header.logicalIndex()`.
- **Solução:** usar o índice lógico diretamente nesse ramo e testar colagens depois de reordenar cabeçalhos.

### 3. Colagem não protege a coluna de assinatura — prioridade alta

- **Local:** `features/spreadsheet/table_panel.py`, `_paste_from_clipboard`.
- **Evidência:** com cabeçalhos `Cópias`, `Ass.`, `Nome`, colar `João` sobre `Ass.` grava o texto na coluna funcional, deixando `Nome` vazio.
- **Causa:** o início da rotina ainda procura assinatura na coluna 0; no layout atual ela fica na coluna 1. O ramo de preenchimento múltiplo compartilha essa inconsistência.
- **Solução:** identificar colunas funcionais de forma única e pular/proteger assinatura nos dois caminhos da colagem, inclusive após reordenação.

### 4. Excluir todas as linhas perde os controles da linha inicial — prioridade média

- **Local:** `features/spreadsheet/table_panel.py`, `_delete_selected_rows_action` e `_handle_delete`.
- **Evidência:** após excluir todas as linhas de uma tabela com assinatura, resta uma linha com `[None, None, None]`: sem o valor inicial de cópias e sem checkbox de assinatura.
- **Solução:** reutilizar a mesma inicialização de linhas de `_add_rows`, preservando os padrões das colunas funcionais nos dois caminhos de exclusão.

### 5. Nomes de saída não são seguros para todos os sistemas — prioridade alta antes da distribuição

- **Local:** `core/naming_engine.py`, utilizado por `features/generator/manager.py`.
- **Evidência:** o gerador retorna `CON`, `Ana` e `ana` como nomes válidos e distintos. Não há tratamento de nomes reservados nem comparação sem distinção de maiúsculas/minúsculas.
- **Impacto:** em sistemas de arquivos que ignoram caixa, dois resultados podem disputar o mesmo arquivo; nomes reservados podem falhar no Windows. A falha de normalização foi demonstrada no Linux; não foi executado teste nativo Windows.
- **Solução:** normalizar nomes reservados, caracteres de controle e limites de comprimento; reservar nomes com comparação compatível com os sistemas suportados e testar colisões antes da geração.

### 6. Construção de layouts antigos ainda existe nos painéis do editor — dívida técnica remanescente

- **Local:** `features/editor/controls.py` e `features/editor/properties.py`.
- **Evidência:** após construir a interface, `caixa_texto_panel` permanece oculto com cinco widgets e `editor_texto_panel` com trinta, incluindo títulos e labels antigos. Os construtores ainda montam layouts que o frontend reaproveita parcialmente.
- **Impacto:** não é, por si só, um crash. Porém contradiz a conclusão de que toda montagem de interface antiga foi removida, mantém responsabilidades misturadas e torna o ciclo de vida mais difícil de revisar.
- **Solução:** separar os controladores da construção visual e criar apenas os controles consumidos pela interface atual, preservando explicitamente a propriedade Qt e as conexões.

## Segurança e distribuição: pendências delimitadas

- A importação ZIP usa `extractall()` para o pacote inteiro, sem limite explícito de tamanho descompactado, número de entradas ou proporção de compressão (`features/workspace/main_window.py`). Isso permite consumo excessivo de disco/tempo por um pacote hostil. Extrair apenas modelos escolhidos, com limites e validação das entradas. Não foi demonstrada execução de código nem exploração de travessia de diretórios nesta revisão.
- Windows, macOS, pacotes instaláveis e prova física duplex continuam sem validação nesta sessão. Licenças e procedência dos ícones continuam pendências de publicação já registradas.
- Os relatórios anteriores devem ser corrigidos após tratar os itens acima. Testes aprovados demonstram os cenários cobertos; não comprovam ausência de falhas nem eliminação de toda dívida técnica.

## Evidências preservadas

- Suíte principal: **111 testes e 10 subtestes aprovados** (33,04 s).
- Editor: **60 testes aprovados** (6,01 s).
- Revisados os commits das etapas 4–7 e os caminhos de sessão multipágina, recursos, temas, tabela, imagens dinâmicas, importação e nomes de saída; consultada a cobertura de grupos, persistência, renderização e migração.
- Reproduções adicionais executadas em Qt offscreen, com dados sintéticos e sem salvar modelos do usuário.
- Compatibilidade v3/v4 e migração antiga são código ativo necessário, não resíduos a apagar.

## Ordem sugerida

Corrigir primeiro o ciclo de vida e as colagens; depois restaurar os padrões da linha inicial e proteger nomes de saída. Em seguida, concluir a separação dos painéis e reforçar importações. Acrescentar regressões para as reproduções deste relatório e repetir os fluxos antes de encerrar novamente a auditoria.
