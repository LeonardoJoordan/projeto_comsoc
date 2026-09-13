# Transição para FORNAX Forge

Nome: **FORNAX Forge — Personalized Batch Material Generation**.
Versão em português: **FORNAX Forge — Geração de material personalizado em lote**.

## Estado e regras de execução

- Inventário realizado em 13/09/2026, na branch `novo_main`, commit `5f0199f`.
- A branch `main` é a referência histórica indicada pelo responsável pelo projeto. Não foi alterada, nem foi consultado o GitHub nesta análise.
- [x] Mapear dependências e escrever este plano.
- [x] Etapa 1: retirar implementações antigas e consolidar documentação/testes. Concluída em 13/09/2026.
- [x] Etapa 2: oficializar entrada e nomes de diretórios. Concluída em 13/09/2026.
- [ ] Etapa 3: aplicar identidade FORNAX Forge, migrar preferências com segurança e validar.
- [ ] Encaminhar à lapidação final e preparação da distribuição.

As implementações antigas foram retiradas do workspace em 13/09/2026 e mantidas temporariamente em `/tmp/fornax-legacy-backup-20260913`. Elas continuam recuperáveis pelo Git na branch histórica `main`; o backup em `/tmp` não é permanente.

Ao concluir um passo, registrar arquivos alterados, comando de validação, resultado e pendências. Não marcar uma etapa como concluída apenas porque seus arquivos foram movidos. Não executar exclusões recursivas genéricas com base no nome “antigo”, “cache” ou “novo”. Revalidar referências antes de cada remoção: este inventário descreve o commit acima, não garante que mudanças posteriores mantenham as mesmas dependências.

## Como o mapa foi obtido

Foi calculado o fechamento transitivo dos imports Python a partir de `features/workspace_novo/main.py`, incluindo imports relativos e imports dentro de funções, por análise de AST. Foram conferidas referências textuais a módulos antigos, recursos de interface, caminhos de dados, entrada raiz, scripts de distribuição e testes. O resultado contém **40 módulos Python alcançáveis**.

Não alcançar um arquivo por import não prova que seja descartável: ícones, documentação de terceiros, scripts, dados e testes têm classificação própria abaixo. A análise é de dependências entre arquivos, não uma prova de que todos os métodos de cada arquivo são usados. Nenhuma limpeza de métodos internos está autorizada por este inventário.

### Fluxo oficial atual

`features/workspace_novo/main.py` abre `workspace_novo/main_window.py`, que utiliza o editor Widgets `editor_novo`, a tabela `spreadsheet_novo`, a prévia compartilhada e o gerador compartilhado.

**A entrada raiz ainda é antiga:** `main.py` importa `features.workspace.main_window`. O workspace antigo importa o editor antigo e carrega `editor_qml.session` dentro de uma função. Os scripts Nuitka e Flatpak usam esse `main.py`; AppImage consome o resultado da compilação. Portanto, remover o workspace antigo sem substituir a entrada raiz quebra a execução oficial e os pacotes.

## Lista de preservação: código em uso

Preservar todos os arquivos abaixo. Renomeações propostas na etapa 2 não significam exclusão de sua implementação.

| Grupo atual | Arquivos Python necessários |
| --- | --- |
| `core/` | `custom_tooltip.py`, `custom_widgets.py`, `document_layers.py`, `font_utils.py`, `history_manager.py`, `html_utils.py`, `naming_engine.py`, `object_style.py`, `paths.py`, `render_cache.py`, `template_manager.py`, `text_layout.py`, `text_state.py` |
| `features/editor_novo/` | `canvas_edit.py`, `canvas_items.py`, `draw_shapes.py`, `editor_window.py`, `frontend.py`, `properties.py`, `rulers.py` |
| `features/workspace_novo/` | `main.py`, `main_window.py`, `controls_panel.py`, `frontend.py`, `settings_dialogs.py`, `import_models_dialog.py`, `export_models_dialog.py` |
| `features/spreadsheet_novo/` | `clipboard.py`, `delegates.py`, `frontend.py`, `table_panel.py` |
| `features/generator/` | `export_dialog.py`, `imposition.py`, `manager.py`, `pdf_links.py`, `preset_warnings.py`, `renderer.py`, `workers.py` |
| `features/preview/` | `preview_panel.py` |
| `shared/` | `log_panel.py` |

