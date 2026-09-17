# Portabilidade visual do FORNAX Forge

Este documento reúne as decisões e os materiais necessários para manter a identidade visual do programa no Linux, Windows e macOS. Ele não altera o comportamento atual da interface.

## 1. Decisões implementadas

### 1.1 Fonte da interface

- [x] Inter é a família oficial da interface e de novas caixas de texto.
- [x] As variantes estáticas 18 pt são registradas antes da criação das janelas.
- [x] Regular, Medium, SemiBold, Bold e ExtraBold estão disponíveis como desenhos reais.
- [x] A licença original está preservada em `assets/fonts/ui/OFL.txt`.

Inter é distribuída sob a SIL Open Font License. Arquivos de outros tamanhos ópticos e variantes variáveis não usados foram retirados do pacote.

As demais fontes escolhidas pelo usuário continuam pertencendo ao documento. O painel de informações do modelo lista as famílias usadas e destaca as ausentes sem interromper o trabalho.

### 1.2 Fontes dos modelos

- [ ] Decidir se o programa fornecerá um pequeno conjunto de fontes livres para os modelos.
- [ ] Decidir se um modelo importado poderá incorporar suas próprias fontes.
- [ ] Definir o comportamento quando uma fonte estiver ausente: impedir a geração, pedir substituição ou permitir substituição automática com aviso.
- [x] Novas caixas de texto usam a Inter incorporada.

Recomendação: usar uma fonte livre fornecida pelo programa como padrão e nunca substituir silenciosamente uma fonte ausente na geração final.

### 1.3 Ícones SVG

- [x] Os SVGs funcionais ativos estão centralizados em `assets/icons/ui/` e possuem teste de carregamento.
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

## 2. Trabalho concluído no código

- [x] PySide6 possui versão exata nos requisitos e no manifesto Flatpak.
- [x] A fonte da interface é registrada com `QFontDatabase` antes das janelas.
- [x] A mesma família é aplicada globalmente, com variantes estáticas para os pesos usados.
- [x] Ícones funcionais foram centralizados em SVG; símbolos restantes são mensagens de log ou avisos textuais.
- [x] A coluna de quantidade usa um identificador centralizado e traduzível.
- [ ] Auditar controles com largura ou altura fixa usando a nova fonte.
- [ ] Auditar o comportamento de DPI e arredondamento em todas as escalas suportadas.
- [ ] Definir o comportamento do menu no macOS.
- [ ] Padronizar apenas os diálogos escolhidos na seção 1.5.
- [x] A versão do Qt/PySide6 é fixada pelo ambiente de requisitos usado pelo Nuitka e pelo manifesto Flatpak.
- [ ] Criar testes de captura visual por plataforma e escala.

## 3. Validações ainda externas

- conferir Windows em 100%, 125% e 150%;
- conferir macOS em tela Retina e o comportamento do menu global;
- revisar visualmente diálogos nativos de arquivos, pastas, impressão e cores;
- registrar capturas da tela inicial, tabela, editor, propriedades e temas;
- executar uma prova física duplex com o pacote candidato;
- confirmar a licença e atribuição do conjunto de ícones antes da publicação.

## 4. Critério de conclusão multiplataforma

A portabilidade visual estará aprovada quando nenhuma tela apresentar texto cortado, sobreposição, botão deslocado, ícone dependente de emoji ou alteração estrutural inesperada nas combinações de sistema e escala definidas acima. Diferenças na moldura externa da janela e nos diálogos nativos aprovados serão consideradas comportamento normal do sistema.
