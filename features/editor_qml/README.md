# COMSOC Studio — editor QML integrado

Frontend Qt Quick conectado ao formato de modelos e ao renderer existentes por
`bridge.py`. Camadas e layout de texto compartilham serviços com o backend.
O editor antigo permanece intacto e pode ser aberto em paralelo.

## Executar

No aplicativo principal, escolha **Novo editor QML** no seletor próximo à lista de
modelos. Os botões Novo e Editar usam essa escolha, mantendo o legado disponível.
Salvar atualiza a biblioteca e a prévia; os valores das colunas mantidas na
planilha são preservados. Nesse modo, Salvar como cria o modelo na biblioteca.

Na raiz do projeto:

```bash
.venv/bin/python features/editor_qml/main.py
.venv/bin/python features/editor_qml/main.py --model models/teste/template_v3.json
```

No Windows, com o ambiente virtual ativo, use `python` no lugar de `.venv/bin/python`.

O menu **Modelos** contém Novo, Abrir e Salvar como. Use Salvar como para preparar
uma cópia de comparação. Atalhos: Ctrl+N, Ctrl+O, Ctrl+S e Ctrl+Shift+S.
O menu também oferece dimensões da página em pixels e tamanho de saída em mm.

## Edição

- Adicione textos, formas, imagens e assinaturas pela coluna esquerda.
- Formas começa com um retângulo. Abra Propriedades para escolher retângulo, quadrado, elipse ou círculo, alterar o preenchimento e configurar o contorno. Quadrado e círculo mantêm proporção 1:1.
- Contorno está disponível em Propriedades para formas e textos, com cor e espessura em pixels. No texto, contorna os glifos e mantém a caixa invisível.
- Selecione no canvas ou na lista; use o olho e o cadeado para visibilidade/bloqueio.
- Arraste objetos para mover; use a alça inferior direita ou os campos superiores para redimensionar. Medidas de edição são em pixels.
- Com foco no canvas, as setas movem 1 px e Shift+setas movem 10 px. Ctrl+D duplica a camada fora da edição de texto.
- Em Propriedades, substitua imagens preservando geometria e ajuste a coluna usada pelo link. Clique com o botão direito em uma guia desbloqueada para editar sua posição ou excluí-la.
- Dê duplo clique no texto para editar. Ctrl+Enter, Esc, seleção de outra camada ou salvar concluem. Abrir os controles laterais mantém a seleção de caracteres.
- Abra Texto para fonte, tamanho, cor, alinhamentos, entrelinha e recuo. Durante a edição, os estilos atuam na seleção ou na próxima digitação; fora dela, no texto inteiro. Use também Ctrl+B/I/U.
- No texto, clique com o botão direito para inserir variável (Ctrl+1) ou tornar a seleção um trecho opcional (Ctrl+2). As marcações `{Nome}` e `|Cargo: {Cargo}|` também podem ser digitadas.
- Arraste os campos em Campos da tabela para alterar a ordem das colunas.
- Arraste camadas para reordenar livremente textos, formas, imagens e assinaturas.
- Use Ctrl+Z e Ctrl+Shift+Z para desfazer/refazer. Durante a edição, atuam no texto; ao concluir, a sessão entra no histórico do documento.

Formas são gravadas no modelo sem precisar de imagens externas. Formas e contornos
são desenhados na prévia e pelo renderer de geração. Fundos antigos são convertidos
em imagens comuns na base das camadas ao abrir; essa
conversão só é gravada quando o modelo é salvo. A prévia usa o renderer compartilhado.

O editor antigo ainda não exibe formas nem contornos e não preserva esses campos,
nem os campos novos de ordem e estilos, ao salvar.
Para comparar, mantenha cópias separadas dos modelos modernizados e dos antigos.

A prévia é gerada em segundo plano e exibe seu estado no rodapé. Fontes ausentes
aparecem em um aviso persistente; seus nomes originais são preservados no arquivo.

Veja [PENDENCIAS_INTEGRACAO.md](PENDENCIAS_INTEGRACAO.md) para a matriz completa de
recursos conectados, diferenças de frontend/backend e tarefas futuras.
O plano de correção da responsividade, com etapas concluídas e ponto de retomada,
está em [PLANO_DESEMPENHO_CANVAS.md](PLANO_DESEMPENHO_CANVAS.md).
O canvas compõe objetos independentes com cache de pintura e acompanha o mouse
durante arraste/redimensionamento. Soltar confirma uma ação no histórico; Esc
cancela o gesto. Texto recalcula a quebra de linhas durante o resize, respeitando
rotação, proporção e bloqueios. Atualizações de geometria reutilizam metadados,
layout e pintura; fontes são verificadas quando os dados tipográficos mudam.
Guias também acompanham o mouse e podem ser canceladas com Esc. O botão do meio
move a área visível; setas/Shift movimentam objetos quando o canvas tem foco.
Atalhos de documento respeitam campos de texto em edição. As sete etapas do plano
de responsividade foram concluídas. As medições, correções finais e limites da
comparação com o legado estão em
[RELATORIO_DESEMPENHO_CANVAS.md](RELATORIO_DESEMPENHO_CANVAS.md).
Os resultados dos testes com modelos reais, PNG/PDF e imposição estão em
[VALIDACAO_FLUXO_COMPLETO.md](VALIDACAO_FLUXO_COMPLETO.md). A impressão física ainda
exige conferência; o legado continua como padrão, respeitando a escolha salva.

## Verificar

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python features/editor_qml/main.py --check
QT_QPA_PLATFORM=offscreen .venv/bin/python features/editor_qml/main.py --model models/teste2/template_v3.json --screenshot /tmp/editor-qml.png
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s features/editor_qml/tests -v
```
