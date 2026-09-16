# Modelos com frente e verso — plano de implementação

Estado: Etapas 0 e 1 concluídas; Etapa 2 aguardando início.
Base: inspeção do código em 15/09/2026.
Escopo: FORNAX Forge, editor Qt Widgets atual, uma ou duas páginas por modelo.

## 1. Objetivo e limites

Permitir documentos como diplomas e históricos escolares com frente e verso, preservando a identidade entre editor, prévia e material exportado e a responsividade atual.

Regras confirmadas:

- Modelos existentes continuam funcionando com uma página.
- Um modelo pode ter uma ou duas páginas; não criar automaticamente um verso nos modelos existentes.
- As duas páginas compartilham dimensões físicas e dimensões do canvas.
- Cada página possui suas próprias camadas, conteúdo e plano de fundo editável.
- O plano de fundo acompanha o documento, permanece na última posição das camadas e não pode ser movido ou redimensionado individualmente.
- A tabela reúne os campos das duas páginas. O mesmo placeholder nas duas páginas utiliza o mesmo valor da linha.
- Cada linha representa um documento completo; a coluna Cópias multiplica documentos completos.
- PNG: gerar uma imagem para cada página, com sufixos `_pag1` e `_pag2` nos modelos de duas páginas.
- PDF por item, sem imposição: um PDF de duas páginas por documento/cópia.
- PDF agrupado, sem imposição: frente e verso do primeiro documento, frente e verso do segundo, e assim por diante.
- Editor e prévia permitem alternar o lado visualizado.
- Continuar usando o motor gráfico atual, inclusive os cálculos compartilhados de texto, formas e links.

Não fazem parte deste escopo: mais de duas páginas, tamanhos diferentes por página, páginas condicionais por linha, editor em outra tecnologia ou controle nativo de impressoras. O preparo das folhas para impressão frente e verso faz parte do plano, mas depende das decisões abaixo.

## 2. Termos que o código e a interface precisam distinguir

| Termo | Significado |
| --- | --- |
| Registro | Uma linha de origem da tabela |
| Documento/cópia | Uma ocorrência produzida após aplicar Cópias |
| Página do modelo | Frente ou verso de um documento |
| Folha física | Papel que pode acomodar vários documentos |
| Face da folha | Frente ou verso desse papel; corresponde a uma página do PDF imposto |
| Imposição | Distribuição dos documentos sobre a folha de impressão |

Exemplo sem imposição: duas linhas com Cópias 2 e 1 produzem três documentos. Se o modelo tiver duas páginas, são seis PNGs, três PDFs de duas páginas ou um PDF agrupado de seis páginas.

## 3. Decisões de produto antes das etapas dependentes

As propostas abaixo orientam o desenvolvimento, mas não devem ser apresentadas como decisões já aprovadas. Registrar a decisão final nesta seção antes de implementar a parte correspondente.

| Decisão | Proposta | Necessária antes de |
| --- | --- | --- |
| Criar/remover verso | **Definida:** novo modelo começa com frente; ação explícita adiciona verso branco. Remover verso pede confirmação se houver conteúdo e pode ser desfeito. | Etapa 4 |
| Identidade das páginas | **Definida:** IDs estáveis `front`/`back` e ordem fixa frente → verso. Sem renomear/reordenar páginas nesta primeira versão. | Etapa 1 |
| Guias | **Definida:** posições pertencem a cada página; visibilidade e bloqueio são comuns ao documento/editor. Trocar de página não cria histórico. | Etapa 4 |
| Histórico entre páginas | **Definida:** histórico único do documento. Se desfazer alterar a outra página, mostrá-la para tornar o efeito visível; a navegação em si não gera histórico. | Etapa 4 |
| Campos removidos | **Definida:** manter a coluna e os dados como inativos durante a sessão, excluí-los da geração e exigir ação explícita antes do descarte. | Etapa 5 |
| Verso vazio | **Definida:** se o verso existe, exportá-lo mesmo vazio, mantendo a ordem do documento. | Etapa 6 |
| Imposição frente e verso | Parear faces da mesma folha e reposicionar os itens no verso conforme a virada pela borda longa/curta. Não inverter o texto nem espelhar os gráficos. | Etapa 7 |
| PDF por item com imposição | Proposta: produzir um PDF por folha física, com suas duas faces, e explicar essa mudança contextual na interface. Confirmar se é preferível bloquear essa combinação ou criar outra opção. | Etapa 7 |
| Contador da prévia imposta | Proposta: contar folhas físicas e selecionar a face separadamente; exportação conta páginas PDF. | Etapa 8 |
| Impressão manual | Primeira versão gera faces intercaladas, apropriadas ao duplex; exportar todas as frentes e depois todos os versos fica fora do escopo inicial. | Etapa 7 |

O ajuste pela borda longa/curta exige prova física em retrato e paisagem. Arquivos corretos não garantem as configurações do driver nem compensam desalinhamentos mecânicos da impressora.

## 4. Mapa do código e pontos de atenção confirmados

