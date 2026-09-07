# Novo editor — decisões de comportamento e arquitetura

Este documento registra as decisões tomadas para o futuro editor localizado em
`features/editor_qml/`. Ele deve servir como referência durante a implementação,
para que a nova interface preserve o que funciona no editor antigo sem herdar
limitações que não fazem mais sentido.

## Convenções usadas neste documento

- **Novo editor:** `features/editor_qml/`.
- **Editor antigo:** `features/editor/`.
- **Canvas:** área na qual o documento e seus objetos são exibidos e manipulados.
- **Inspector:** painel contextual com as propriedades do objeto selecionado.

## Estado atual do novo editor

O novo editor ainda é um protótipo visual. Ele não está conectado ao modelo de
dados, renderer, persistência, camadas, histórico ou demais comportamentos do
editor antigo. Portanto, os elementos atualmente presentes no QML representam
uma intenção visual e podem ser alterados para atender às decisões deste
documento.

## Edição de texto diretamente no canvas

### Decisão

No novo editor, o conteúdo dos objetos de texto será editado diretamente na
caixa desenhada no canvas.

O campo de conteúdo duplicado que atualmente aparece no inspector não fará
parte do fluxo principal e deverá ser removido. O inspector continuará sendo
usado para propriedades e comandos relacionados ao texto, mas não como o local
normal de digitação do seu conteúdo.

Essa decisão não exige mudar o formato persistido dos modelos nem o renderer.
Ela muda principalmente a forma como o usuário interage com o conteúdo.

### Comparação com o editor antigo

No editor antigo, o texto exibido no canvas não é diretamente editável. O
usuário seleciona uma caixa e altera seu HTML por meio de um `QTextEdit`
separado, localizado no painel lateral. Essa separação existe por causa da
implementação atual com `QGraphicsTextItem`; ela não representa uma regra de
negócio que precise ser preservada.

O novo editor deverá preservar do editor antigo:

- o conteúdo HTML compatível com o renderer;
- as variáveis entre chaves;
- os trechos opcionais delimitados por barras verticais;
- a formatação parcial, como negrito, itálico e sublinhado;
- fonte, tamanho, cor, alinhamentos, recuo e entrelinha;
- a integração com camadas, seleção, histórico e persistência;
- o resultado visual produzido pelo renderer como referência final.

O novo editor não deverá preservar a obrigação de digitar em um campo lateral.

### Comportamento esperado

| Ação | Resultado esperado |
|---|---|
| Clique simples em uma caixa de texto | Seleciona a caixa para manipulação. |
| Arraste com a caixa selecionada | Move a caixa, desde que ela não esteja em modo de edição. |
| Duplo clique na caixa selecionada | Entra no modo de edição de texto. |
| `Enter` com uma única caixa de texto selecionada | Entra no modo de edição de texto. |
| Clique e arraste durante a edição | Seleciona caracteres; não move a caixa. |
| `Delete` ou `Backspace` durante a edição | Remove caracteres do conteúdo. |
| `Delete` fora da edição | Remove o objeto selecionado, conforme o fluxo de objetos. |
| `Ctrl+B`, `Ctrl+I` e `Ctrl+U` durante a edição | Formata a seleção ou o texto que será digitado. |
| `Esc` durante a edição | Encerra a edição, preservando as alterações feitas. |
| Clique fora da caixa durante a edição | Confirma o conteúdo e encerra a edição. |
| Comando “Inserir variável” | Insere ou transforma texto na posição/seleção atual do cursor. |
| Comando “Trecho opcional” | Aplica a marcação ao trecho selecionado no canvas. |

O comportamento exato de `Enter` para textos multilinha deverá continuar sendo
natural: depois que o modo de edição estiver ativo, `Enter` cria uma nova linha.
O comando para entrar na edição só se aplica quando o foco ainda pertence ao
modo de seleção de objetos.

### Estados visuais e de interação

Uma caixa de texto deve possuir pelo menos dois estados claramente separados:

1. **Modo de seleção:** mostra contorno e alças; permite mover, redimensionar,
   girar e manipular o objeto.
2. **Modo de edição:** mostra cursor e seleção de caracteres; impede que um
   gesto destinado ao texto mova ou redimensione acidentalmente o objeto.

Durante a edição:

- o cursor deve ser o cursor de texto;
- as alças podem ser ocultadas ou temporariamente desativadas;
- atalhos de texto devem ter prioridade sobre atalhos de objeto;
- comandos do inspector devem atuar sobre o cursor ou a seleção textual ativa;
- a edição deve permanecer possível em objetos com rotação, observando a
  legibilidade e o posicionamento correto do cursor;
- em zoom muito baixo, poderá ser oferecida ampliação temporária para facilitar
  a digitação, sem alterar o tamanho real do objeto.

### Papel do inspector

O inspector continua importante, mas passa a controlar propriedades e ações da
seleção. Para objetos de texto, ele deverá conter, conforme necessário:

- fonte, tamanho e cor;
- negrito, itálico e sublinhado;
- alinhamento horizontal e vertical;
- recuo e entrelinha;
- comportamento de link;
- comandos para inserir variável e criar trecho opcional;
- identificação de que o objeto contém conteúdo dinâmico.

O inspector não deve manter um segundo editor de conteúdo permanentemente
sincronizado com o canvas. Isso criaria dois focos de edição, duplicaria estados
de cursor e seleção e tornaria undo/redo mais sujeito a inconsistências.

Se testes futuros demonstrarem necessidade, poderá existir uma ação secundária
“Editar em painel” para textos muito longos, objetos muito girados ou situações
de acessibilidade. Ela será uma alternativa explícita, não o fluxo padrão nem
um campo sempre visível.

## Fonte de verdade e fluxo de dados

Cada objeto de texto deverá possuir um único modelo como fonte de verdade. O
componente visual no canvas e o inspector apenas editam esse modelo.

```text
Modelo do objeto de texto
  ├── conteúdo HTML
  ├── fonte, tamanho e cor
  ├── alinhamentos, recuo e entrelinha
  ├── propriedades dinâmicas e link
  └── posição, dimensões, rotação e ordem
             │
             ├── componente editável no canvas
             ├── inspector contextual
             ├── persistência do modelo
             └── renderer baseado em QTextDocument
```

Fluxo recomendado para uma sessão de edição:

1. Ao entrar no modo de edição, o componente recebe o estado atual do modelo.
2. A digitação altera uma versão de trabalho do conteúdo.
3. Comandos de formatação atuam sobre o documento e a seleção atuais.
4. O HTML passa pela mesma normalização e higienização usada pelo restante do
   sistema.
5. Ao confirmar ou sair da edição, o resultado é gravado no modelo.
6. O canvas, a lista de variáveis, o inspector e a persistência são atualizados
   a partir desse modelo.

Não deve haver sincronização circular entre dois campos de conteúdo.

## Compatibilidade com o renderer

O renderer atual usa `QTextDocument` e conteúdo HTML. Esse contrato deverá ser
mantido inicialmente para garantir compatibilidade com os modelos existentes e
reduzir divergências entre a tela e o resultado exportado.

O componente QML deve respeitar, tanto quanto possível:

- margem de documento igual a zero;
- mesma largura útil e mesmas regras de quebra de linha;
- mesma fonte e tamanho;
- mesma formatação parcial representada no HTML;
- mesmos alinhamentos, recuo e entrelinha;
- mesma lógica de alinhamento vertical;
- substituição de variáveis e ocultação de trechos opcionais.

O renderer continua sendo a referência canônica para a saída final. Diferenças
visuais relevantes entre canvas e exportação deverão ser tratadas como defeito.

## Variáveis e trechos opcionais

O sistema atual reconhece variáveis no formato:

```text
{Nome}
{Nome_completo}
{Campo123}
```