Dependências que merecem atenção especial:

- `workspace_novo/settings_dialogs.py` herda `ConfigDialog` de `features/generator/export_dialog.py`, usando o alias `LegacyConfigDialog`. **Esse arquivo não é descartável**, apesar do nome do alias e da aparência antiga de partes de sua implementação.
- `spreadsheet_novo/frontend.py` importa `icon` de `editor_novo/frontend.py` e monta o caminho das setas dentro de `editor_novo/icons`. Atualizar tanto import quanto caminho literal ao renomear.
- `editor_novo/frontend.py` reaproveita controles criados por `editor_window.py` e `properties.py`; mantém o container original oculto. Não apagar esse container ou os controles “não visíveis” nesta transição: sinais e referências ainda dependem deles.
- `preview_panel.py` é compartilhado e continua ativo. O seletor antigo de editor está oculto no workspace novo; isso não torna o painel inteiro obsoleto.
- Conversão de fundos antigos, compatibilidade de JSON, HTML, camadas e estilos permanecem no código ativo. Eliminar a interface antiga não elimina a necessidade de abrir documentos antigos.

### Recursos e arquivos auxiliares a preservar

| Caminho | Destino e justificativa |
| --- | --- |
| `features/editor_novo/icons/spin-up.svg`, `spin-down.svg` | Necessários às setas de campos no editor e na tabela. Caminhos referenciados por QSS. |
| `features/workspace_novo/icons/combo-down.svg` | Necessário ao estilo dos seletores do workspace. |
| `icone.png`, `icone.ico`, `icone.icns` | Recursos atuais de distribuição. Substituir pela identidade aprovada posteriormente, não excluir sem substitutos. |
| `requirements.txt` | Preservar. Declara PySide6, Nuitka, zstandard e pypdf. Dependência de build não é automaticamente dependência inútil. |
| `features/editor_novo/main.py` | Entrada independente de diagnóstico do editor; não alcançada pela entrada do workspace por definição. Manter e atualizar imports/documentação. |
| `features/editor_novo/test_canvas_edit.py`, `test_draw_shapes.py`, `test_layers.py`, `test_window_lifecycle.py` | Preservar os testes; ajustar imports e caminhos de mocks ao mover os módulos. |
| `tests/test_pdf_links.py` | Testa injeção de links em PDF, independente das interfaces antigas. |
| `features/workspace_novo/THIRD_PARTY_LICENSES.md` | Preservar avisos e pendências; documento atual é introdutório e não comprova prontidão de distribuição. |
| `.gitignore`, `.continueignore`, `.codex`, `.agents/`, `.git/` | Metadados/configuração de desenvolvimento e histórico. Não são lixo por não integrarem o runtime. |

## Etapa 1 — Limpeza controlada

### Implementações fora do fluxo novo

| Alvo | Evidência | Condição para remover |
| --- | --- | --- |
| `features/editor/` (`canvas_items.py`, `editor_window.py`, `properties.py`) | Nenhum desses módulos pertence aos 40 alcançáveis; usados pelo workspace antigo e por testes históricos. | Substituir entrada raiz e retirar/adaptar consumidores antigos na mesma entrega. |
| `features/workspace/` (`controls_panel.py`, `export_models_dialog.py`, `import_models_dialog.py`, `main_window.py`) | O workspace novo tem implementações próprias; ainda é o destino de `main.py` da raiz. | Trocar o import da entrada antes da exclusão. |
| `features/spreadsheet/` (`clipboard.py`, `delegates.py`, `table_panel.py`) | A aplicação nova usa exclusivamente `spreadsheet_novo`. | Retirar consumidores antigos e confirmar busca global de imports. |
| `features/editor_qml/` | Não integra o fechamento do workspace novo; a entrada antiga ainda oferece sua sessão. | Revisar e reaproveitar cobertura de testes compartilhados antes da remoção integral. |

O alvo QML abrange suas implementações Python (`main.py`, `session.py`, `bridge.py`, `canvas_layers.py`, `canvas_text_editor.py`, `layer_paint_cache.py`, `preview_service.py`, `benchmark_canvas.py`), componentes `.qml`, `qmldir`, testes e relatórios. A pasta inteira é candidata à retirada **somente depois da triagem abaixo**. Não substituir imports do QML por imports Widgets mecanicamente: APIs e comportamento são diferentes.

