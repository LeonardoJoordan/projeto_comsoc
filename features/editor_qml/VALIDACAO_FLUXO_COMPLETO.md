# Validação do fluxo do editor QML

Data: 07/09/2026. Ambiente: Linux, PySide6/Qt com plataforma `offscreen`.

Complemento de 08/09/2026: o plano de desempenho do canvas foi concluído com novas
correções e validação de exportação. Ver
[RELATORIO_DESEMPENHO_CANVAS.md](RELATORIO_DESEMPENHO_CANVAS.md) para 68 testes do
editor/workspace, dois de PDF, nove cenários gráficos e medições comparativas.

**Resultado:** validação automatizada aprovada: 46 testes do editor/workspace e
2 testes de links PDF. A abertura QML com `--check` também passou. O editor legado
permanece como padrão para instalações sem preferência salva. A escolha existente
do usuário é respeitada. Não foi realizada impressão em equipamento físico; a
mudança definitiva do padrão fica aguardando essa conferência e aceite operacional.

## Modelos utilizados

Foram utilizadas cópias temporárias dos três modelos existentes em `models/`.
Os hashes dos arquivos originais foram conferidos após os testes: nenhum mudou.
Esses são os exemplos disponíveis no repositório, não uma amostra completa dos
modelos usados em produção.

| Modelo | Canvas original | Elementos exercitados | Resultado no QML |
| --- | --- | --- | --- |
| `teste` | 1000 × 1000 | Texto Amiri, variável, negrito, recuo | Pixels idênticos após migrar, salvar e reabrir |
| `teste2` | 2484 × 3512 | Fundo, três textos, variáveis e assinatura | Pixels idênticos após migrar, salvar e reabrir |
| `teste3` | 2484 × 3512 | Fundo, imagem e dois textos variáveis | Pixels idênticos após migrar, salvar e reabrir |

Cada modelo foi renderizado com variáveis vazias/assinatura desativada e com
variáveis preenchidas/assinatura ativada. Foram comparados os pixels completos
contra a renderização do JSON original, inclusive com cache estático habilitado.
PNG gerado pelo `RenderManager` também preservou os pixels. Os PDFs dos três
modelos foram verificados quanto à presença da imagem e às medidas da página.

Os mesmos modelos foram abertos no editor Widgets, usando uma biblioteca
temporária para resolver seus assets. As quantidades de textos, imagens e
assinaturas e a presença dos fundos foram preservadas na abertura.

**Diferença preexistente no legado:** ao abrir `teste`, que não declara medidas
físicas, o editor Widgets assume 100 × 150 mm e modifica o canvas de 1000 × 1000
para 1181 × 1771. Por isso não se declara igualdade visual entre as duas janelas
nesse caso. O QML conserva as dimensões originais; o baseline de comparação é o
JSON original renderizado pelo gerador. Nenhum arquivo de `features/editor/` foi
alterado. Arial está ausente neste ambiente: o QML informa o fallback e preserva
o nome solicitado no arquivo, mas isso não comprova equivalência com Arial instalada.

## Matriz de exportação e integração

| Verificação | Resultado |
| --- | --- |
| Modelos reais → abrir/salvar/reabrir → PNG e PDF pelo gerador do workspace | Aprovado |
| Modelo com forma girada, contorno, texto variável e link → salvar/reabrir → PDF individual/único | Aprovado; três páginas/registros na ordem esperada e URLs conservadas |
| PDF rasterizado pelo Poppler (`pdftoppm`) comparado ao renderer | Aprovado para o cenário moderno; erro médio por canal inferior a 8 em escala 0–255 |
| Medida personalizada próxima de A4: 210,312 × 297,349 mm | Aprovado sem ajuste automático para A4 |
| Imposição A4 com cartões 95 × 134,3 mm | Retrato, capacidade 4; cinco registros em duas folhas |
| Imposição A4 com cartões 40 × 50 mm | Paisagem, capacidade 28; 29 registros em duas folhas |
| Ambas as imposições em PNG, PDF individual e PDF único | Aprovado; página final parcial, dimensões e contagem corretas |
| PNG das folhas contra montagem esperada, incluindo marcas de corte | Pixels idênticos; metadados de 300 DPI |
| Falha ao gravar PNG, lote vazio ou cartão maior que a folha | Erro e término emitidos; interface pode liberar a geração |
| Imagem intermediária ausente no PDF único | Erro emitido, sem sinal de sucesso |
| Histórico, bloqueios, estilos, controles QML e fechamento com cancelamento | Suíte existente aprovada |
| Salvar pelo QML e atualizar biblioteca, colunas, valores e prévia do workspace | Suíte existente aprovada |

