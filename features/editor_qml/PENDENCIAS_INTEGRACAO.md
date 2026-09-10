# Integração do editor QML — estado e ajustes futuros

Atualizado em 07/09/2026.

## Escopo e arquitetura

As etapas 1 (camadas), 2 (edição de texto), 3 (formas) e 4 (contorno) foram implementadas. Além de
`features/editor_qml/`, foram ajustados o renderer em `features/generator/` e
os serviços compartilhados `core/document_layers.py`, `core/text_layout.py` e
`core/object_style.py`.
O editor Widgets em `features/editor/` permanece intacto. O workspace recebeu a
escolha do editor e atualização após salvar. A revisão de funcionamento também
ajustou histórico, detecção de fontes e geração assíncrona de miniaturas.
Os dois editores têm entradas independentes e podem ser usados em paralelo.

`bridge.py` adapta o frontend ao formato `template_v3.json` e usa `HistoryManager`.
O canvas compõe objetos independentes com pintura derivada do renderer; miniaturas
e exportação usam a renderização da página. O canvas não usa mais o
certificado fictício do protótipo. O JSON v3 mantém as coleções antigas e recebe campos opcionais:
`object_id` estável em cada objeto, `layer_order` com os IDs do fundo para o topo
e `rich_text_version: 1` em textos com estilos por trecho. Arquivos sem esses
campos continuam sendo renderizados pelas regras anteriores.

## Funcionalidades conectadas

| Área | Funcionamento atual |
| --- | --- |
| Modelos | Novo, abrir, salvar e salvar como pelo menu Modelos. A entrada também aceita `--model arquivo.json`. |
| Persistência | JSON gravado atomicamente; preserva chaves desconhecidas, configuração de exportação/impressão e atributos sem controles no QML. |
| Assets | Resolve caminhos relativos ao modelo. Salvar em outra pasta copia imagens para `assets/`, com referências relativas no JSON. |
| Prévia | Renderer em worker, limitado a 1600 px no maior lado. Há um trabalho ativo e somente o pedido mais recente na fila; resultados obsoletos são descartados. O salvamento confirma a miniatura antes de notificar o workspace. |
| Objetos | Adicionar texto, forma, imagem e assinatura; selecionar, renomear, duplicar, excluir, ocultar e bloquear. |
| Geometria | X/Y, largura/altura, rotação, opacidade e manter proporção. Unidades do canvas em pixels e fonte em pontos; medidas físicas existentes são preservadas. |
| Manipulação | Arraste e resize acompanham o mouse; apenas o objeto alterado é atualizado. Soltar confirma uma ação no histórico; Esc cancela. |
| Texto | Duplo clique ou Enter sobre texto selecionado abre edição rica no canvas. Ctrl+Enter, Esc, seleção de outra camada ou salvar concluem. O inspector mantém a seleção de caracteres durante a formatação. |
| Tipografia | Fonte, tamanho, cor e B/I/U aplicam-se à seleção de caracteres ou à próxima digitação durante a edição; fora dela, ao texto inteiro. Alinhamento horizontal, entrelinha e recuo atuam nos parágrafos selecionados; vertical na caixa. |
| Variáveis | Colunas derivadas de `{variavel}` e links habilitados. Campos da tabela permite reordenação por arraste. Menu de contexto e Ctrl+1 inserem variável; Ctrl+2 envolve a seleção como trecho opcional. A resolução suporta marcações divididas entre estilos HTML. |
| Links | Ativa Link no PDF em texto/imagem/forma, preservando a chave da coluna. Exportação do PDF continua no workspace. |
| Histórico | Desfazer/refazer com snapshots independentes. Salvar na mesma pasta mantém histórico; salvar em outra pasta reinicia-o para não usar referências relativas da origem. |
| Guias | Adicionar horizontal/vertical, mover ao vivo, mostrar/ocultar e bloquear. Soltar confirma um gesto no histórico; Esc cancela. Botão direito sobre uma guia desbloqueada permite editar posição ou excluir. |
| Navegação | Zoom, rolagem horizontal/vertical, pan com botão do meio e grade local. Atalhos respeitam campos em edição; trocar zoom cancela gestos pendentes. |
| Camadas | Lista única na ordem real da pintura. Arraste reordena livremente texto, forma, imagem e assinatura. IDs e ordem persistem ao salvar e no histórico. |