### Testes dentro do QML que não devem desaparecer sem revisão

- `tests/test_end_to_end.py`: contém casos de modelos reais, PDF por item/agrupado, links, imposição, comparação rasterizada e falhas de geração. Transportar os cenários aplicáveis ao gerador/workspace atual para `tests/`, removendo dependência da bridge QML e do workspace antigo.
- `tests/test_shapes_outline.py`: reaproveitar cenários de renderização, ordem mista, cache e links; separar dos testes específicos da bridge e do editor de texto QML.
- `tests/test_completion.py`: revisar principalmente histórico sem alteração e conclusão/erro do fluxo de geração. Os casos de escolha entre editores não são mais requisitos do produto.
- Demais testes QML: classificar antes de apagar. Testes de controles, transformações, camada de pintura e bridge exclusivamente QML podem sair junto com a implementação; cenários do backend compartilhado devem ser transferidos quando não cobertos.

### Documentação histórica

Arquivar em `docs/historico/`, em vez de apagar decisões ou instruções ainda úteis:

- `README_legado.md`, `novo_editor.md`, `PLANO_MODERNIZACAO_INTERFACE.md`.
- `features/workspace_novo/PLANO_REDESIGN_WORKSPACE.md`.
- Os Markdown de `features/editor_qml/` e `BENCHMARK_RESULTADOS.json`.

O arquivo `novo_editor.md` chama o QML de “novo editor” e descreve um estágio antigo. Deve deixar de ser orientação ativa. O README raiz será reescrito na etapa 3, e os README do workspace/editor serão atualizados na etapa 2. Extrair pendências ainda aplicáveis dos relatórios antes de arquivar; checkbox histórica concluída não prova que o produto atual esteja validado.

### Conteúdo local não versionado: não confundir com legado removível

- `models/` contém `teste`, `teste2`, `teste3` e não tem arquivos rastreados pelo Git nesta revisão. **Preservar integralmente** até inventário de JSON/assets e cópia de segurança: estar ignorado pelo Git significa que a branch histórica não protege esses dados.
- `.venv/` é o ambiente validado. Preservar durante a migração. `venv/` também existe e é referenciado por `script_appimage.sh`; não removê-lo antes de corrigir e validar esse script.
- `.flatpak-builder/`, `build-dir/`, `repo/`, `Linux_Projeto_COMSOC.flatpak` e `Projeto_ComSoc.AppImage` são artefatos locais de distribuição. Não fazem parte do grafo do aplicativo, mas podem ser a única cópia de um instalador útil. Candidatos à limpeza local após confirmar recuperação/backup; não são alvo desta entrega.
- `__pycache__/` e `.pytest_cache/` são caches descartáveis. A limpeza deve atingir apenas diretórios de cache identificados, sem entrar em modelos/ambientes por exclusão ampla.

### Ordem executável

1. [x] Registrar baseline de modelos de teste em cópias isoladas, com imagens de prévia e hashes dos originais. Artefatos: `/tmp/fornax-transition-baseline`.
2. [x] Triar testes e documentos QML. A cobertura compartilhada de PDF, links, cache, imposição e falhas foi transferida para `tests/test_rendering_pipeline.py`; os casos restantes eram específicos do editor descartado ou já estão cobertos pelos testes Widgets.
3. [x] Substituir a entrada raiz pelo fluxo de `workspace_novo/main.py`.
4. [x] Retirar as três interfaces antigas e o QML após resolver seus consumidores. Backup temporário: `/tmp/fornax-legacy-backup-20260913`.
5. [x] Buscar referências residuais e validar entrada raiz, editor e geração. Resultado: 23 testes aprovados e importação raiz apontando para `features.workspace_novo.main_window`.
6. [x] Registrar commit e resultado antes das renomeações. Checkpoint: `51fd2fa`.

## Etapa 2 — Diretórios oficiais

| Origem | Destino |
| --- | --- |
| `features/workspace_novo/` | `features/workspace/` |
| `features/editor_novo/` | `features/editor/` |
| `features/spreadsheet_novo/` | `features/spreadsheet/` |
| Documentos históricos listados acima | `docs/historico/` |
| `features/workspace_novo/THIRD_PARTY_LICENSES.md` | `docs/THIRD_PARTY_LICENSES.md` (atualizar qualquer acesso/documentação) |