O MediaBox escrito pelo Qt tem quantização em pontos; as medidas dos PDFs são
conferidas com tolerância de 0,18 mm por dimensão. A comparação visual independente
usa tolerância por conta da compressão e reamostragem do PDF; não é igualdade
pixel a pixel. PDFs continuam contendo a imagem rasterizada do modelo.

## Correções feitas durante a validação

- Resolução de fundo legado com caminho relativo ao diretório do modelo no renderer.
- Montagem de folhas com `QImage`, evitando `QPixmap` em threads de geração.
- PNG individual recebe a medida física configurada; PNG de imposição informa
  300 DPI. Os metadados são aplicados após pintar o cartão, conservando o layout
  de texto calculado a 96 DPI.
- PDFs usam medidas exatas, sem aproximação automática para um papel conhecido.
  A orientação da folha já montada não é aplicada uma segunda vez.
- Falhas de gravação PNG e de abertura do PDF são informadas. Falhas dos workers,
  ausência de registros e falta de espaço na folha encerram o processo em erro.
- Montagem híbrida não ignora imagens ausentes nem esconde falhas ao inserir links.
- Medidas físicas sugeridas pelo QML, quando ausentes no arquivo, seguem o fallback
  de 300 DPI do workspace; documentos com medidas explícitas as conservam.
- Testes da escolha de editor usam o identificador da opção, sem depender de sua
  posição na lista. A alteração antecipada do padrão para QML foi retirada.

## O que ainda exige conferência antes de trocar o padrão

1. Imprimir os PDFs em tamanho real (100%, sem ajustar à página), medir cartão e
   margens e conferir marcas de corte, cores e recortes na impressora utilizada.
   Não há validação de driver, spooler ou papel nesta execução. A aba de impressão
   configura a imposição/exportação; não existe envio direto à impressora no fluxo atual.
2. Conferir modelos de produção com as fontes efetivamente instaladas e realizar
   aceite visual/operacional nos dois editores. A comparação automatizada cobre
   os três exemplos do repositório e os cenários sintéticos descritos acima.
3. Medir consumo de memória e resposta em lotes grandes e modelos pesados de produção.

Limitações funcionais continuam em [PENDENCIAS_INTEGRACAO.md](PENDENCIAS_INTEGRACAO.md).
Em particular, os links foram validados em PDFs diretos e únicos sem imposição;
o gerador de folhas ainda não mapeia links dos cartões para a página imposta.
Salvar recursos modernos pelo editor antigo continua perdendo campos que ele não
conhece, com aviso antes da abertura. Isso não foi tratado como ida e volta compatível.

## Reproduzir

### Correção posterior: fechamento ao abrir no ambiente gráfico

O teste do operador revelou uma falha que a execução `offscreen` não cobria.
Foi reproduzido um `Segmentation fault` em `CanvasTextEditor.paint()` no X11:
o Qt Quick chamava a pintura pela `QSGRenderThread`, que acessava o
`QTextDocument` pertencente à thread da interface.

A edição agora prepara um `QPicture` na thread da interface. A pintura apenas
reproduz esses comandos, sem acessar documento, cursor ou layout. A atualização
inclui seleção, formatação, cursor e mudança de foco.

Após a correção, passaram a suíte anterior de 46 testes e um novo teste de
regressão que pinta em outra thread com o acesso ao documento/cursor bloqueado.
Também passaram os três testes de integração do workspace em X11 com renderização
threaded, usando modelos/configurações temporários, e a abertura/edição em memória
do modelo `teste2` no ambiente gráfico real. O encerramento nativo foi reproduzido
antes da correção e deixou de ocorrer nesse mesmo ambiente depois dela.

```bash
QT_QPA_PLATFORM=xcb QSG_RENDER_LOOP=threaded .venv/bin/python -X faulthandler \
  -m unittest features.editor_qml.tests.test_completion.WorkspaceEditorTest -v
```

Esse comando exige uma sessão gráfica X11 acessível; os testes headless continuam
úteis, mas não substituem a verificação do render loop gráfico.

Na raiz do projeto:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s features/editor_qml/tests -v
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen .venv/bin/python features/editor_qml/main.py --check
```

Para guardar os PNGs/PDFs gerados e conferir em um visualizador:

```bash
QT_QPA_PLATFORM=offscreen COMSOC_VALIDATION_ARTIFACTS=/tmp/comsoc-validacao \
  .venv/bin/python -m unittest features.editor_qml.tests.test_end_to_end -v
```

Os artefatos desta execução estão em `/tmp/comsoc-validacao/`, incluindo a captura
`editor-qml.png`. Arquivos em `/tmp` são temporários; os testes permitem recriá-los.
O teste de rasterização independente requer `pdftoppm`; sem ele é marcado como
ignorado. Nesta execução ele estava disponível e o teste passou.