## Etapas 1 e 2 — detalhes concluídos

- Abertura converte `background_path` em uma imagem na base da lista, conservando
  posição, dimensões, opacidade, visibilidade e bloqueio. A conversão ocorre em
  memória; o arquivo original só muda quando o operador salva. `bg_props` permanece
  como metadado, sem papel de desenho. A imagem convertida aceita rotação e pode
  ser movida na lista após desbloquear.
- A ordem inicial de um modelo antigo segue sua geração anterior (fundo, imagens,
  textos e assinaturas). Os antigos `z_value` são sincronizados com a ordem única.
  O cache estático considera somente as imagens anteriores ao primeiro elemento
  dinâmico, evitando sobreposições erradas em lotes.
- `CanvasTextEditor` usa `QTextDocument`, cursor e layout compartilhados com o
  renderer. Zoom, rotação, alinhamentos, recuo e entrelinha usam as mesmas medidas.
  Durante a edição, camadas inferiores e superiores são renderizadas separadamente
  para conservar a sobreposição.
- Ctrl+B/I/U, seleção por mouse e teclado, copiar/recortar/colar e desfazer/refazer
  atuam no cursor. O histórico local de digitação é consolidado no histórico do
  documento ao concluir. Abrir e fechar edição sem mudar nada preserva o histórico.
- Variáveis e trechos opcionais têm comandos no menu de contexto, sem reintroduzir
  os botões removidos da lateral. As marcações aparecem durante a edição; a prévia
  final resolve os delimitadores conforme as regras do gerador.

### Limite de compatibilidade com o editor antigo

Modelos antigos continuam abrindo nos dois editores; o novo aceita arquivos
anteriores sem conversão no disco. O editor antigo também lê as coleções dos
novos arquivos, mas seu salvamento não preserva `layer_order`, `object_id` e
`rich_text_version`. Regravar nele pode restaurar a ordem por tipos e perder a
interpretação dos estilos por trecho. Compatibilidade de ida e volta dos recursos
novos permanece pendente; o editor antigo não foi alterado nesta etapa.

## Etapas 3 e 4 — formas e contorno concluídos

- **Formas:** o botão Formas adiciona um retângulo. Em Propriedades, é possível
  escolher Retângulo, Quadrado, Elipse ou Círculo, alterar o preenchimento pelo
  código hexadecimal ou seletor de cores e configurar o contorno.
- Formas são objetos vetoriais na coleção `shapes`, com `object_id` e participação
  em `layer_order`. Não dependem de arquivos de imagem. Aceitam mover, redimensionar,
  girar, ajustar opacidade, bloquear, ocultar, duplicar, excluir, reordenar e link
  no PDF. Quadrado e círculo mantêm largura e altura iguais.
- **Contorno:** disponível apenas para formas e textos, com ativação, cor e
  espessura de 0,1 a 100 pixels do modelo. O traço é centrado na borda da forma
  ou dos glifos. No texto, aplica-se ao objeto inteiro e a caixa permanece
  invisível. Não há sombra/desfoque nem contorno para imagens e assinaturas.
- Persistência: `shape_type`, `fill_color`, `width` e `height` definem a forma;
  `outline_enabled`, `outline_color` e `outline_width` definem o contorno.
  Campos ausentes significam contorno desativado, preservando modelos antigos.
- O renderer desenha os recursos tanto na prévia quanto nas imagens utilizadas
  pela geração de PNG/PDF e pelos lotes. O cache respeita formas intercaladas
  com texto, imagem e assinatura. O editor nativo de texto compartilha o mesmo
  contorno e reserva margem para não cortar o traço nos limites da caixa.