| Área | Arquivos e pontos inspecionados | Limitação atual / cuidado |
| --- | --- | --- |
| Modelo no editor | `features/editor/editor_window.py`: `get_current_scene_state`, `apply_scene_state`, `load_from_json`, `export_to_json` | Captura/restaura uma cena; salvar deve incluir a página inativa. |
| Histórico | Mesmo arquivo: `save_snapshot`, `_restore_history_state`; `core/history_manager.py` | Estado de documento deve abranger as duas páginas; seleção e painéis não viram ações. |
| Assets | Editor: `_collect_used_asset_paths`, `_cleanup_unused_assets_on_close`, `_rewrite_state_asset_paths` | Varredura atual percorre coleções da raiz. Sem revisão, pode excluir imagens utilizadas somente no verso. |
| Camadas | `core/document_layers.py`, `features/editor/canvas_items.py` | Ordem e IDs precisam ser interpretados por página. `object_id` é atualmente derivado de tipo/layer_id ao salvar. |
| Estilos e texto | `core/object_style.py`, `core/text_layout.py`, `features/editor/canvas_edit.py` | Preservar texto rico, alinhamento, métricas tipográficas, contornos e geometria. |
| Fontes | `core/font_utils.py`: `template_font_families` | Atualmente examina `boxes` da raiz; precisa incluir ambas as páginas. |
| Renderização | `features/generator/renderer.py`: `NativeRenderer` | Um template, uma base estática; requer contexto de página explícito e cache isolado. |
| Cache | `core/render_cache.py`; miniatura `thumbnail_raw.png` | Há premissas de fundo único e caminhos únicos de miniatura; revisar chaves e limpeza. |
| Workspace/biblioteca | `features/workspace/main_window.py` | Carregamento, edição, fontes, links, assinaturas, colunas, miniaturas, importação e atualização de metadados percorrem a raiz. |
| Cópias/dados | Workspace: `_scrape_table_data`, `_get_row_data_rich`, `_visible_preview_rows` | Cópias já são expandidas; não multiplicar novamente ao adicionar páginas. Preservar mapeamento à linha de origem. |
| Folhas | `features/generator/production_plan.py`, `imposition.py` | Plano atual divide uma sequência de itens pela capacidade; não representa pares frente/verso. |
| Prévia | `features/preview/preview_panel.py`, `sheet_preview_worker.py`; métodos `_on_preview_*` do workspace | Estado atual inclui item/folha e índice; incluir página/face e invalidar resultados antigos. |
| Exportação | `features/generator/manager.py`, `workers.py` | Uma tarefa por item; PDF agrupado usa imagens temporárias e ordenação por índices. Links são associados ao índice do cartão. |
| Nomes | `core/naming_engine.py`, `core/output_folders.py` | Sufixo de página entra no arquivo; contador de Forjas continua por geração, não por página. |
| Distribuição de modelos | Workspace: abrir/duplicar/renomear/importar/exportar; `core/paths.py` | Diversos consumidores procuram `template_v3.json`; mudança do formato exige leitura centralizada. |
| Tradução | `core/i18n.py`, `assets/translations/` | Novos controles e mensagens devem existir em português, inglês e espanhol. |

## 5. Estrutura técnica proposta

Criar uma camada central de leitura/normalização/validação do documento, sugerida como `core/model_document.py`. Evitar que cada tela implemente sua própria migração.

Estrutura conceitual, não um schema final:

```text
Documento
  schema_version
  nome e configurações de exportação
  dimensões comuns (canvas e mm)
  ordem global de campos
  pages[1..2]
    page_id estável
    boxes, images, signatures, shapes
    layer_order
    guias da página
```

- Manter as coleções gráficas atuais dentro de cada página para reaproveitar o renderizador.
- Não manter duas versões editáveis das mesmas camadas (na raiz e dentro de pages).
- Criar um adaptador que combine dimensões/metadados comuns e conteúdo de uma página para os consumidores gráficos atuais. Não permitir mutação acidental do documento pelo adaptador.
- Identificar objetos por `(page_id, object_id)` ou usar IDs únicos no documento. Índice de página e nome de camada não são identidade estável.
- Caminhos dos assets permanecem relativos à pasta do modelo; a resolução absoluta acontece no carregamento/contexto do renderizador.
- Identificadores e placeholders são independentes do idioma da interface.
- Preferências de painel, seleção, zoom e página ativa ficam fora do estado usado para detectar alterações e alimentar undo/redo.

### Formato e compatibilidade

Decisão técnica adotada: novo schema versionado e novo arquivo `template_v4.json`, com leitor central que reconheça v4 e o atual `template_v3.json`. A Etapa 1 deve confirmar o inventário de leitores antes da primeira gravação.

- Converter v3 em uma página apenas em memória ao abrir; não modificar modelos só por visualizá-los.
- No primeiro salvamento convertido, preservar cópia recuperável do modelo anterior e publicar o novo JSON atomicamente.
- Se coexistirem arquivos v3/v4, definir uma única autoridade: v4 válido tem precedência; falha no v4 gera erro explícito, nunca abertura silenciosa de um v3 desatualizado.
- Backup não é segundo modelo nem fonte para edição automática. Duplicação e ZIP precisam seguir a mesma política.
- Versões antigas do programa não poderão editar documentos de duas páginas; documentar essa limitação, sem prometer compatibilidade de ida e volta.
- Testar falhas de gravação e diretórios sem permissão antes de habilitar o novo salvamento na interface.

## 6. Etapas de execução

Riscos: baixo = interface/documentação com impacto localizado; médio = mudança compartilhada reversível; alto = várias áreas ou desempenho; crítico = risco de perda de conteúdo, arquivos incorretos ou pares frente/verso trocados.

### Etapa 0 — Referência verificável e decisões iniciais

**Risco: baixo. Dependência: nenhuma.**

Objetivo: poder demonstrar que modelos atuais continuam corretos.

