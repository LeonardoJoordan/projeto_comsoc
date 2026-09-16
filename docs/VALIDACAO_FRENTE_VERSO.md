# Validação de modelos com frente e verso

Data: 16/09/2026  
Plataforma executada: Linux, Python 3.13.11, Qt 6.11.0  
Branch: `novo_main`  
Commit-base da execução: `6822b450d3243845f308643b10d1bad9476ce66b`

## Resultado atual

A validação automatizada e a inspeção dos artefatos renderizados foram concluídas. A funcionalidade ainda não deve ser considerada liberada para todas as plataformas enquanto faltarem a inspeção nativa em Windows e macOS e uma nova prova física duplex depois da correção de orientação do verso em paisagem.

## Suítes executadas

- 94 testes e 10 subtestes em `tests/`.
- 30 testes do editor Widgets.
- Todos passaram na execução desta etapa.
- A prévia de folha foi interrompida enquanto processava 800 registros; a thread encerrou dentro do limite de cinco segundos e não permaneceu ativa.

Os testes cobrem contrato v3/v4, duas páginas, histórico, assets, fundos, texto rico, Amiri e alinhamento vertical, placeholders, links, Cópias, PNG, PDF por item, PDF agrupado, imposição, folha incompleta, orientação retrato/paisagem, cache, temas, traduções e falhas parciais.

## Compatibilidade gráfica

Três modelos reais preservados na Etapa 0 foram carregados pelo adaptador atual. A renderização do v3 original e a visão normalizada da página 1 foram idênticas pixel a pixel nos três casos. Os hashes dos JSONs de origem permaneceram inalterados.

| Modelo preservado | Dimensões | Resultado |
| --- | ---: | --- |
| `teste` | 1000 × 1000 px | idêntico; origem intacta |
| `teste2` | 2484 × 3512 px | idêntico; origem intacta |
| `teste3` | 2484 × 3512 px | idêntico; origem intacta |

A fixture rica continuou com 320 × 200 px. Formas, contorno, transparência, imagem, assinatura e link permaneceram iguais. A região da caixa de texto mudou intencionalmente: a captura antiga continha o defeito em que o HTML da célula substituía fonte e tamanho do modelo; a saída atual preserva corretamente a tipografia do placeholder. O hash atual é `d213677b364257247cdf3ff6b1c05385ded7cde66073c87bf0ab9f4b47efbe65`.

## Arquivos e sequência

Foram confirmados por testes:

- PNGs `_pag1` e `_pag2` com um único nome-base por documento;
- verso vazio exportado quando a segunda página existe;
- ausência de publicação parcial quando a segunda página falha;
- PDF por item com duas páginas;
- PDF agrupado na ordem documento 1/frente, documento 1/verso, documento 2/frente, documento 2/verso;
- dimensões físicas dentro da tolerância de 0,18 mm;
- links associados à página e à região correta;
- imposição duplex como duas faces da mesma folha física;
- preservação das vagas vazias na última folha;
- quatro itens mantidos na orientação paisagem, sem a regressão que reduzia a capacidade para dois.

A fixture de uma página produziu PDF de 80,081 × 50,094 mm, uma página e um link, como na referência anterior.

## Biblioteca, transporte e recuperação

Um ensaio temporário criou um documento de duas páginas com asset compartilhado, exportou-o para ZIP, extraiu, instalou, moveu de pasta, duplicou, renomeou e reabriu. As duas páginas e o asset foram preservados.

Os testes automatizados também confirmaram:

- falha de gravação não substitui o documento válido;
- um novo salvamento mantém o v4 anterior em `template_v4.json.bak`;
- o verso removido pode ser recuperado pelo backup;
- assets usados somente no verso ou na recuperação não são apagados;
- v4 inválido não provoca abertura silenciosa do v3;
- instalação importada troca documento e assets em uma operação recuperável.

Para retorno manual, feche o aplicativo, preserve a pasta atual do modelo e substitua `template_v4.json` por uma cópia validada de `template_v4.json.bak`. Modelos v3 permanecem intactos até o primeiro salvamento no editor atual.

## Desempenho comparativo

Medições repetidas na mesma máquina e com a mesma fixture:

| Operação | Referência | Etapa 10 | Variação |
| --- | ---: | ---: | ---: |
| Primeira prévia | 13,187 ms | 14,266 ms | +8,2% |
| Prévia aquecida | 0,941 ms | 0,947 ms | +0,6% |
| Abertura do editor | 21,172 ms | 21,022 ms | −0,7% |
| 200 movimentos | 1,520 ms | 1,559 ms | +2,6% |
| 100 edições de texto | 17,082 ms | 16,383 ms | −4,1% |
| Colagem de 500 linhas | 24,023 ms | 24,109 ms | +0,4% |
| Navegação por 500 linhas | 0,635 ms | 0,617 ms | −2,8% |
| Renderização de 100 documentos | 96,175 ms | 93,340 ms | −2,9% |

O pico registrado caiu de 124.576 KiB para 123.504 KiB, sem crescimento adicional durante o lote. A variação da primeira prévia representa aproximadamente 1,1 ms e não se repete com o cache aquecido.

Os relatórios locais completos estão em `.validation/front_back_baseline/report.json` e `.validation/front_back_stage10/report.json`. Esse diretório é ignorado pelo Git.

## Pendências externas antes da liberação

- Inspecionar a interface nativa e o fluxo completo em Windows.
- Inspecionar a interface nativa e o fluxo completo em macOS.
- Fazer uma passagem visual final da interface nativa Linux com os cinco temas e os três idiomas.
- Reimprimir a prova duplex em paisagem, usando alimentação A4 de pé e virada lateral, e confirmar orientação e coincidência depois do corte.
- Se a distribuição oferecer outras formas de virada, criar contratos e provas próprios; atualmente somente o padrão aprovado acima é suportado.

Testes headless e inspeção de imagens não substituem essas verificações.