O nome interno aceita letras sem acento, números e subtraços. Espaços, acentos e
outros símbolos não são reconhecidos pela expressão atual. Por esse motivo, o
exemplo visual `{Nome completo}` presente no protótipo deverá ser substituído
por `{Nome_completo}` ou a regra de nomes deverá ser deliberadamente alterada
em uma decisão futura, acompanhada de migração e testes.

No modo de edição direta:

- “Inserir variável” deve usar a seleção textual ou a posição atual do cursor;
- “Trecho opcional” exige uma seleção que contenha pelo menos uma variável
  válida;
- mensagens de validação devem ser apresentadas próximas ao contexto da edição;
- realce visual de variáveis pode ser usado, desde que não altere o HTML salvo
  nem a aparência final exportada.

## Histórico e atalhos

O histórico global do documento e o histórico interno da digitação precisam ser
coordenados explicitamente.

- Uma sessão contínua de digitação deve produzir uma operação coerente no
  histórico do documento, e não um snapshot completo a cada caractere.
- Enquanto o texto estiver em edição, `Ctrl+Z` e `Ctrl+Shift+Z`/`Ctrl+Y` devem
  priorizar alterações de texto da sessão atual.
- Depois que a edição for confirmada, desfazer no documento deve conseguir
  restaurar o conteúdo anterior da caixa.
- Formatações, inserção de variáveis e trechos opcionais devem participar do
  mesmo histórico.
- Atalhos globais que poderiam duplicar, apagar ou renomear objetos não devem
  disparar enquanto o usuário estiver digitando.

## Colagem e higienização

A edição direta deve preservar a proteção já existente contra formatação
indesejada vinda da área de transferência. Ao colar conteúdo externo, deverão
ser removidos ou normalizados, conforme as regras atuais:

- família e tamanho de fonte externos;
- cores e fundos externos;
- links HTML inesperados;
- entrelinha externa;
- estilos de títulos incompatíveis;
- marcações que não façam parte do subconjunto HTML suportado.

A colagem deve preservar o texto e somente as formatações explicitamente
suportadas pelo COMSOC.

## Critérios de aceite da edição direta

A funcionalidade será considerada pronta quando:

- for possível criar, selecionar, mover e editar uma caixa sem ambiguidade;
- o usuário conseguir editar textos de uma ou várias linhas no próprio canvas;
- seleção textual e seleção do objeto não entrarem em conflito;
- variáveis e trechos opcionais puderem ser criados a partir do cursor no
  canvas;
- formatação parcial sobreviver ao salvamento, reabertura e exportação;
- atalhos se comportarem corretamente nos modos de seleção e edição;
- undo/redo restaurar conteúdo e formatação de maneira previsível;
- copiar e colar não introduzir estilos externos incompatíveis;
- modelos produzidos pelo editor antigo continuarem abrindo corretamente;
- o resultado exportado permanecer visualmente coerente com o canvas;
- o campo lateral duplicado não for necessário para completar o fluxo normal.

## Decisões registradas

### 7 de agosto de 2026 — Conteúdo editável diretamente no canvas

- Definida a edição direta no canvas como fluxo principal do novo editor.
- Definida a remoção do campo lateral duplicado de conteúdo.
- Mantido o inspector para propriedades e comandos contextuais.
- Mantido o modelo do objeto como única fonte de verdade.
- Mantida a compatibilidade inicial com HTML, modelos existentes e renderer
  baseado em `QTextDocument`.
- Definida a necessidade de modos explícitos de seleção e edição.
- Registrados os cuidados com foco, atalhos, undo/redo, zoom, rotação, colagem,
  variáveis e fidelidade do renderer.

## Questões para decisões futuras

- O modo de edição será iniciado somente por duplo clique e `Enter`, ou também
  por um segundo clique em uma caixa já selecionada?
- Qual será o agrupamento temporal exato de digitação no histórico global?
- Objetos girados serão editados na própria rotação ou temporariamente
  apresentados sem rotação?
- A ampliação automática em zoom baixo será necessária após testes de uso?
- Haverá um editor em painel opcional por acessibilidade ou para textos longos?
- O formato permitido para nomes de variáveis será mantido ou ampliado?