- As verificações específicas incluem cor de preenchimento/contorno nos pixels,
  opacidade, rotação, visibilidade, ordem e cache, links, histórico, gravação sem
  assets, reabertura, controles QML e igualdade da pintura de texto com o renderer.

O editor antigo não cria nem exibe formas da coleção `shapes`, não oferece
contorno e descarta esses campos ao salvar. Essa compatibilidade permanece
pendente junto à preservação da ordem e dos estilos por trecho descrita acima.

## Funcionalidades existentes sem interface equivalente ou com integração parcial

| Área | Pendência / decisão futura |
| --- | --- |
| Réguas e precisão | Réguas decorativas saíram ao conectar o canvas real. Faltam réguas calculadas, magnetismo, guias inteligentes e os modos avançados de zoom/pan do legado. Setas movem o objeto com foco no canvas; Shift aumenta o passo de 1 para 10 px. |
| Nomes de variáveis | A integração segue a expressão do renderer: letras ASCII, números e `_` entre chaves. Espaços/acentos nos nomes exigem revisão coordenada do backend. |
| Links | A chave de coluna pode ser editada no inspector. Duplicar mantém a coluna compartilhada; uma política de geração automática de colunas independentes continua como decisão futura. PDFs com imposição ainda não recebem os links dos cartões. |
| Seleção múltipla | Falta seleção em grupo, propriedades e ações coletivas, além das demais alças/modos de transformação. |
| Fontes | Famílias ausentes, incluindo estilos HTML por trecho, geram aviso persistente. Os nomes são preservados ao salvar e o Qt usa fallback visual. Submenu de variantes da família permanece pendente. |
| Desempenho | Plano de sete etapas concluído; medidos dois modelos reais e cenário de 150 textos. Correções reduziram transporte de estado QML e recriação da lista lateral. O legado continua mais leve por operação; salvamento/histórico permanecem síncronos. Ver RELATORIO_DESEMPENHO_CANVAS.md para números e limites. |
| Mensagens | Erros aparecem em diálogo, fontes ausentes em faixa persistente e estado da prévia/gravação no rodapé. Logs de salvamento também chegam ao workspace. Telemetria detalhada de operações longas continua futura. |
| Exportação/lotes | PNG/PDF, imposição, presets, quantidade e assinatura por registro continuam no workspace antigo. O novo editor salva modelos, mas não substitui a geração em lote. |
| Biblioteca/pacotes | O novo menu abre JSON. Gestão completa de modelos e pacotes ZIP continua no aplicativo principal. |
| Multipágina | Página 1 corresponde ao formato atual; não há criação/edição multipágina. |

## Etapas 5, 6 e 7 — escopo confirmado e concluído

O escopo confirmado foi: revisar formas/contorno já implementados, fechar lacunas
de funcionamento/interface e integrar a escolha do editor ao workspace.

- Formas e contorno mantêm criação, propriedades, persistência, histórico e
  renderização cobertos pelos testes anteriores.
- Controles inválidos voltam ao valor do modelo. Ações de camada respeitam
  bloqueio/seleção; Ctrl+D duplica fora da digitação e Ctrl+Y refaz. Salvar um
  estado sem alterações não apaga o histórico de refazer.
- O menu Modelos oferece dimensões em pixels e medidas físicas de saída em mm.
  As posições dos objetos são preservadas. Propriedades permite substituir a
  imagem/assinatura mantendo geometria, ID e ordem e editar a coluna do link.
- Fontes ausentes são informadas, inclusive em trechos HTML. O seletor conserva
  o nome solicitado e o JSON não é regravado com uma substituição silenciosa.
- A prévia usa QImage em worker, agrupa pedidos e ignora resultados ultrapassados.
  As propriedades das camadas são calculadas uma vez por alteração. Erros
  assíncronos voltam à interface; o encerramento aguarda o trabalho em curso.