- [x] Registrar estado do repositório e separar alterações preexistentes; não sobrescrevê-las.
- [x] Criar cópias de modelos reais representativos para testes, sem alterar originais ou dados pessoais.
- [x] Registrar PNG/PDF de referência, dimensões físicas, links, campos e hashes de assets.
- [x] Medir abertura, movimentação de item, renderização de prévia e colagem de 500 linhas na mesma máquina.
- [x] Registrar tempo de geração e pico de memória para lote representativo; incluir assinatura e link.
- [x] Fechar as decisões necessárias às etapas 1–5 e registrar as demais como pendentes.

**Saída:** fixtures e medições repetíveis, regras iniciais registradas. Não inventar metas absolutas antes de medir.

### Etapa 1 — Contrato do documento e leitura compatível

**Risco: alto. Dependência: 0.**

Objetivo: representar uma ou duas páginas sem alterar a aparência de uma página existente.

- [x] Implementar schema, normalizador, validações e adaptador de página centralizados.
- [x] Definir versão, precedência de arquivos, IDs e compatibilidade.
- [x] Validar cardinalidade 1–2, dimensões válidas e comuns, IDs e ordem de camadas.
- [x] Converter estruturas legadas (inclusive fundo antigo) sem dupla pintura nem transformação gráfica indevida.
- [x] Testar normalização idempotente e sem escrita na origem.
- [x] Modelos inválidos ou versões desconhecidas devem gerar mensagens claras, sem truncar páginas silenciosamente.

**Cuidados:** não recalcular coordenadas, DPI, estilos ou IDs a cada leitura. Não usar textos traduzidos como chave.

**Saída:** v3 e documento novo de uma página entregam os mesmos dados gráficos ao renderizador; duas páginas são válidas e isoladas.

### Etapa 2 — Persistência, assets e biblioteca

**Risco: crítico. Dependência: 1.**

Objetivo: salvar e transportar o documento inteiro sem perder o verso nem arquivos usados por ele.

- [x] Implementar leitura/escrita central e publicação atômica do JSON, com plano de recuperação.
- [x] Adaptar importação de assets e reescrita de caminhos em todas as páginas e estados históricos.
- [x] Reescrever coleta e limpeza de assets para incluir as duas páginas, assets compartilhados e referências que precisam sobreviver à recuperação/undo.
- [x] Nunca remover assets com base apenas na cena visível; suspender limpeza se não for possível determinar todas as referências.
- [x] Adaptar biblioteca, modelo inicial, abrir, duplicar, renomear, importar/exportar ZIP e gravação das preferências de exportação.
- [x] Preservar nome, ordem de campos, predefinição, formato e demais metadados suportados.
- [x] Testar fechar sem salvar, salvar como cópia, remover verso e desfazer, interromper salvamento e abrir após falha.

**Cuidados:** JSON atômico sozinho não garante a integridade dos assets. Copiar recursos antes de publicar referências; só limpar depois de confirmar o estado salvo e a política de recuperação.

**Saída:** salvar/reabrir e exportar/importar preservam conteúdo e assets das duas páginas. Nenhum asset exclusivo do verso é apagado.

### Etapa 3 — Renderização e caches por página

**Risco: alto. Dependências: 1–2.**

Objetivo: pintar qualquer página usando a lógica gráfica que já funciona.

- [x] Dar contexto explícito de página ao renderizador ou instanciar renderizadores por página via adaptador.
- [x] Isolar bases estáticas, miniaturas, proxies e cache de imagens conforme a página e a revisão relevante.
- [x] Incluir página, revisão do documento, dados e configurações relevantes nas chaves dos resultados de prévia.
- [x] Revisar `infer_model_dir` e limpeza de proxies para não invalidar recursos da outra página.
- [x] Coletar fontes, links e assets das duas páginas sem ignorar texto rico.
- [x] Usar QImage nos workers; manter QPixmap e widgets na thread da interface.
- [x] Comparar renderização antiga e nova de uma página com a referência; testar frente/verso graficamente distintos.

**Cuidados:** não alterar as métricas tipográficas para implementar páginas. Não compartilhar caches mutáveis entre workers sem estratégia explícita. Não pré-renderizar o lote inteiro na interface.

**Saída:** cada lado produz a imagem correta e links próprios, sem mistura de cache e com custos de uma página preservados.

### Etapa 4 — Editor, navegação e histórico do documento

**Risco: alto. Dependências: 1–3.**

Objetivo: editar frente e verso com a mesma fluidez do editor atual.

- [x] Acrescentar navegação compacta de páginas e ação de adicionar/remover verso conforme decisões da seção 3.
- [x] Manter dados de ambas as páginas; montar no canvas somente a ativa como abordagem inicial.
- [x] Antes de alternar, concluir edição de texto/gesto ativo e guardar o estado atual sem criar snapshot de navegação.
- [x] Ao alternar, atualizar camadas, propriedades, seleção, fundo, guias e réguas; impedir callbacks de montagem de criarem alterações falsas.
- [x] Separar captura da cena da captura do documento; salvar sempre o documento completo.
- [x] Aplicar dimensões comuns aos dois fundos sem escalar objetos inadvertidamente; uma alteração dimensional é uma ação de histórico.
- [x] Histórico único com limite de memória: mudanças de conteúdo, dimensões e criação/remoção do verso são ações; troca de página, seleção e recolhimento de painel não são.
- [x] Preservar seleção por identidade quando o objeto ainda existe e definir a seleção quando a restauração exigir outra página.
- [x] Confirmar que desfazer e refazer recuperam o conteúdo do verso removido, inclusive imagens.

**Cuidados:** uma troca de página não pode parecer modificação ao fechar. Evitar custo duplo de QGraphicsScene ativa, renderização geral a cada clique e snapshots desnecessários.

