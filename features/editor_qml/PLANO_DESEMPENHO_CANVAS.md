# Plano de desempenho e interação do canvas QML

## Objetivo e limites

Recuperar a resposta imediata do editor legado preservando o frontend aprovado.
Não modificar `features/editor/`, o formato salvo ou o resultado de exportação.
Usar as regras antigas de geometria, proporção, bloqueio e histórico como referência.
Não tentar embutir `QGraphicsItem` diretamente no QML: reaproveitar regras e layout,
com objetos visuais independentes na cena Qt Quick.

Este arquivo é o ponto de retomada. Ao concluir cada etapa, registrar arquivos,
testes efetivamente executados e o próximo trabalho. Não marcar como concluída
uma melhoria apenas porque sua infraestrutura foi criada.

## Diagnóstico confirmado

- `CanvasWorkspace.qml` mostra uma imagem única e overlays transparentes.
- Arraste/redimensionamento atualizam o documento somente em `onReleased`; não
  existe acompanhamento visual do conteúdo durante o movimento.
- `bridge.notify()` invalida todas as views, verifica fontes, emite notificações
  amplas e agenda a renderização completa, mesmo para alteração de posição.
- `paint_preview()` cria novos renderers e perde caches entre prévias.
- Entrar na edição de texto ainda renderiza sincronicamente as camadas de baixo/cima.
- No legado, os itens da cena mudam de posição independentemente, sem recriar
  a imagem completa do documento a cada movimento.
- `QTextDocument` deve permanecer na thread da interface. A correção anterior
  registra `QPicture` na GUI e apenas reproduz a pintura na thread gráfica.

## Etapas e critérios de conclusão

### 1. Mapear responsabilidades e definir a arquitetura — CONCLUÍDA

Separar conteúdo pintado de posição e interação. A cena QML deve compor objetos
individualmente, em `layer_order`. A geração final continua no renderer existente.
Preparar pintura reutilizável na GUI; a thread gráfica não acessa documentos de texto.
Decisão: começar pelo cache isolado com paridade verificada antes de trocar o canvas.

### 2. Preparar pintura reutilizável por objeto — CONCLUÍDA

Criar cache de comandos de pintura em coordenadas locais usando o renderer atual.
Mover X/Y, selecionar, bloquear ou renomear não deve recalcular o conteúdo.
Mudanças de texto, dimensões, estilo e assets devem invalidar somente o necessário.
Remover entradas de objetos excluídos. Validar igualdade dos pixels na composição
com textos, formas, imagens, rotação, opacidade e contorno.
Esta etapa isolada não muda ainda a interação visível.

Implementado em `layer_paint_cache.py`: comandos QPicture locais, reutilização
do renderer/assets entre objetos, invalidação por conteúdo e versão do arquivo,
descarte explícito por IDs retidos. X/Y, nome, bloqueio e visibilidade não invalidam
a pintura. Visibilidade e translação ficam a cargo do consumidor. Nesta versão,
rotação/opacidade estão gravadas no QPicture; não aplicá-las novamente no QML.

Verificação executada: `test_layer_paint_cache.py`, dois testes aprovados.
Incluem igualdade de pixels para composição de texto/forma e imagem/assinatura,
rotação, opacidade, contorno, troca de asset, descarte e contagem de gravações:
mover/renomear não grava novamente; mudar fonte grava apenas o texto alterado.
Não foram medidos FPS nem latência da interface nesta etapa.

### 3. Substituir a imagem única pela composição de objetos — CONCLUÍDA

Criar o componente visual Qt Quick que consome a pintura local sem acessar o
documento em `paint()`. Tratar limites de tinta/contorno, texto fora da caixa,
rotação, opacidade, zoom e ordem entre tipos. Fundo branco é da página.
Preservar objetos por ID: evitar destruir todos os delegates em cada alteração.
Integrar edição de texto na posição da camada, sem renderizar duas páginas ao entrar.
Critério: cena composta equivalente à prévia atual; exportação permanece igual.

Implementação: `canvas_layers.py` fornece `LayerSceneModel` (QAbstractListModel),
`LayerData` com identidade estável e `CanvasLayer` para reproduzir comandos de
pintura. O bridge mantém o cache por sessão e sincroniza conteúdo/geometria sem
recriar delegates de camadas mantidas. O canvas compõe esses objetos na ordem global.
Os limites incluem rotação, contorno e transbordamento de texto; os limites de texto
são calculados explicitamente porque QPicture não os determina corretamente.