Manter `core/`, `shared/`, `features/generator/` e `features/preview/` em seus locais nesta fase. Separar futuramente recursos visuais compartilhados em `shared/` pode melhorar a organização, mas não é necessário para oficializar o aplicativo. Não combinar essa mudança com reescrita do motor gráfico.

- [x] Mover as pastas somente após retirar os destinos legados, sem mesclar árvores antigas e novas.
- [x] Corrigir todos os imports absolutos, inclusive em testes e strings de `unittest.mock.patch`.
- [x] Corrigir o caminho literal dos ícones na tabela; manter os SVG junto dos módulos que os usam.
- [x] Manter uma entrada raiz oficial e preservar a entrada independente do editor para diagnóstico.
- [x] Atualizar comandos nos README e testes transferidos sem alterar documentos históricos.
- [x] Validar ausência de dependência de pastas `_novo` e QML com busca de referências, compilação e execução.

## Etapa 3 — Identidade, compatibilidade e validação

### Marca visível

- [x] Atualizar título do workspace em `main_window.py`, título do editor, descrição do executável de diagnóstico, menu/diálogo Sobre em `frontend.py`.
- [x] Atualizar mensagens de importação, nome sugerido `Modelos_ProjetoComSoc.zip`, dica de saída e nome de lote `Projeto COMSOC_<timestamp>` no workspace.
- [x] Reescrever README raiz com nome, proposta e comandos oficiais; atualizar documentação operacional.
- [ ] Definir ícones finais e verificar os três formatos existentes de distribuição.

Usar FORNAX Forge como nome curto. Descrição longa em português na interface/documentação em português; versão inglesa na apresentação em inglês. O nome não exige novo formato de documento.

### Identidade técnica e dados — não fazer substituição cega

`core/paths.py` usa atualmente `com.leobelisario.ProjetoComSoc` no Linux/macOS e `ProjetoComSoc` no Windows. `workspace_novo/main_window.py` usa `QSettings("Projeto ComSoc", "MainApp")`. Trocar essas strings sem migração faz biblioteca e preferências parecerem perdidas.

- [x] Definir identificador técnico FORNAX estável antes do novo pacote; foi adotado `com.leobelisario.FornaxForge`, preservando o namespace técnico já controlado pelo projeto.
- [x] Migrar por cópia verificável, mantendo a origem; em conflito, não sobrescrever silenciosamente modelos de mesmo nome/slug.
- [x] Migrar preferências relevantes (tema, geometria, divisão, configurações) antes de salvar no novo namespace.
- [x] Considerar os caminhos por sistema e o isolamento Flatpak: a migração nativa cobre Windows, Linux e macOS; o README orienta exportação/importação para sandboxes Flatpak isoladas.
- [x] Preservar `template_v3.json`, assets, chaves de dados e conversões existentes. Rebranding não implica alterar IDs internos dos documentos.
- [x] Não renomear automaticamente pastas de saída já geradas pelo usuário.

### Empacotamento

Preservar e corrigir `script_nuitka.py`, `script_appimage.sh` e `com.leobelisario.ProjetoComSoc.yaml`.

- Nuitka usa `main.py`, inclui `features`, `core`, `shared` e pypdf; atualizar nomes de executável, app/DMG e inclusão explícita dos SVG usados por caminho. A inclusão de pacotes Python não comprova que recursos não Python estarão no produto final.
- AppImage referencia `build/main.dist`, `venv/lib/python3.13/site-packages/PySide6`, executável `COMSOC_OFICIAL` e ícone vazio criado com `touch`. Harmonizar com a saída real do Nuitka e os ícones finais antes de usá-lo para distribuição.
- Flatpak copia a árvore `features` inteira e usa o main raiz. Atualizar manifesto/nome do arquivo, app-id, comando, desktop entry, ícone e permissão da pasta de saída de forma coerente.
- Separar requisitos de desenvolvimento/build de runtime se útil, sem retirar PySide6, seus componentes necessários (incluindo SVG), shiboken6 associado ou pypdf. Não remover componentes Qt por associação superficial com QML sem verificar o pacote gerado.
- Completar inventário e avisos de terceiros do pacote efetivamente distribuído; o arquivo atual registra essa pendência. Não declarar conformidade de licenças ou prontidão de publicação apenas com este plano.

