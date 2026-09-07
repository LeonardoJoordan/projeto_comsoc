# COMSOC Studio — exploração visual do editor QML

Este diretório contém uma proposta isolada de rebranding para o futuro frontend do editor do COMSOC. A composição busca acabamento profissional com baixa carga cognitiva: ações reais e camadas à esquerda, geometria contextual no topo, canvas dominante e propriedades da seleção à direita.

O protótipo não importa módulos do projeto, não abre modelos e não executa ações de edição. Seu objetivo é permitir a avaliação da organização, hierarquia, densidade e identidade visual antes de qualquer integração funcional. O nome visual “COMSOC Studio” é uma proposta de interface, não uma alteração definitiva da marca do produto.

## Princípios desta proposta

- O documento e a seleção são o centro da atenção.
- A barra superior mostra apenas propriedades relevantes ao contexto atual.
- Adicionar ao modelo apresenta Texto, Formas, Imagens e Assinatura em uma coluna, com botões de 43,5 px (75% da altura anterior).
- O fundo é uma imagem comum na base da lista única de camadas. O frontend não distingue um tipo Fundo nem separa camadas por tipo de objeto; a adaptação do modelo de dados e do renderer legado fica para a integração futura.
- As ações de criação e as camadas ficam num painel esquerdo aberto, recolhível e redimensionável.
- O inspector direito troca seu conteúdo conforme o tipo de objeto selecionado e não repete a geometria disponível no topo.
- A aba `Página 1` reserva uma direção visual para modelos multipágina sem expor controles ainda inexistentes.
- Guias, réguas, estado da seleção, zoom e atalhos são visíveis sem ocupar o canvas.
- A aparência é própria do COMSOC; nenhuma implementação de terceiros foi copiada ou adaptada.

## Executar

Na raiz do projeto:

```bash
.venv/bin/python features/editor_qml/main.py
```

No Windows, com a virtualenv ativa:

```powershell
python features/editor_qml/main.py
```

## Verificar o carregamento

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python features/editor_qml/main.py --check
```

## Gerar uma captura

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python features/editor_qml/main.py --screenshot /tmp/editor-qml.png
```

## Limites atuais

- Nenhum botão executa ações do COMSOC.
- Propriedades, Texto e Campos da tabela são cabeçalhos de seção, inicialmente recolhidos. Cada clique abre ou fecha o respectivo conteúdo; trocar de camada recolhe Propriedades e Texto. Campos da tabela pertence ao modelo e demonstra a reordenação das variáveis ao segurar e arrastar uma linha, confirmando a nova posição ao soltar. Comportamento fica em Propriedades.
- Selecionar uma camada da lista atualiza o nome, o tipo e o conteúdo demonstrativo no inspector. Texto permanece visível, recolhido e bloqueado para imagens e assinaturas; só é habilitado para texto. Os botões de criação não alteram a seleção. A opção Contorno fica disponível para textos e formas simples e indisponível para imagens.
- A barra superior agrupa os botões compactos de guia horizontal e vertical após a opacidade, junto à visibilidade e ao bloqueio. Adicionar guias ainda não altera o documento. O rodapé mantém apenas a grade, que mostra ou oculta as linhas do fundo.
- Fonte lista as famílias instaladas no sistema. Não há campo Peso nem opções fictícias de variantes. Os alinhamentos horizontal e vertical usam ícones do mesmo conjunto. Esses controles demonstram estados locais; não alteram o texto no canvas. O campo lateral de conteúdo foi retirado, conforme a direção de edição futura no canvas.
- Os valores apresentados são demonstrativos.
- O documento no canvas é uma composição visual fictícia.
- A interface ainda não está conectada ao renderer, persistência, camadas ou histórico.
- O protótipo não representa paridade funcional do futuro editor QML.
- Botões e campos demonstram intenção de interação; somente alguns estados visuais locais respondem nesta exploração.
