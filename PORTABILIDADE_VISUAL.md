# Portabilidade visual do FORNAX Forge

Este documento reúne as decisões e os materiais necessários para manter a identidade visual do programa no Linux, Windows e macOS. Ele não altera o comportamento atual da interface.

## 1. Tarefas e decisões do responsável pelo projeto

### 1.1 Fonte da interface

- [ ] Escolher uma família tipográfica livre para toda a interface.
- [ ] Definir os pesos que serão usados: Regular 400, Medium 500, Semibold 600 e Bold 700.
- [ ] Colocar os arquivos da fonte em `assets/fonts/ui/`.
- [ ] Colocar junto a licença original da fonte, com o nome `LICENSE.txt`.

Sugestão técnica: **Inter**, distribuída sob SIL Open Font License. Ela possui boa leitura em tamanhos pequenos, muitos pesos e ampla cobertura de caracteres. A escolha deve ser confirmada antes da integração.

Arquivos esperados caso a escolha seja Inter:

- `assets/fonts/ui/Inter-Regular.ttf`
- `assets/fonts/ui/Inter-Medium.ttf`
- `assets/fonts/ui/Inter-SemiBold.ttf`
- `assets/fonts/ui/Inter-Bold.ttf`
- `assets/fonts/ui/LICENSE.txt`

Essa fonte será exclusiva da interface. As fontes usadas na arte dos modelos precisam de uma política separada para que documentos tenham o mesmo resultado em todos os sistemas.

### 1.2 Fontes dos modelos

- [ ] Decidir se o programa fornecerá um pequeno conjunto de fontes livres para os modelos.
- [ ] Decidir se um modelo importado poderá incorporar suas próprias fontes.
- [ ] Definir o comportamento quando uma fonte estiver ausente: impedir a geração, pedir substituição ou permitir substituição automática com aviso.
- [ ] Confirmar se a fonte padrão de novas caixas de texto continuará sendo Arial ou será uma fonte livre distribuída com o programa.

Recomendação: usar uma fonte livre fornecida pelo programa como padrão e nunca substituir silenciosamente uma fonte ausente na geração final.

### 1.3 Ícones SVG

- [ ] Obter os SVGs indicados em `assets/icons/ui/README.md`.
- [ ] Preservar a licença e a atribuição exigidas pelo conjunto escolhido.
- [ ] Usar preferencialmente um único conjunto de ícones para manter espessura e desenho coerentes.
- [ ] Confirmar se os SVGs podem ser redistribuídos em software livre e em versões instaláveis do programa.

### 1.4 Comportamento específico do macOS

- [ ] Decidir se o menu superior ficará na barra global do macOS ou dentro da janela como no Linux e Windows.

Recomendação: usar o menu nativo do macOS. A posição será diferente, mas o comportamento será familiar para usuários desse sistema. Se a prioridade absoluta for uma captura visual igual, será necessário manter o menu dentro da janela.

### 1.5 Diálogos do sistema

- [ ] Decidir se seleção de arquivos e pastas continuará usando diálogos nativos.
- [ ] Decidir se a seleção de cores deve ser nativa ou receber um seletor próprio do FORNAX Forge.
- [ ] Decidir se mensagens de confirmação devem manter `QMessageBox` ou usar modais próprios.

Recomendação: manter arquivos e pastas nativos; criar componentes próprios somente para cores e diálogos que façam parte do fluxo visual frequente.

### 1.6 Telas e escalas que serão suportadas

- [ ] Definir a menor resolução oficial. Sugestão: 1366 × 768.
- [ ] Confirmar suporte às escalas de 100%, 125%, 150% e 200%.
- [ ] Informar se monitores ultrawide devem possuir alguma adaptação específica além dos painéis flexíveis atuais.
- [ ] Definir se o editor deve funcionar em telas menores que 1366 × 768 com rolagem ou se poderá exigir resolução mínima.

### 1.7 Máquinas para validação

- [ ] Disponibilizar teste em Windows com escalas de 100%, 125% e 150%.
- [ ] Disponibilizar teste em macOS, preferencialmente Retina.
- [ ] Manter a referência Linux atual.
- [ ] Registrar capturas da tela inicial, tabela, editor, propriedades, temas e diálogos em cada sistema.

## 2. Trabalho posterior no código

- [ ] Fixar uma versão exata do PySide6 em todos os pacotes e ambientes.
- [ ] Registrar a fonte da interface com `QFontDatabase` antes de criar as janelas.
- [ ] Aplicar a mesma família e os mesmos pesos globalmente.
- [ ] Substituir símbolos Unicode funcionais pelos SVGs aprovados.
- [ ] Remover emojis dos identificadores internos da tabela. Quantidade e assinatura não devem ser reconhecidas pelo texto visível do cabeçalho.
- [ ] Auditar controles com largura ou altura fixa usando a nova fonte.
- [ ] Auditar o comportamento de DPI e arredondamento em todas as escalas suportadas.
- [ ] Definir o comportamento do menu no macOS.
- [ ] Padronizar apenas os diálogos escolhidos na seção 1.5.
- [ ] Fixar a versão do Qt/PySide6 nos scripts Nuitka e Flatpak.
- [ ] Criar testes de captura visual por plataforma e escala.

## 3. Critério de conclusão

A portabilidade visual estará aprovada quando nenhuma tela apresentar texto cortado, sobreposição, botão deslocado, ícone dependente de emoji ou alteração estrutural inesperada nas combinações de sistema e escala definidas acima. Diferenças na moldura externa da janela e nos diálogos nativos aprovados serão consideradas comportamento normal do sistema.