**Saída:** editar A → editar B → desfazer/refazer → salvar/reabrir preserva ambas. Arraste e digitação não sofrem regressão perceptível em relação à etapa 0.

### Etapa 5 — Tabela, placeholders, assinaturas e links

**Risco: alto. Dependências: 1, 2 e 4.**

Objetivo: uma tabela alimentar o documento completo.

- [x] Extrair a união dos placeholders das duas páginas, sem duplicar nomes idênticos.
- [x] Manter ordem global: preservar ordem existente e acrescentar campos novos deterministicamente.
- [x] Incluir campos de links e assinatura usados somente no verso; revisar colisões de nomes de camadas entre páginas.
- [x] Manter a regra de assinatura por registro nas duas páginas; exceções exigem definição adicional.
- [x] Atualizar campos ao salvar e ao criar/remover verso, preservando conteúdo já digitado conforme política aprovada.
- [x] Garantir Cópias = N documentos completos, com tratamento atual para zero e dados inválidos.
- [x] Testar campos só no verso, campo repetido, HTML rico, nome com acentos e link em forma.

**Cuidados:** não mudar IDs de campo quando a interface troca de idioma. Não reconstruir a tabela por célula durante Ctrl+V nem disparar renderização completa para cada alteração.

**Saída:** cada página recebe os valores corretos da mesma linha e a planilha mantém dados, ordem e desempenho.

### Etapa 6 — Exportação direta sem imposição

**Risco: crítico. Dependências: 2, 3 e 5.**

Objetivo: concluir PNG, PDF por item e PDF agrupado de documentos com duas páginas.

- [x] Definir tarefa identificada por registro de origem, cópia e página; reservar o nome-base uma única vez por documento/cópia.
- [x] Acrescentar `_pag1`/`_pag2` antes da extensão; manter nomenclatura anterior para uma página.
- [x] PNG: dois arquivos por documento de duas páginas, incluindo verso vazio se existir.
- [x] PDF por item: criar o writer uma vez por documento e adicionar ambas as páginas com dimensões corretas.
- [x] PDF agrupado: montar por chave numérica (documento/cópia/página), nunca pela ordem de conclusão dos workers ou nome alfabético.
- [x] Reassociar links a cada página PDF, inclusive na montagem híbrida; testar rotações e regiões clicáveis.
- [x] Definir progresso sem confundir documentos com páginas; total final e mensagens devem concordar.
- [x] Tratar cancelamento, erro parcial e limpeza temporária sem anunciar sucesso de um PDF incompleto.

**Cuidados:** não gerar nomes-base diferentes para frente/verso, duplicar Cópias ou anexar links do primeiro lado ao segundo. Uma Forja continua correspondendo a uma execução completa.

**Saída:** exemplo da seção 2 comprovado, ordem estável mesmo com workers finalizando fora de ordem e nenhuma regressão em documentos de uma página.

### Etapa 7 — Imposição frente e verso

**Risco: crítico. Dependências: 3, 5, 6 e decisões de impressão da seção 3.**

Objetivo: fazer as duas faces da folha corresponderem aos mesmos documentos após corte e virada.

- [x] Estender o plano compartilhado de produção para representar documento/cópia, folha física, face e posição na malha.
- [x] Calcular capacidade por documento; frente/verso ocupam o mesmo par de posições físicas, não duas vagas independentes na frente.
- [x] Aplicar transformação das posições do verso para A4 alimentado de pé e virada lateral, respeitando a orientação automática da imposição sem espelhar conteúdo.
- [x] Preservar posições vazias na última folha incompleta; não compactar o verso independentemente.
- [x] Aplicar dimensões, margens, sangrado, marcas de corte, orientação e links às duas faces.
- [x] Implementar formatos de saída conforme a política aprovada e mensagens contextuais que esclareçam PDF por item/folha.
- [x] Testar malhas simétricas e assimétricas, capacidade 1, folha incompleta e rotação automática retrato/paisagem. Outras bordas de virada ficaram fora do contrato aprovado.
- [x] Gerar prova com identificadores A/B/C e marcas de orientação para inspeção física.

**Cuidados:** não alimentar o agrupador atual com uma lista achatada de páginas; isso pode colocar frente e verso lado a lado na mesma face. Esta etapa não está concluída enquanto a correspondência física não for validada.

**Saída:** cada documento conserva seu verso após impressão e corte; prévia e exportação usam exatamente o mesmo plano.

### Etapa 8 — Prévia ativa e sincronização com a tabela

**Risco: alto. Dependências: 3, 5, 6 e 7 para modo imposto.**

Objetivo: visualizar lado do item e face da folha final sem regressão de colagem/navegação.

- [x] Separar estado de registro/documento, página do modelo, folha física e face visualizada.
- [x] Adicionar seletor discreto de frente/verso, disponível somente quando o modelo tiver duas páginas.
- [x] Manter seleção do registro ao trocar lado; ao mudar item → folha, mostrar a folha correspondente à cópia/registro atual.
- [x] Ao voltar folha → item, selecionar o primeiro documento presente nela e manter o lado correspondente conforme regra aprovada.
- [x] Tornar explícito qual cópia é usada quando um registro tem várias cópias; preservar mapeamento com linhas visíveis/filtradas.
- [x] Renderizar primeiro o resultado solicitado; restante em segundo plano, com cancelamento e cache limitado.
- [x] Exibir mensagem de carregamento quando necessário; descartar respostas de modelo, lado, dados ou predefinição antigos.
- [x] Invalidar a biblioteca/prévia após salvar qualquer página, mesmo que a frente não tenha mudado.
- [x] Miniatura da biblioteca usa a frente; não sobrescrever a capa com o último lado editado.

