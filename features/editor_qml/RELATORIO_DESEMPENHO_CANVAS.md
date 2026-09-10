# Validação de desempenho do canvas — etapa 7

Data: 08/09/2026. Etapa técnica concluída, com correções e medições repetidas.

O cenário pesado revelou custos que os testes funcionais não detectavam. Após
as correções desta etapa, desapareceram os bloqueios de segundos nos cenários
medidos. O legado ainda usa menos memória e tem menor custo por operação. Não
se declara igualdade de desempenho em todas as máquinas/modelos nem impressão
física validada. O editor padrão não foi alterado.

## Correções motivadas pelas medições

- Cada consulta QML a `editor.state` transportava as listas completas de camadas,
  além do objeto selecionado. Muitos bindings de campos e camadas repetiam esse
  transporte. A interface agora usa `uiState`, sem essas listas e sem HTML bruto.
  Contagem de elementos é um inteiro; a API Python anterior foi preservada.
- `uiTextFormat` e `LayerData.uiView` também evitam transportar HTML para controles
  que só precisam de formatação, título ou geometria. A edição continua recebendo
  o documento completo diretamente pelo bridge.
- A lista lateral deixou de receber uma lista QVariant inteira a cada atualização.
  Agora usa o modelo de objetos estáveis com um proxy em ordem inversa. Seus itens
  são preservados ao confirmar movimento/alterações comuns. Uma reordenação
  estrutural pode reorganizar/recriar delegates do proxy; a identidade dos objetos
  e a ordem permanecem corretas.
- Removida a ligação obsoleta `selectionContent`, que transportava HTML sem consumidor.

Nenhum arquivo de `features/editor/` foi alterado nesta etapa. O backend de
exportação também permaneceu como estava no início desta etapa.

## Método e condições

Script: [benchmark_canvas.py](benchmark_canvas.py).
Dados: [BENCHMARK_RESULTADOS.json](BENCHMARK_RESULTADOS.json).

- Linux x86_64, Qt/PySide6 6.11.0, X11 (`xcb`), render loop `threaded`, 32 CPUs
  lógicas informadas pelo sistema e tela com frequência informada próxima de 60 Hz.
- Janelas de 1500 × 930; cada execução em processo separado, sequencialmente,
  sem rodar a suíte de testes simultaneamente às medições.
- Modelos copiados para diretórios temporários. Hashes dos arquivos de origem
  conferidos ao terminar. Não houve gravação nos modelos originais.
- 90 atualizações programáticas de movimento e 90 de resize, solicitadas por
  timer de 16 ms. Mede-se o tempo da chamada à API, a confirmação com snapshot,
  os intervalos efetivos dos callbacks e um proxy de atualização gráfica.
- O texto escolhido é desbloqueado e sua proporção liberada **nas cópias de ambos
  os editores**. Uma primeira medição da biblioteca foi descartada porque o texto
  estava bloqueado e o QML não iniciou um gesto. O script agora exige início válido.
- O script aciona `updateTransform` no QML e `setPos`/`resize_from_handle` no legado.
  Isso compara o custo desses caminhos programáticos, não toda a cadeia de eventos
  físicos de mouse. A interação de mouse foi coberta separadamente pelos testes
  gráficos com eventos postados.
- `open_api_ms` inclui construção/importação do editor, leitura, preparação e
  seleção/configuração do alvo, mas não significa tempo até o primeiro frame.
- Pico de RSS é do processo completo durante a execução, não só das texturas.

### Modelos

| Cenário | Canvas de origem | Conteúdo |
| --- | --- | --- |
| `teste2` do repositório | 2484 × 3512 | Fundo, três textos e assinatura |
| Cartão de aniversário da biblioteca instalada | 1748 × 1240 | Fundo e dez textos |
| Sintético pesado | 2400 × 3300 | Fundo e 150 textos; primeiro texto com cerca de 4.700 caracteres |

O legado abriu `teste2` com canvas 2480 × 3507 por sua conversão preexistente
de medidas físicas; o QML preservou o original. Portanto esse caso não tem
geometria rigorosamente idêntica nos dois editores. Nos outros dois cenários,
as dimensões coincidiram. Arial ausente é tratada pelo fallback já documentado.

O cenário sintético é gerado pelo próprio script, sem arquivos externos. Os
dados informam quantidade de objetos, presença de fundo e bytes do diretório.
O arquivo da biblioteca instalada não é distribuído com o benchmark.

## Resultados finais

P95: 95% das chamadas medidas ficaram abaixo desse tempo. Valores em milissegundos,
exceto memória em MiB. As faixas do cenário pesado correspondem a três processos
independentes por editor; os outros cenários tiveram uma rodada final por editor.