- A lista “Editor legado / Novo editor QML”, junto ao seletor de modelo no
  workspace, define os botões Novo e Editar. A preferência é persistida; o
  padrão continua sendo o legado. Reabrir o mesmo arquivo no QML traz a janela
  existente para frente. O fluxo legado não foi substituído.
- O QML emite `modelSaved` somente após gravação bem-sucedida. O workspace
  recarrega modelo, biblioteca, colunas e prévia, preservando valores, formatação,
  quantidades e estado das assinaturas nas colunas mantidas. Salvar em uma janela
  de outro modelo não troca a seleção ativa do workspace.
- Quando aberto pelo workspace, Novo/Salvar como gravam em
  `models/<nome>/template_v3.json`, copiando assets. Arquivos abertos de fora
  dessa biblioteca são salvos como cópia nela. O launcher independente conserva
  a escolha livre do caminho.
- Fechar o workspace respeita salvar/descartar/cancelar nas janelas QML. Abrir
  modelos modernizados no legado exibe aviso sobre os campos que ele não conserva.
- A atualização de miniaturas do workspace usa a resolução reduzida desde a
  renderização e descarta resultados de modelos alterados durante o trabalho.

Continuam fora destas etapas os recursos de precisão avançada, multisseleção,
variantes de fontes, multipágina e a aposentadoria do editor legado. As pendências
restantes estão na tabela acima.

## Usar os dois editores

Inicie o aplicativo normalmente com `python main.py`. No seletor próximo ao
modelo, escolha Editor legado ou Novo editor QML e use Novo ou Editar.

Editor novo, a partir da raiz:

```bash
.venv/bin/python features/editor_qml/main.py --model models/teste/template_v3.json
```

Sem `--model`, inicia vazio. O menu Modelos oferece Novo, Abrir e Salvar como.
Salvar como permite uma cópia de teste e sugere a pasta de modelos do aplicativo,
com nome `template_v3.json`, para que o workspace possa encontrá-la ao atualizar
sua biblioteca. Janelas QML abertas pelo workspace atualizam a biblioteca após salvar. O
launcher independente não envia eventos a outro processo do aplicativo.

Antes de sobrescrever um JSON aberto, o novo adaptador verifica se outro processo
mudou seu conteúdo em disco. Se mudou, pede reabrir ou salvar uma cópia. O editor
antigo não recebeu essa proteção e conserva seu comportamento anterior.

## Verificações específicas das alterações

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s features/editor_qml/tests -v
```

Testes verificam migração idempotente do fundo, IDs/ordem entre tipos, paridade do
cache estático, composição das camadas durante edição, pintura nativa versus
renderer, estilos por seleção, variáveis entre spans HTML, atalhos e histórico.
Também cobrem metadados, cópia de assets, salvar/reabrir, igualdade da
imagem renderizada após Salvar como, conflitos, valores inválidos, histórico,
geometria, bloqueio/visibilidade, variáveis/links, guias, ordenação e abertura do
resultado no editor legado. Testes QML acionam mouse/teclado para seleção,
geometria, cor, duplo clique/edição de HTML e reordenação de campos.

## Validação final do fluxo

A validação automatizada foi executada: 46 testes do editor/workspace e dois de
links PDF aprovados, incluindo cópias dos três modelos reais do repositório,
exportação PNG/PDF individual e única, imposição retrato/paisagem e falhas de
produção. Foram corrigidos metadados físicos dos PNGs, medidas personalizadas e
orientação dos PDFs, resolução do fundo relativo e encerramento de geração com erro.

Veja [VALIDACAO_FLUXO_COMPLETO.md](VALIDACAO_FLUXO_COMPLETO.md) para a matriz,
evidências, comandos e diferenças preexistentes do legado. Permanecem a conferência
física de impressão, aceite com modelos/fontes de produção e medição em grandes
lotes. O padrão continua legado até esse aceite; a preferência salva é preservada.
