# FORNAX Forge — Referência funcional da etapa 3

Esta é a referência reproduzível anterior à remoção da interface legada. Ela registra o comportamento que as etapas 4 a 7 devem preservar.

## Matriz de regressão

| Fluxo | Evidência automatizada | Estado em 16/09/2026 |
|---|---|---|
| Modelos antigos e atuais | normalização v3/v4, migração, assets e três modelos reais de `models/` | aprovado |
| Editor e histórico | criação, seleção, undo/redo, ciclo de abertura e fechamento | aprovado |
| Duas páginas | isolamento, dimensões comuns, cópia entre páginas e ordem frente/verso | aprovado |
| Máscaras | criação, edição, cancelamento, cópia, renderização e restrição de link à forma | aprovado |
| Grupos | agrupamento, camadas, transformação proporcional, texto rico, máscaras e histórico | aprovado |
| Fontes e texto rico | métricas, estilos por trecho, edição no canvas e renderização | aprovado |
| Dados em lote | colagem tabular, texto rico, fórmulas, campos funcionais e atualização do preview | aprovado |
| Imagens dinâmicas | resolução externa, ambiguidades, enquadramento, cache e duas páginas | aprovado |
| Geração | PNG, PDF por item, PDF agrupado, links e nomes de saída | aprovado |
| Imposição | capacidade, página parcial, rotação automática e duplex frente/verso | aprovado |
| Interface | workspace e editor abrem, exibem e fecham corretamente em Qt offscreen | aprovado |
| Recursos | temas, traduções e caminhos dos ícones | aprovado |

## Comandos de referência

Suíte principal:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests
```

Suíte do editor:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest \
  features.editor.test_canvas_edit \
  features.editor.test_draw_shapes \
  features.editor.test_groups \
  features.editor.test_layers \
  features.editor.test_masks \
  features.editor.test_pages \
  features.editor.test_window_lifecycle
```

Em 16/09/2026, a primeira suíte concluiu **107 testes e 10 subtestes** em 31,26 s. A segunda concluiu **59 testes** em 6,00 s. Os avisos `propagateSizeHints()` e `raise()` são limitações esperadas do plugin Qt offscreen e não ocorreram como exceções no aplicativo.

## Referência de desempenho

As medições abaixo servem para detectar regressões grandes. Não são metas rígidas de hardware nem substituem profiling quando houver alteração relevante.

| Cenário | Resultado nesta máquina |
|---|---:|
| Colar 500 linhas por 5 campos | 39,5 ms de colagem + 19,6 ms de eventos |
| Renderizar 200 itens do modelo A4 `teste2`, com cache estático | 3,833 s; 19,16 ms por item |
| Renderizar `teste` após normalização v3 → v4 | 2,1 ms |
| Renderizar `teste2` após normalização v3 → v4 | 127,0 ms |
| Renderizar `teste3` após normalização v3 → v4 | 110,8 ms |

Os três modelos produziram imagens válidas; `teste` gerou 1000 × 1000 px e `teste2`/`teste3` geraram 2484 × 3512 px.

## Limites desta referência

- A validação foi executada no Linux e em modo offscreen. Aparência, atalhos nativos, diálogos e empacotamento ainda precisam ser conferidos nos três sistemas na etapa 7.
- A equivalência de impressão duplex está coberta por geometria e arquivos gerados. Uma prova física depende de impressora, driver, alimentação e configuração de virada e continua sendo uma verificação manual de distribuição.
- Fotografias reais são exercitadas pelo mesmo caminho de `QImage` usado nos testes de imagem dinâmica e máscara. Uma revisão visual com o conjunto final de exemplos deve acompanhar a preparação do tutorial e dos pacotes.

## Fechamento de escopo

Não foi identificada outra função indispensável antes da limpeza estrutural. Imagens dinâmicas, grupos proporcionais, máscaras, frente e verso, imposição e dados em lote formam a referência funcional atual. O tutorial permanece deliberadamente após a limpeza para não documentar uma estrutura transitória.