| Cenário/editor | Abertura API | Movimento P95 | Resize P95 | Confirmar movimento | Confirmar resize | Pico RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `teste2` legado | 222 | 0,092 | 0,298 | 0,425 | 0,449 | 151 |
| `teste2` QML | 1.118 | 0,720 | 1,743 | 7,612 | 7,420 | 288 |
| Biblioteca legado | 175 | 0,083 | 0,286 | 0,653 | 0,654 | 122 |
| Biblioteca QML | 999 | 0,748 | 1,795 | 10,113 | 10,631 | 257 |
| Pesado legado | 1.553–1.557 | 0,083–0,098 | 0,889–1,099 | 5,334–5,396 | 5,247–5,878 | 157,0–157,4 |
| Pesado QML | 1.109–1.165 | 0,712–0,908 | 4,519–4,583 | 40,596–45,577 | 42,566–43,340 | 324,6–325,1 |

### Antes/depois no QML pesado

| Medida | Antes das correções da etapa 7 | Depois, três repetições |
| --- | ---: | ---: |
| Abertura API | 10.420 ms | 1.109–1.165 ms |
| Movimento P95 | 16,983 ms | 0,712–0,908 ms |
| Resize P95 | 19,563 ms | 4,519–4,583 ms |
| Confirmação do movimento | 5.851,517 ms | 40,596–45,577 ms |
| Confirmação do resize | 5.851,638 ms | 42,566–43,340 ms |
| Pico RSS | 2.606,2 MiB | 324,6–325,1 MiB |

A linha de base pesada teve uma execução. A repetição final reforça a estabilidade
do resultado novo, mas não constitui um estudo estatístico amplo. A confirmação
de um gesto pesado ainda pode ocupar alguns frames; não foi prometido custo zero.

### Atualização gráfica observada

No QML, o proxy usa `frameSwapped` recebido na GUI após submissão de atualizações.
No legado, usa um callback após `Paint` do viewport Widgets. **Esses sinais medem
coisas diferentes e não servem para comparar diretamente a latência visual dos
dois editores.** Também não provam quando um pixel chegou ao monitor ou se cada
callback contém a última atualização: podem existir frames em andamento e eventos
agrupados. Por isso não são apresentados como FPS garantidos ou input-to-photon.

Nas três rodadas pesadas do QML, foram observados 85–87 ciclos associados às 90
atualizações de movimento. O P95 do proxy ficou entre 16,795 e 16,877 ms; no resize,
86–87 ciclos e P95 de 16,733–16,792 ms. Os dados brutos conservam as contagens,
intervalos de entrega e máximos, permitindo avaliar a diferença entre atualização
da API e ciclo gráfico observado.

Mover não regravou nenhum QPicture. Resize produziu 90 gravações do objeto
selecionado, com P95 abaixo de 4,6 ms neste cenário. Não foi acrescentado
coalescimento de resize sem necessidade demonstrada; ele continua sendo uma
possibilidade para textos maiores ou hardware mais lento.

## Regressões e exportação

- **68 testes** do editor/workspace aprovados em `offscreen` e **2 testes** de links PDF.
- **9 verificações** em X11/threaded aprovadas: arraste/resize, guias, foco/atalhos,
  pan, identidade/ordem das camadas e três fluxos do workspace.
- Novo teste impede que listas do documento e HTML bruto voltem aos estados
  consumidos pelos bindings QML. Outro verifica preservação da linha lateral
  ao mover, além da identidade da pintura e ordem já verificadas.
- A suíte de ponta a ponta agora conecta o canvas antes de exercitar persistência
  e geração. Os três modelos do repositório conservaram os pixels de saída após
  salvar/reabrir. PNG, PDF individual/único, links e imposição retrato/paisagem
  passaram; o cenário de PDF rasterizado independentemente pelo Poppler passou.
- `--check` e `git diff --check` aprovados. Os PNG/PDFs desta rodada foram guardados
  em `/tmp/comsoc-stage7-validation/`; são temporários e recriáveis pelos testes.

## Reproduzir

Executar a partir da raiz, com uma sessão X11 acessível:

```bash
QT_QPA_PLATFORM=xcb QSG_RENDER_LOOP=threaded .venv/bin/python features/editor_qml/benchmark_canvas.py \
  --editor qml --output /tmp/pesado-qml.json
QT_QPA_PLATFORM=xcb QSG_RENDER_LOOP=threaded .venv/bin/python features/editor_qml/benchmark_canvas.py \
  --editor legacy --output /tmp/pesado-legado.json
```

Adicionar `--model models/teste2/template_v3.json` para comparar o modelo real.
Repetir cada processo para observar variação. O script possui watchdog de 60 s
e encerra em erro se o gesto não puder começar. O parâmetro `--samples` controla
a quantidade de atualizações por fase (padrão: 90).

```bash
QT_QPA_PLATFORM=offscreen COMSOC_VALIDATION_ARTIFACTS=/tmp/comsoc-stage7-validation \
  .venv/bin/python -m unittest discover -s features/editor_qml/tests -v
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```

A avaliação do operador com seus modelos e a prova física de impressão permanecem
necessárias antes de mudar o editor padrão. A presente etapa encerra o plano
técnico de correção/medição do canvas; não aposenta o editor antigo.
