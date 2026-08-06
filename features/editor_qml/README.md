# COMSOC Studio — exploração visual do editor QML

Este diretório contém uma proposta isolada de rebranding para o futuro frontend do editor do COMSOC. A composição busca acabamento profissional com baixa carga cognitiva: ações reais e camadas à esquerda, geometria contextual no topo, canvas dominante e propriedades da seleção à direita.

O protótipo não importa módulos do projeto, não abre modelos e não executa ações de edição. Seu objetivo é permitir a avaliação da organização, hierarquia, densidade e identidade visual antes de qualquer integração funcional. O nome visual “COMSOC Studio” é uma proposta de interface, não uma alteração definitiva da marca do produto.

## Princípios desta proposta

- O documento e a seleção são o centro da atenção.
- A barra superior mostra apenas propriedades relevantes ao contexto atual.
- A interface mostra somente objetos que o COMSOC realmente cria: texto, imagem, assinatura, fundo e guias.
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
- Os valores apresentados são demonstrativos.
- O documento no canvas é uma composição visual fictícia.
- A interface ainda não está conectada ao renderer, persistência, camadas ou histórico.
- O protótipo não representa paridade funcional do futuro editor QML.
- Botões e campos demonstram intenção de interação; somente alguns estados visuais locais respondem nesta exploração.