**Cuidados:** não gerar todos os versos ao colar dados. Não armazenar milhares de QImages de alta resolução em memória. Preservar largura fixa e centralização da navegação atual.

**Saída:** navegar item/folha/frente/verso mostra o conteúdo esperado e continua responsivo em lotes grandes.

### Etapa 9 — Interface completa, idiomas e documentação

**Risco: médio. Dependências: 4–8.**

Objetivo: entregar todos os controles e mensagens com o padrão visual atual.

- [ ] Revisar estados indisponíveis, textos explicativos, confirmações de remoção e contadores.
- [ ] Usar ícones SVG existentes quando adequados; listar qualquer novo asset necessário sem recorrer a emojis de controle.
- [ ] Traduzir textos em `pt_BR`, `en_US`, `es_ES`; compilar catálogos e conferir placeholders.
- [ ] Revisar largura dos controles nos três idiomas, atalhos, foco e acessibilidade por teclado.
- [ ] Documentar arquivos gerados, Cópias, versão do modelo, recuperação e impressão duplex.
- [ ] Revisar todos os consumidores do arquivo antigo para encontrar acessos diretos esquecidos.

**Saída:** não há ações sem implementação, textos incompletos ou caminho que salve só a página ativa.

### Etapa 10 — Validação final e liberação

**Risco: crítico. Dependência: 0–9.**

Objetivo: provar integridade, desempenho e correspondência gráfica antes de disponibilizar a funcionalidade como concluída.

- [ ] Rodar suíte atual e testes novos focados nos riscos deste plano.
- [ ] Comparar modelos de referência de uma página; conferir texto rico, fonte Amiri e alinhamento vertical, transparência, contorno, imagens, assinaturas e links.
- [ ] Validar modelo de duas páginas com conteúdos distintos e com conteúdo compartilhado.
- [ ] Conferir PNG/PDF, dimensões em mm, metadados relevantes, ordem, links e contagens.
- [ ] Testar importação/exportação ZIP, modelo movido de pasta, duplicação, renomeação, gravação interrompida e recuperação.
- [ ] Repetir medições da etapa 0; investigar aumento de latência/memória sem justificativa antes de liberar.
- [ ] Testar rapidamente alternar lado/modelo/modo durante carregamento e encerrar com worker ativo.
- [ ] Validar fluxo visual em Linux, Windows e macOS; registrar plataforma realmente testada e pendências.
- [ ] Validar prova física duplex com o operador; registrar borda, orientação e resultado.
- [ ] Registrar limitações conhecidas, versão e caminho de retorno aos backups.

**Saída:** critérios atendidos com evidências. Teste headless não substitui inspeção visual nativa nem impressão física; itens dependentes do usuário permanecem explicitamente pendentes, sem marcar conclusão total.

## 7. Matriz mínima de aceitação

| Caso | Resultado esperado |
| --- | --- |
| Modelo antigo aberto sem salvar | Arquivo e assets originais intactos; aparência preservada |
| Editar apenas o verso, salvar e reabrir | Verso editado; frente preservada |
| Remover verso e desfazer | Conteúdo, ordem e assets restaurados |
| Alterar dimensões | Duas páginas e dois fundos atualizados; uma ação undo |
| Trocar página/recolher painel/selecionar item | Nenhuma ação gráfica adicionada ao histórico |
| Campo `{Nome}` nos dois lados | Uma coluna, mesmo valor aplicado aos dois lados |
| Link ou assinatura somente no verso | Detectado no workspace e gerado no verso correto |
| Duas linhas, cópias 2 e 1, duas páginas | Três documentos e seis páginas produzidas |
| Zero cópias | Nenhuma página daquele registro |
| PDF agrupado com conclusão fora de ordem | Sequência frente/verso por documento intacta |
| Modelo de uma página | Sem verso artificial e sem sufixo novo obrigatório |
| Três documentos, capacidade quatro, duplex | Duas faces; uma vaga vazia corretamente pareada |
| Trocar item/folha | Preservar correspondência entre linha, cópia, folha e face |
| Colar 500 linhas | Interface utilizável; prévia prioritária e geração de fundo controlada |
| Versão desconhecida ou arquivo corrompido | Mensagem explícita; sem sobrescrita ou conversão destrutiva |

## 8. Estratégia de avanço e recuperação

A sequência é 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Correções de regressão são feitas na etapa que as introduziu antes de avançar.

Durante etapas intermediárias, não disponibilizar exportação aparentemente completa que descarte o verso. Novos controles devem ser habilitados somente quando os caminhos correspondentes estiverem prontos. Modelos de uma página devem continuar utilizáveis durante a transição.

Não aplicar migração em massa da biblioteca. Trabalhar com cópias e converter no salvamento autorizado. Registrar pontos de recuperação antes de mudanças de schema/persistência; não apagar backups automaticamente nesta implementação.

## 9. Registro obrigatório de continuidade

Ao concluir uma etapa, marcar seus itens e registrar evidências abaixo. Se houver interrupção, anotar função/arquivo em andamento, próximo passo exato e testes pendentes. Não marcar a etapa inteira quando apenas a interface estiver concluída.