A textura tem dimensões de exibição; o zoom não requer uma textura no tamanho
original do documento. Rotação/opacidade continuam gravadas na pintura, sem segunda
aplicação no item visual. Overlays de seleção continuam usando a geometria da caixa.
Ao editar texto, somente sua pintura estática é escondida e o editor nativo ocupa
a mesma posição entre as camadas. Não há divisão da página em imagens superior/inferior.

Após `attachCanvas()`, alterações não agendam a prévia completa. O caminho de
renderização anterior permanece disponível para salvamento/miniaturas e consumidores
sem canvas. Ainda existem notificações amplas, verificação de fontes e cópias do
documento; sua redução continua na etapa 5.

Validação executada:

- 53 testes do editor/workspace aprovados em `offscreen`, incluindo os novos testes
  de identidade, cache, ordem da edição e recorte de cada objeto.
- Composição dos três modelos do repositório comparada ao renderer. A composição
  intermediária com transparência admite até 2 níveis por canal (0–255), devido ao
  arredondamento de alpha; não é declarada igualdade bit a bit desse novo caminho.
  O cenário de texto girado com contorno/transbordamento passou com pixels idênticos.
- Quatro testes em X11 com `QSG_RENDER_LOOP=threaded` aprovados: identidade/ordem na
  cena e os três testes do workspace (abrir/salvar/fechar).
- Abertura normal com captura de `teste2` em X11 aprovada; captura temporária em
  `/tmp/comsoc-stage3-native.png`.
- A tentativa de executar toda a suíte de mouse em X11 bloqueou no `QTest.mouseClick`;
  a pilha foi capturada e os processos de teste encerrados. A abertura normal não
  apresentou esse bloqueio. A espera da suíte foi adaptada para QEventLoop; os sete
  testes QML com mouse/teclado passaram em `offscreen`. Não declarar essa suíte toda
  aprovada no modo threaded. Esse limite do harness permanece para a etapa 7.

### 4. Movimentação e redimensionamento imediatos — CONCLUÍDA

Durante o gesto, alterar somente a transformação visual; confirmar dados e um
snapshot ao soltar. Cancelar restaura a posição inicial sem criar histórico.
Reaproveitar regras de proporção, bloqueio, rotação e zoom. No resize de texto,
recalcular somente seu layout quando necessário; não esticar glifos como resultado final.
Critério: conteúdo acompanha o mouse, camadas paradas não são repintadas por Python,
desfazer restaura o gesto inteiro e não existem saltos ao confirmar.

Implementado no bridge: `beginTransform`, `updateTransform`, `finishTransform`
e `cancelTransform`. A geometria transitória fica em `LayerData.view`, compartilhada
pela pintura e pelo overlay, sem modificar `_data`, sem chamar `notify()` e sem
adicionar histórico durante os eventos de mouse. Soltar confirma uma única ação.
Movimentar reutiliza o mesmo QPicture; redimensionar recalcula somente o objeto
selecionado, inclusive a quebra de linhas do texto. A pintura final é reaproveitada
na confirmação, evitando recalcular novamente o mesmo resize.

O delta do ponteiro é convertido pelo zoom capturado no início do gesto. No resize,
é convertido também para os eixos locais do objeto girado; o canto superior
esquerdo no espaço girado permanece fixo. Bloqueio, proporção e formas quadradas/
circulares são respeitados. Dimensões mínimas de 1 px e deltas finitos são exigidos.

Esc, perda do mouse grab, desativação da janela, mudança de zoom e troca de seleção
cancelam o gesto. Salvar/fechar cancelam a geometria ainda não confirmada. Desfazer/
refazer durante um gesto primeiro cancelam esse gesto. Cancelar restaura a pintura
e os dados visuais iniciais e conserva o histórico de refazer. Os campos do inspector
continuam exibindo a geometria confirmada até soltar; atualização incremental desses
campos pode ser tratada na etapa 5 sem reintroduzir notificações globais por evento.

Validação:

- 59 testes da suíte do editor/workspace aprovados em `offscreen`.
- Quatro novos testes de transação: 99 movimentos sem regravar pintura nem alterar
  documento/histórico, confirmação única e undo/redo, cancelamento de resize,
  preservação do canto com rotação de 45°, bloqueio/proporção e deltas inválidos.
- Dois novos testes QML com eventos postados verificam a posição visual antes de
  soltar, zoom de 140%, Esc, histórico e reflow durante resize; ambos passaram
  também em X11 com `QSG_RENDER_LOOP=threaded`.
- A primeira tentativa gráfica de arraste falhou durante ativação da janela. Após
  aguardar sua ativação antes dos eventos, os dois cenários passaram. Os testes
  usam `postEvent` + `QEventLoop`, evitando a espera síncrona de `QTest.mouseClick`
  que bloqueava os testes threaded da etapa 3.
