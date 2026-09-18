# FORNAX Forge — Auditoria final da limpeza

Auditoria executada em 17/09/2026 sobre a branch `novo_main`, usando como referência [VALIDACAO_ETAPA_3.md](VALIDACAO_ETAPA_3.md).

## Resultado funcional

| Área | Evidência | Resultado |
|---|---|---|
| Suíte principal | 111 testes e 10 subtestes | aprovado |
| Editor | 60 testes de canvas, formas, grupos, camadas, máscaras, páginas e ciclo de vida | aprovado |
| Modelos reais | `teste`, `teste2` e `teste3` normalizados e renderizados | aprovado |
| Interface | editor aberto e fechado em Qt offscreen | aprovado |
| Traduções | todo literal estático passado a `tr()` existe nos catálogos inglês e espanhol | aprovado |
| Recursos | SVGs referenciados existem e carregam; não foram encontrados SVGs sem consumidor | aprovado |
| Código e scripts | compilação Python, `bash -n`, whitespace e referências de recursos | aprovado |

As referências compatíveis com v3, migração de dados antigos e pintura de fundo histórico continuam presentes por serem compatibilidade ativa. Nenhuma interface antiga permanece no ponto de entrada ou é construída de forma oculta.

## Desempenho comparado

| Cenário | Etapa 3 | Etapa 7 |
|---|---:|---:|
| Colar 500 × 5 células | 39,5 ms + 19,6 ms de eventos | 36,34 ms + 16,53 ms de eventos |
| Renderizar 200 itens de `teste2` | 3,833 s | 3,784 s |
| Renderizar `teste` | 2,1 ms | 1,7 ms |
| Renderizar `teste2` | 127,0 ms | 124,8 ms |
| Renderizar `teste3` | 110,8 ms | 107,9 ms |

As diferenças são normais para medições locais e não indicam regressão relevante.

## Limpeza concluída nesta auditoria

- Removidas 38 fontes não registradas nem consumidas: variantes Inter 24 pt, 28 pt e variáveis. O pacote deixa de carregar cerca de 14 MB de recursos sem uso.
- Mantidas as variantes estáticas Inter 18 pt, inclusive os pesos reais usados pelo texto rico, junto da licença OFL.
- Removidos arquivos `.gitkeep` de diretórios que já contêm recursos.
- Fixada a versão PySide6 6.11.0 nos requisitos e no manifesto Flatpak para reduzir variações visuais entre ambientes.
- Integrados ao sistema de tradução os textos do menu de contexto da tabela.
- Removida uma duplicação sem efeito no processamento da colagem e um import sem consumidor.
- Atualizada a documentação de portabilidade para separar decisões implementadas de validações externas.

## Limites da validação

Esta auditoria comprova o estado no Linux e em Qt offscreen. Antes de publicar os pacotes finais ainda é necessário:

- construir e inspecionar os pacotes candidatos de cada sistema;
- validar Windows nas escalas escolhidas e macOS em tela Retina;
- revisar diálogos nativos, atalhos e controles de janela em cada sistema;
- executar uma prova física duplex;
- concluir o inventário e os textos integrais das licenças de terceiros;
- definir a licença própria do FORNAX Forge e confirmar a licença do conjunto de ícones.

Essas tarefas dependem dos ambientes e decisões de distribuição. Elas não representam dívida de implementação escondida no fluxo atual.