### Critérios de aceite

- [ ] Instalação em ambiente limpo inicia pelo `main.py` raiz e não importa implementações removidas.
- [ ] Novo modelo; abrir/salvar/reabrir; duplicar/renomear/excluir; importar/exportar biblioteca, com cópias de teste.
- [ ] Tabela: colagem externa, edição da célula e barra de conteúdo, Enter/Shift+Enter, formatação, altura, filtros/seleção e quantidades.
- [ ] Editor: texto rico e placeholders, imagens/assinaturas, formas e quatro cantos, alpha/contorno, plano de fundo, links, guias/régua, camadas e undo/redo.
- [ ] Workspace oculto durante edição, retorno/cancelamento sem perda de dados, geometria, minimizar/restaurar e atualização da prévia após salvar.
- [ ] Comparação de prévias antes/depois com mesmas fontes e parâmetros; PNG, PDF por item e agrupado, links, transparência, tamanho físico e imposição.
- [ ] Falhas de leitura/gravação e geração não informam sucesso indevido e liberam corretamente a interface.
- [ ] Dados e preferências migrados sem apagar fontes; repetir migração não duplica ou sobrescreve dados silenciosamente.
- [ ] Testes nativos em Windows, Linux e macOS, incluindo tela cheia, monitores e controles de janela. Testes offscreen não verificam comportamento de gerenciador de janelas.
- [ ] Pacote instalado encontra SVG, fontes disponíveis, plugins de imagem e dados, sem depender do checkout ou dos ambientes de desenvolvimento.
- [ ] Conferir impressão física/escala com o fluxo de PDF e imposição antes da distribuição.

## Evidência inicial e limites

Comando executado nesta análise:

```sh
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest features.editor_novo.test_window_lifecycle features.editor_novo.test_draw_shapes features.editor_novo.test_layers features.editor_novo.test_canvas_edit tests.test_pdf_links
```

Resultado: **19 testes aprovados**. PyPDF disponível no `.venv`: **6.14.2**. A execução inicial com `python` global passou nos 17 testes do editor, mas falhou ao importar o teste de PDF porque esse interpretador não tem `pypdf`; não confundir isso com regressão do projeto. Usar `.venv/bin/python` como referência até preparar novo ambiente reproduzível.

Essa validação não cobre todos os fluxos do workspace, impressão física, instalação de pacotes, migração de dados ou macOS/Windows. Não foram apagados arquivos para “provar” o grafo. A equivalência final exige os critérios acima.

## Registro e retomada

| Data | Trabalho | Resultado | Próxima ação |
| --- | --- | --- | --- |
| 13/09/2026 | Mapa estático de 40 módulos, conferência de recursos, caminhos, distribuição e testes | Plano criado; 19 testes aprovados no `.venv`; nenhum código removido | Iniciar etapa 1 pelo baseline isolado e pela triagem de cobertura QML |
| 13/09/2026 | Etapa 1: baseline, cobertura compartilhada, troca da entrada e retirada das interfaces antigas | 23 testes aprovados; prévias e hashes de `teste`, `teste2` e `teste3` idênticos; legado recuperável em `/tmp/fornax-legacy-backup-20260913` | Registrar checkpoint Git e iniciar as renomeações oficiais |
| 13/09/2026 | Etapa 2: `workspace_novo`, `editor_novo` e `spreadsheet_novo` oficializados sem os sufixos | Imports, mocks, ícones e README corrigidos; 23 testes aprovados; editor independente aprovado em modo offscreen | Registrar checkpoint Git e iniciar identidade/migração da Etapa 3 |
| 13/09/2026 | Etapa 3: marca visível, identificador técnico, migração conservadora e nomes de distribuição | Entrada oficial exibe FORNAX Forge; dados e preferências legados são copiados sem sobrescrita; manifesto/scripts renomeados; 25 testes aprovados; hashes dos modelos reais preservados | Criar os ícones definitivos e validar pacotes/controles nativamente em Windows, Linux e macOS antes da publicação |

Ao retomar, ler este documento e o diff atual, confirmar branch e commit, executar somente o próximo item pendente. Se o código mudou desde `5f0199f`, atualizar o mapa antes de excluir. A limpeza de arquivos locais não versionados permanece separada da limpeza de código rastreado.
