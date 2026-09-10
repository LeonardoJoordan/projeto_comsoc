# Editor Widgets modernizado

Interface inspirada no editor QML, usando exclusivamente Qt Widgets e o canvas
do legado. Os outros dois editores não são alterados por esta versão.

Na raiz do projeto:

```bash
.venv/bin/python features/editor_novo/main.py
.venv/bin/python features/editor_novo/main.py --model /caminho/template_v3.json
```

O segundo comando abre o modelo real: use uma cópia da pasta do modelo para
experimentos que envolvam salvar, substituir imagens ou excluir recursos.

Verificação sem interface gráfica e captura:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python features/editor_novo/main.py --check
QT_QPA_PLATFORM=offscreen .venv/bin/python features/editor_novo/main.py --screenshot /tmp/editor-novo.png
```

## Primeira versão visual

- Barra superior com posição, dimensões, proporção, rotação, opacidade e guias.
- Ferramentas de criação, camadas e laterais redimensionáveis.
- Seções recolhíveis de documento, propriedades, texto e campos da tabela no painel direito.
- Tema grafite, destaque violeta, controles uniformes e ícones vetoriais.
- Fontes do sistema, alinhamentos em comboboxes e cor com seletor/hexadecimal.

O menu Formas oferece Quadrado, Círculo e Linha. Sombras ainda não foram implementadas.
As camadas têm ordem única, sem categorias. Fundos de modelos antigos são
convertidos em imagens comuns ao abrir, preservando a composição inicial.
O salvamento utiliza `layer_order`, já suportado pelo renderer compartilhado.
Documentos novos recebem um retângulo branco “Plano de fundo” do tamanho da
página, sempre abaixo das demais camadas. Existe exatamente uma base, selecionável
somente pela lista. Posição, dimensões e rotação são vinculadas ao documento;
exclusão, duplicação e reordenação são bloqueadas. Preenchimento, opacidade e
visibilidade continuam editáveis. O fundo é salvo em `shapes`, sem gerar uma
imagem, e acompanha o redimensionamento e o histórico do documento.
A base faz parte do estado inicial, sem alterações pendentes ao criar o modelo.
O quadriculado representa transparência no canvas; a saída de impressão continua
representando o papel. O novo editor não oferece exportação direta em PNG.

As propriedades das formas oferecem preenchimento, contorno opcional, cor e
opacidade independentes (campos α em porcentagem), além de cantos retos ou
arredondados para contornos retangulares. A opacidade geral do objeto multiplica
as opacidades de preenchimento e contorno. Também oferecem
espessura em milímetros, com alinhamento interno, externo ou centralizado. A
interface converte para pixels internamente, preservando o formato dos modelos. O estilo
é preservado no histórico, duplicação e salvamento, e compartilhado com o desenho
da exportação. No plano de fundo, o contorno é sempre interno; as opções externa
e centralizada ficam desabilitadas em Propriedades. Fundos salvos anteriormente
com outro alinhamento passam a usar o contorno interno ao abrir.
O seletor de cores é o diálogo Qt existente. Não há integração nova no workspace.

`frontend.py` reorganiza os controles existentes preservando seus sinais. Os
contêineres originais ficam ocultos para manter referências usadas pelo legado;
a separação definitiva entre construção da interface e lógica pode ser feita
após aprovação visual. Nenhum processamento periódico foi adicionado ao canvas.

Validação inicial: abertura offscreen, captura visual, criação de texto, seleção,
alteração de largura, bloqueio dos campos sem seleção e execução de desfazer/refazer.
A fluidez no computador do operador ainda precisa ser avaliada presencialmente.

## Aproximação visual ao QML

Barra compacta com identificadores X/Y/L/A dentro dos campos, cabeçalho com
nome do modelo, ferramentas com subtítulos e ações de camada em ícones.
Laterais inicialmente com 262 e 322 pixels, seguindo a referência QML.
As medidas continuam em mm para preservar o contrato dos controles do legado.

## Edição no canvas

## Criação de formas

Escolha Quadrado, Círculo ou Linha em Formas e arraste no canvas. O desenho livre
permite retângulos, elipses e linhas em qualquer direção. Segurar Shift restringe
quadrado/círculo à proporção 1:1 e linhas a múltiplos de 45°. Esc cancela; soltar
confirma uma única operação no histórico. Um clique sem arraste não cria objeto.
Novas formas começam em cinza-claro (#d9d9d9); o plano de fundo continua branco.
Durante o redimensionamento pelas alças, Shift preserva a proporção inicial da
forma sem alterar o botão de manter proporção. Ao ajustar linhas, Shift restringe
a direção a múltiplos de 45°.

Linhas têm comprimento e espessura em mm, cor do traço e ângulo em graus em
Propriedades. A diagonal que sobe para a direita exibe 45° (rotação matemática
positiva; a transformação Qt usa o sinal oposto). Formas e linhas participam da
ordem global, duplicação, persistência e renderização. O plano de fundo conserva
as restrições próprias de geometria e contorno interno.

As réguas permitem criar guias ao arrastar para o canvas. Para remover uma guia,
arraste a horizontal para a régua superior ou a vertical para a régua esquerda.
A remoção participa de desfazer/refazer; guias bloqueadas não podem ser arrastadas.

Duplo clique no texto ou Enter com um texto selecionado inicia a edição nativa.
Esc ou seleção de outro objeto encerra a sessão. Espaço, setas e Delete atuam
no texto durante a edição. Ctrl+B/I/U formata; Ctrl+Z desfaz a digitação local.
Ao encerrar, o conteúdo entra no histórico do modelo. Salvar e fechar também
encerram a sessão. A colagem por Ctrl+V usa texto simples para evitar estilos
externos incompatíveis. O campo de conteúdo lateral foi retirado da interface.

Teste: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest features.editor_novo.test_canvas_edit -v`.