- Ainda não foram medidos FPS/latência com modelos pesados; essa medição permanece
  na etapa 7, sem alegação de desempenho equivalente ao legado em todos os casos.

### 5. Notificações e trabalhos incrementais — CONCLUÍDA

Separar atualização de geometria, seleção, conteúdo, fontes e estrutura. Seleção
e movimento não devem reconstruir layouts nem disparar geração completa.
Reutilizar assets e controlar invalidação. Reservar renderer de página para
miniaturas/salvamento/exportação. Remover caminhos antigos depois de cobrir substitutos.
Critério: verificar por contadores que operações simples não disparam trabalho global.

Implementado: cache de views por ID, análise de HTML e formato rico reutilizável,
verificação de fontes condicionada a alterações dos campos tipográficos e emissão
de `documentChanged` somente quando as views realmente mudam. A cena compara os
dados de cada objeto e resolve/copia apenas os alterados; movimento, bloqueio e
renomeação reutilizam a pintura sem sequer consultar seu cache de comandos.
Guias não alteram as views nem a pintura dos objetos.

O canvas não chama mais `render_data()` na sincronização de alterações e a sessão
não solicita uma prévia completa redundante ao abrir. A geração de página continua
disponível para salvamento/miniaturas e para consumidores sem canvas conectado.
Salvar como sincroniza imediatamente os caminhos resolvidos da cena. Reabrir
invalida caches; substituir uma imagem, inclusive pelo mesmo caminho, invalida os
objetos que usam esse asset e a imagem decodificada correspondente.

Validação: 62 testes aprovados em `offscreen`; cinco verificações em X11/threaded
(arraste com zoom/Esc, resize e três testes do workspace) aprovadas. Os três testes
incrementais foram repetidos após reforçar a invalidação de assets no mesmo caminho.
Em um cenário de 20 textos, os contadores confirmaram:

- Seleção e movimento sem reconstrução de QTextDocument/layout, varredura de fontes
  ou preparação de página; mover atualiza apenas uma view.
- Guias sem novas views nem consultas à pintura dos objetos.
- Alteração de HTML com apenas uma view e uma pintura atualizadas; aviso de fonte
  ausente atualizado e restaurado ao desfazer.
- Salvar como, reabrir e substituir asset no mesmo caminho atualizam paths e pixels.

Limites: a comparação leve das listas e os sinais gerais de estado ainda existem;
o histórico continua usando snapshots completos por operação confirmada. Não foi
afirmado custo constante em relação ao tamanho do documento. Resize de texto ainda
recalcula o objeto selecionado por evento; coalescer por frame depende das medições
da etapa 7. Arquivos alterados externamente são atualizados ao reabrir/substituir,
sem monitoramento contínuo do filesystem.

### 6. Guias, teclado e acabamento da interação — CONCLUÍDA

Aplicar o mesmo acompanhamento visual às guias; conferir setas, foco, edição,
rolagem e zoom. Comparar com o comportamento antigo. Magnetismo/réguas avançadas
não entram implicitamente neste trabalho; registrar necessidades separadas.
Critério: nenhum conflito entre arrastar, digitar, atalhos e navegar.

Implementação concluída em 08/09/2026:

- Guias horizontais/verticais usam posição transitória e acompanham o mouse sem
  modificar o documento ou repintar objetos. Soltar confirma uma ação; Esc, perda
  do grab/foco, mudança de zoom e troca de seleção cancelam. Bloqueio/visibilidade
  são verificados. Gesto sem mudança não cria histórico nem dispara atualização.
- Removida a propriedade `position` do MouseArea da guia: seu sinal colidia com
  o evento de movimento e produzia um argumento `mouse` indefinido.
- Desfazer/refazer/duplicar por atalho não atuam sobre o documento enquanto um
  TextInput/TextEdit tem foco. A edição nativa de texto conserva seus comandos.
  Selecionar uma camada pela lateral ou clicar no canvas devolve foco ao canvas.
- Setas movem 1 px e Shift+setas 10 px com foco no canvas; em campos de entrada,
  as setas ficam com a edição do campo. Não há movimentação de camada durante digitação.
- Botão do meio permite pan, limitado às dimensões roláveis. Pan não altera o
  documento/histórico. Flickable fica sem interação de navegação durante gestos
  de objeto/guia; mudança do zoom ou tamanho do viewport cancela o gesto pendente.
  Barras de rolagem e controles de zoom existentes permanecem disponíveis.