| Etapa | Estado | Arquivos alterados / evidência | Pendência / próximo passo |
| --- | --- | --- | --- |
| Planejamento | Concluído | Código mapeado; este documento criado | Fechar decisões da seção 3 conforme dependências |
| 0 | Concluída | Fixture versionada em `tests/fixtures/front_back_baseline`; capturador em `tools/capture_front_back_baseline.py`; relatório e cópias locais em `.validation/front_back_baseline/` | Iniciar contrato do documento na Etapa 1; decisões de imposição permanecem para a Etapa 7 |
| 1 | Concluída | Contrato em `core/model_document.py`; 14 testes em `tests/test_model_document.py`; renderização v3/adaptada idêntica | Integrar persistência e consumidores na Etapa 2; nenhum arquivo v4 é gravado ainda |
| 2 | Concluída | Persistência e recuperação em `core/model_document.py`; editor, workspace, biblioteca, ZIP, fontes e cache usam o leitor central; testes de duas páginas e assets | Iniciar isolamento de renderização e caches por página na Etapa 3 |
| 3 | Concluída | Renderizador aceita documento+página; caches e miniaturas isolados; workers sem caches mutáveis compartilhados; referência gráfica preservada | Iniciar navegação e histórico do documento na Etapa 4 |
| 4 | Concluída | Navegação compacta no rodapé; frente/verso com menus Limpar/Remover; cena ativa isolada; histórico único limitado a 64 MiB; persistência e reabertura das duas páginas; 25 testes do editor e 70 testes + 10 subtestes gerais aprovados | Iniciar união de placeholders, assinaturas e links na Etapa 5 |
| 5 | Concluída | União ordenada dos campos das páginas; links de texto/imagem/forma e assinaturas do verso integrados; placeholders Unicode; campos removidos preserváveis como inativos; linhas e Cópias preservadas | Etapa 6 concluída; manter as garantias ao implementar imposição |
| 6 | Concluída | PNG pag1/pag2; PDF por item multipágina; PDF agrupado ordenado; links por página; publicação temporária e limpeza de falhas; 83 testes + 10 subtestes aprovados | Alinhar decisões de imposição e iniciar a Etapa 7 |
| 7 | Implementação concluída; nova prova física pendente | Teste físico confirmou coincidência das posições. Em paisagem, o driver deixou o verso de cabeça para baixo; cada cartão e seus links agora recebem rotação interna de 180° sem mudar a vaga. Retrato mantém a inversão de colunas; paisagem mantém a inversão de linhas; rotação automática preservada | Reimprimir em duplex paisagem com virada lateral e confirmar orientação após o corte |
| 8 | Concluída | Estados independentes de item/cópia, página, folha e face; seletor Frente/Verso; transição item↔folha sincronizada; worker priorizado e cache limitado a 12 faces; respostas obsoletas descartadas; 90 testes + 10 subtestes e 4 testes do editor aprovados | Iniciar revisão de interface, idiomas e documentação da Etapa 9 |
| 9 | Não iniciada | — | — |
| 10 | Não iniciada | — | — |

### Correção arquitetural após a Etapa 8

O renderizador voltou a operar exclusivamente sobre uma prancheta completa, pelo mesmo contrato usado pelo editor legado. Ele não recebe mais o documento multipágina e não contém seleção interna de frente/verso. `renderers_for_document()` apenas extrai cada página como uma visão completa e cria uma instância comum de `NativeRenderer` para ela.

As propriedades físicas continuam no documento; camadas, guias e objetos permanecem isolados por página. Prévia, PNG e PDF consomem a mesma lista ordenada de renderizadores. Somente navegação, nomenclatura, sequência do PDF e imposição conhecem múltiplas páginas.

O editor ganhou clipboard de objetos com `Ctrl+C`/`Ctrl+V` entre páginas. A colagem cria identidades e camadas independentes, preserva posição e estilo e reutiliza o mesmo arquivo de asset. A limpeza existente só remove um asset quando ele não é referenciado por nenhuma página nem pelos documentos de recuperação.

Evidências: páginas idênticas produzem imagens pixel a pixel idênticas; cópia entre páginas preserva Amiri, tamanho e referência de imagem; 92 testes + 10 subtestes e 13 testes combinados do editor aprovados.

## 10. Evidências da Etapa 0

Captura realizada em Linux, Python 3.13.11 e Qt 6.11.0, na branch `novo_main`, commit-base `2f99296ffce510766b7669514e727eb4b1071f74`. O diretório `.validation/` está ignorado pelo Git e contém dados locais; não deve ser distribuído.

- Fixture sintética: 320 × 200 px, 80 × 50 mm, texto rico, duas formas, uma imagem, uma assinatura e um link.
- PNG de referência: 320 × 200 px; SHA-256 `31855e193b02d56eb6a5964d1bebb64ec37afae4d202bed7435537476b185691` na captura inicial.
- PDF de referência: uma página, 80,081 × 50,094 mm conforme leitura do PDF e um link; o hash pode variar por metadados.
- Primeira prévia: 13,394 ms; prévia aquecida mediana: 0,922 ms; abertura do editor: 20,599 ms.
- Duzentas movimentações programáticas na cena: mediana de 1,610 ms; cem edições sucessivas de texto: 17,692 ms.
- Colagem de 500 linhas: 25,151 ms; passagem programática por 500 registros: mediana de 0,614 ms.
- Renderização em memória de 100 documentos com assinatura e link: 91,329 ms nesta captura; pico do processo: 124.364 KiB. O lote não superou o pico já atingido pelas etapas anteriores do ensaio.
- Três modelos locais foram copiados com assets e hashes para a área ignorada; os originais em `models/` não foram alterados.