Validação: 67 testes do editor/workspace aprovados em `offscreen`. Três testes
novos de eventos postados também passaram em X11 com `QSG_RENDER_LOOP=threaded`:
guia ao vivo/cancelamento por zoom; setas/Shift e atalhos com foco em input; pan
com botão do meio sem modificar o documento. Testes do bridge cobrem as duas
orientações de guia, 100 atualizações transitórias, confirmação única, undo,
cancelamento com redo preservado, bloqueio/visibilidade e posições inválidas.
`--check` e `git diff --check` passaram.

Não foram adicionados magnetismo, réguas avançadas nem todos os modos de pan do
legado. A etapa entrega navegação com botão do meio e controles existentes; a
comparação quantitativa de desempenho continua na etapa 7.

### 7. Validar desempenho e regressões no ambiente real — CONCLUÍDA

Executar testes de pintura, histórico, gravação e integração. Testar X11 com
`QSG_RENDER_LOOP=threaded`, porque `offscreen` não detectou a falha gráfica anterior.
Usar cópias de modelos reais e um cenário pesado reproduzível; registrar dimensões,
número de objetos, tempo de preparação e latência durante arraste. Comparar com
o legado na mesma máquina, sem prometer FPS antes de medir.
Critério: movimento sem renderização global, resposta visual contínua, pixels de
exportação preservados e nenhuma falha nativa. Solicitar avaliação do operador
somente depois de entregar a implementação concreta.

Concluída em 08/09/2026. Script reproduzível em `benchmark_canvas.py`; números
brutos em `BENCHMARK_RESULTADOS.json` e análise completa em
[RELATORIO_DESEMPENHO_CANVAS.md](RELATORIO_DESEMPENHO_CANVAS.md).

Foram comparados os dois editores no X11/threaded com um modelo do repositório,
um modelo da biblioteca instalada e um cenário sintético de 150 textos. Cada
execução usou processo separado e cópias temporárias; o cenário pesado teve três
repetições finais por editor. Medidas de API, memória e sinais gráficos foram
registradas separadamente, sem apresentar proxies Qt como latência física ou FPS.

O benchmark revelou um gargalo ainda presente após a etapa 6: transporte das
listas completas do documento em cada consulta QML a `state` e recriação das
linhas laterais ao confirmar alterações. Isso foi corrigido com `uiState`,
`uiTextFormat`, `LayerData.uiView` e modelo estável da lista lateral em ordem inversa.
As APIs Python anteriores foram preservadas; o HTML completo continua disponível
para edição, mas não é transportado para cada binding de geometria/formatação.

No cenário pesado, a confirmação caiu de aproximadamente 5,85 s para 40–46 ms,
o pico de RSS de 2.606 MiB para aproximadamente 325 MiB e o P95 da API de movimento
de 16,98 ms para 0,71–0,91 ms. Resize ficou em 4,52–4,59 ms no P95. O legado
continua com menor custo por operação/memória; a comparação detalha essa diferença.
Os resultados não justificaram coalescimento adicional de resize neste cenário.

Validação final: 68 testes do editor/workspace, dois de links PDF e nove verificações
gráficas aprovados; PNG/PDF individual/único e imposição passaram com o canvas
conectado. Os modelos de origem não foram regravados. `--check` e `git diff --check`
passaram. Nenhum arquivo do editor legado foi alterado por estas etapas.

## Estado para a próxima retomada

**Etapas 1 a 7 concluídas.** O plano técnico de responsividade foi executado e
medido. Não reiniciar etapas concluídas em uma retomada: consultar o relatório
e os dados do benchmark antes de investigar um novo relato do operador.

Continuidade fora deste plano técnico:

1. Obter avaliação do operador nos modelos habituais; se houver novo atraso,
   reproduzir o arquivo/operação e comparar com o benchmark registrado.
2. Não afirmar que o QML iguala o legado em todos os cenários: o relatório conserva
   os custos maiores de memória, chamadas e confirmação que ainda existem.
3. Fazer a prova física de impressão e aceite operacional antes de mudar o padrão.
4. Para novas regressões, preservar os testes de estado compacto e identidade da
   lista lateral; não reintroduzir listas/HTML em cada binding QML.

Teste específico executado:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s features/editor_qml/tests -v
QT_QPA_PLATFORM=xcb QSG_RENDER_LOOP=threaded .venv/bin/python -X faulthandler -m unittest \
  features.editor_qml.tests.test_qml.QmlIntegrationTest.test_live_drag_at_zoom_commits_once_and_escape_restores \
  features.editor_qml.tests.test_qml.QmlIntegrationTest.test_live_resize_reflows_text_before_release -v
```

`git diff --check` passou. A suíte completa e nove cenários gráficos foram
executados após as correções motivadas pelas medições da etapa 7.

Preservar todas as alterações anteriores do worktree. Testes e experimentos com
modelos devem usar cópias temporárias e configurações isoladas.