Esses números são referências comparativas desta máquina. A movimentação programática não mede pintura percebida na tela; fluidez visual, pico real da memória nativa do Qt e impressão continuam como validações manuais nas etapas correspondentes. Para repetir a captura:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen .venv/bin/python tools/capture_front_back_baseline.py
```

## 11. Evidências da Etapa 1

- `template_v3.json` é normalizado somente em memória como documento v4 de uma página.
- `template_v4.json` possui precedência quando os dois arquivos coexistem; um v4 inválido interrompe a abertura, sem retorno silencioso ao v3.
- O contrato aceita exatamente uma frente ou uma frente seguida de verso, com IDs `front` e `back`.
- Dimensões do canvas, dimensões físicas e estado global das guias pertencem ao documento; conteúdo, camadas e posições de guias pertencem à página.
- Objetos legados sem identidade recebem IDs determinísticos, sem alterar coordenadas, estilos ou ordem de pintura.
- Ordem de camadas v4 precisa corresponder aos objetos. O leitor mantém a tolerância histórica do v3 para ordens antigas incompletas.
- O adaptador entrega uma cópia isolada no formato gráfico atual. Alterá-la não modifica o documento nem a outra página.
- Fundo legado por imagem permanece no caminho histórico uma única vez; o fundo moderno em forma não é duplicado.
- A fixture de uma página apresentou imagem exatamente igual antes e depois do adaptador.
- Inventário confirmou acessos diretos ao arquivo antigo em `core/render_cache.py`, `features/editor/editor_window.py`, `features/generator/workers.py` e `features/workspace/main_window.py`; a substituição desses acessos pertence à Etapa 2.
- Validação: 14 testes específicos do contrato e suíte completa com 70 testes e 10 subtestes aprovados.

## 12. Evidências da Etapa 2

- Novos salvamentos publicam `template_v4.json` por arquivo temporário sincronizado e troca atômica. O v3 existente permanece intacto.
- A partir do segundo salvamento v4, `template_v4.json.bak` conserva o último documento válido. Falha antes da troca mantém o arquivo principal anterior.
- O editor monta somente a frente nesta etapa, mas salva o documento completo: o teste de integração confirmou que abrir e salvar a frente preserva o verso.
- A coleta e a limpeza percorrem imagens, assinaturas e fundos das duas páginas. Também preservam referências existentes no backup v4 e no v3 usado para recuperação; se o documento principal não puder ser determinado, a limpeza é cancelada.
- Modelo inicial, biblioteca, abertura, duplicação, renomeação, importação e preferências de exportação usam o contrato central. Um pacote v3 é promovido na área temporária; um pacote v4 conserva as duas páginas.
- A instalação de ZIP copia e valida todo o diretório em uma área intermediária no mesmo sistema de arquivos. A troca pela versão anterior ocorre somente depois disso e possui restauração em caso de falha.
- O workspace usa a frente para os recursos ainda restritos a uma página e bloqueia a exportação de um documento com verso até as Etapas 6–7, evitando perda silenciosa.
- Workers de prévia descartam o resultado se o arquivo ativo mudar de v3 para v4 durante o processamento, além de conferir o hash do arquivo de origem.
- Foram cobertos salvamento interrompido, recuperação, remoção/restauração lógica do verso, cópia integral, preservação de asset exclusivo do verso e de asset acessível somente pela recuperação.
- Validação: 25 testes em `tests/test_model_document.py`; conjunto `tests/` com 62 testes e 10 subtestes; conjunto do editor com 19 testes. Todos aprovados em modo offscreen.
- A captura de referência foi repetida após a integração: o PNG permaneceu em 320 × 200 px e com SHA-256 `31855e193b02d56eb6a5964d1bebb64ec37afae4d202bed7435537476b185691`.

## 13. Evidências da Etapa 3

- `NativeRenderer` aceita um documento v4 e o ID `front` ou `back`; dados legados e visões já adaptadas continuam aceitos.
- Cada renderizador registra sua página e mantém caches próprios. Workers recebem forks com dicionários de imagens/pixmaps independentes e uma cópia da base estática em `QImage`.
- Miniaturas passaram de um único `thumbnail_raw.png` para `thumbnail_front.png` e `thumbnail_back.png`. O manifesto exige página, nome do arquivo fonte e SHA-256 da revisão ativa.
- A publicação de miniaturas e do manifesto usa arquivos temporários e troca atômica. Um resultado iniciado em outra revisão ou antes da promoção v3→v4 é descartado.
- Proxies de fundo incluem a página na especificação e ficam registrados separadamente no manifesto. Atualizar ou limpar um lado preserva o proxy ainda válido do outro.
- A prévia de folha já usa diretório exclusivo e número de geração; alterações de dados, modelo ou configuração cancelam a geração anterior. Os workers pintam em `QImage`; a conversão para `QPixmap` permanece no fluxo da interface.
- Fontes simples e ricas, links e assets são coletados nas duas páginas. Foi corrigido o caso em que uma declaração `font-family` sem ponto e vírgula final incorporava o restante do HTML ao nome.
- Testes renderizam frente e verso graficamente distintos e confirmam que links do verso não aparecem na frente. Também verificam isolamento de proxies, miniaturas, revisões e caches dos workers.
- Validação: 32 testes no contrato multipágina; conjunto `tests/` com 69 testes e 10 subtestes; conjunto do editor com 19 testes. Todos aprovados em modo offscreen.
- A prova de compatibilidade permaneceu idêntica: PNG de 320 × 200 px e SHA-256 `31855e193b02d56eb6a5964d1bebb64ec37afae4d202bed7435537476b185691`. Nesta repetição, a primeira prévia levou 13,187 ms, a prévia aquecida 0,941 ms e 100 renderizações 96,175 ms.

## 14. Evidências da Etapa 4

- O rodapé exibe `Página 1` e `+ Página` em modelos simples. Ao adicionar o verso, passa a exibir `Página 1` e `Página 2`, centralizados sob o canvas mesmo após redimensionar os painéis.
- Cada botão de página possui menu próprio com `Limpar página`; com duas páginas, o menu também oferece `Remover página`. As ações destrutivas pedem confirmação e entram no histórico.
- Remover a página 1 promove a antiga página 2 para página 1. Limpar mantém uma página válida contendo somente o plano de fundo branco obrigatório.
- Apenas a página ativa é montada na cena. Trocar de página conclui a edição em curso, cancela o desenho ainda incompleto, conserva a seleção de cada página por identidade e não cria ação de histórico.
- O histórico guarda o documento completo, possui limite de 100 estados e 64 MiB e conduz o editor à página afetada ao desfazer ou refazer. Seleção, navegação e estado visual dos painéis permanecem fora dele.
- Alterar largura ou altura sincroniza os fundos das duas páginas. Edições comuns não normalizam nem modificam a página inativa; o teste de abrir, editar e salvar somente a frente preserva o verso integralmente.
- Salvar e reabrir um modelo conserva o conteúdo das duas páginas. O editor continua abrindo pela página 1 e permite alternar para o verso salvo.
- Os textos novos foram incorporados aos catálogos em inglês e espanhol. A exportação pelo workspace continua bloqueada para duas páginas até as Etapas 6–7, evitando produzir um resultado parcial.
- Validação: `tests/` com 70 testes e 10 subtestes; conjunto do editor com 25 testes. Todos aprovados em modo offscreen. `git diff --check` e compilação dos módulos alterados também foram aprovados.

## 15. Evidências da Etapa 5

- `placeholders` representa a ordem global escolhida na lista do editor; `field_ids` registra somente os campos usados por cada página. Alternar ou salvar uma página não copia seus campos para a outra.
- A união mantém a ordem já definida, elimina repetições e acrescenta campos novos deterministicamente. Ao remover o último uso de um campo, ele sai do documento; a coluna e seus dados podem permanecer como inativos durante a sessão, fora da geração, até o usuário confirmar o descarte. Campos ainda usados no outro lado permanecem ativos.
- Links ativos em texto, imagem e forma são campos de dados mesmo quando aparecem somente no verso. Objetos podem repetir nomes entre as páginas porque suas identidades são locais à página; chaves de link iguais compartilham intencionalmente uma coluna, assim como placeholders iguais.
- O workspace examina assinaturas nas duas páginas. Uma assinatura exclusiva do verso já cria a coluna de ativação, e `__use_signature__` continua sendo uma decisão única por registro aplicada ao documento completo.
- Criar, limpar ou remover o verso recalcula a união sem alterar a ordem dos campos restantes. Ao salvar pelo editor, a atualização da tabela continua restaurando as células pelo identificador do cabeçalho, preservando os dados dos campos que permanecem.
- A extração e a substituição de placeholders agora aceitam letras Unicode. Foi validado `{Matrícula}` em HTML rico com estilos dividindo a palavra e na renderização final.
- `Cópias = N` produz N cópias da linha completa, incluindo campos usados no verso e a opção de assinatura. Zero continua omitindo o registro; valor inválido conserva a regra anterior de uma cópia.
- Os catálogos inglês e espanhol incluem a mensagem atualizada sobre caracteres válidos e os estados dos campos inativos.
- Validação específica da etapa aprovada antes do avanço; a regressão acumulada está registrada na Etapa 6.

## 16. Evidências da Etapa 6

- Cada tarefa continua representando um registro/cópia. O nome-base é reservado uma vez e suas páginas são renderizadas em ordem pelos renderizadores isolados `front` e `back`.
- Modelos de uma página conservam a nomenclatura anterior. Em modelos de duas páginas, PNG gera `<nome>_pag1.png` e `<nome>_pag2.png`; um verso existente é produzido mesmo quando contém somente o fundo branco.
- PDF por item abre um único writer por documento e grava frente e verso com as dimensões físicas do modelo. PDF agrupado ordena pelo índice numérico do documento e da página, independentemente da ordem em que as threads terminam.
- Links são coletados separadamente em cada página e reinseridos no índice PDF correspondente. O teste multipágina validou URLs diferentes na frente e no verso e confirmou que a região clicável acompanha a caixa delimitadora de uma forma rotacionada.
- O progresso conta documentos completos. A montagem do PDF agrupado reserva os últimos 5% e só informa 100% depois que o arquivo final foi publicado.
- PNG e PDF por item são gravados primeiro em nomes temporários. Uma falha no verso remove os temporários e não publica apenas a frente. O PDF agrupado também usa arquivo temporário, atende cancelamento e limpa o diretório intermediário em falhas gerenciadas.
- O workspace permite exportação direta de duas páginas. Enquanto a Etapa 7 não estiver concluída, uma predefinição com imposição é bloqueada com orientação para usar `Definição do Modelo`, evitando saída física incorreta.
- Erros reabilitam a interface com a mensagem de processo interrompido; não são mais apresentados como conclusão normal. Os catálogos inglês e espanhol possuem 423 traduções concluídas.
- Validação: `tests/` com 83 testes e 10 subtestes; conjunto do editor com 26 testes. Todos aprovados em modo offscreen. A compilação dos módulos alterados e `git diff --check` também foram aprovados.
