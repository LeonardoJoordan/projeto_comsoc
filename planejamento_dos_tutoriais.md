# Planejamento dos tutoriais interativos

## Finalidade deste documento

Este arquivo define o padrão comum dos tutoriais e o roteiro aprovado para o tutorial **Primeiros passos**. A implementação deve seguir este documento somente depois de sua revisão final.

## Padrão geral dos tutoriais

### Aprendizado pela interface real

O tutorial deve ensinar usando os controles reais do programa. Quando mencionar um botão, campo, menu ou item, deve destacá-lo e aguardar a ação do usuário.

Cada ação prática será apresentada em duas partes:

1. **Orientação:** destacar o controle e explicar o que deve ser feito.
2. **Resultado:** destacar a região alterada e explicar o efeito da ação.

O botão **Continuar** será usado somente quando a etapa for explicativa. Ele nunca substituirá um clique, preenchimento, redimensionamento, colagem ou escolha que faça parte do exercício.

O tutorial só avançará quando detectar a ação e confirmar seu resultado. Interações em outros controles não concluirão a etapa.

### Destaque e posição do cartão

- Manter toda a interface visível, sem escurecer nem bloquear os demais controles.
- Manter o alvo totalmente visível.
- Aplicar um contorno pulsante discreto somente no alvo da ação.
- Posicionar o cartão próximo ao alvo, com uma folga confortável e usando o lado com maior espaço livre.
- Não cobrir o alvo nem o resultado explicado.
- Recalcular a posição quando a janela, o painel ou o alvo mudar de tamanho ou posição.
- Quando uma ação abrir um menu, transferir o destaque para a opção dentro dele.
- Quando um diálogo bloquear a janela, transferir o tutorial para o diálogo e restaurá-lo na janela adequada depois do fechamento.
- Quando o resultado estiver no canvas, na tabela ou no log, destacar exatamente a área modificada.

### Cartão do tutorial

O cartão deve apresentar:

- progresso, como `ETAPA 8 DE 37`;
- título curto;
- orientação objetiva;
- somente as ações de navegação adequadas à etapa.

Nas etapas práticas, o texto deve apresentar primeiro a ação em destaque e depois a explicação. Nas etapas informativas, deve destacar a informação principal. Explicações longas devem ser divididas em mais de uma etapa.

### Botões

Os botões devem seguir o padrão dos diálogos do FORNAX Forge:

- **Voltar** e **Pular tutorial** com a mesma dimensão secundária e altura de 24 px;
- **Continuar** centralizado, com altura de 30 px e maior destaque;
- ícone de retorno à esquerda em **Voltar** e avanço à direita em **Pular tutorial**;
- texto centralizado;
- **Começar**, **Continuar** e **Concluir** como ações afirmativas, usando a cor de destaque do tema;
- **Pular tutorial** como ação de cancelar: fundo neutro e vermelho somente no hover ou ao pressionar;
- **Voltar** como ação secundária neutra.

Em etapas que aguardam uma ação na interface, não haverá botão afirmativo no cartão. O próprio controle destacado será a ação afirmativa.

### Navegação e segurança

- **Voltar** retorna à explicação anterior sem desfazer o trabalho do usuário.
- Uma ação já concluída será reapresentada como explicação do estado atual, sem exigir sua repetição.
- **Pular tutorial** encerra apenas a orientação; não fecha janelas nem apaga o trabalho.
- Fechar o editor ou a janela principal encerra o tutorial com segurança.
- O tutorial não salva, exclui, renomeia ou gera arquivos sem uma ação explícita do usuário.
- As validações e mensagens reais do programa permanecem ativas.
- Quando faltar uma condição, o cartão explica o problema e mantém o destaque no controle que precisa de correção.

### Uso da área de transferência

O tutorial poderá preparar textos para exercícios de `Ctrl+V`. Para não apagar dados pessoais do usuário:

1. guardar o conteúdo textual anterior da área de transferência ao iniciar o tutorial;
2. informar sempre que um conteúdo de exercício foi copiado;
3. substituir o conteúdo somente no momento em que ele será usado;
4. restaurar o conteúdo original ao concluir, pular ou interromper o tutorial.

### Estado ao final

O tutorial cria um modelo e uma geração reais. Ao final permanecem:

- o modelo salvo na biblioteca;
- dez linhas de dados na tabela;
- o material produzido;
- a pasta exclusiva criada para o trabalho.

O programa não cria silenciosamente um modelo de treinamento e não apaga o resultado ao concluir.

---

## Roteiro: Primeiros passos

### Objetivo

Ensinar o fluxo básico completo:

1. criar um modelo;
2. adicionar e redimensionar texto;
3. conhecer propriedades de alinhamento;
4. usar placeholders e trechos opcionais;
5. salvar o modelo;
6. alimentar a tabela por colagem;
7. conferir o preview;
8. escolher a pasta de destino;
9. acompanhar a geração pelo log;
10. compreender a organização dos trabalhos em Forjas.

O tutorial termina somente depois da geração bem-sucedida dos dez itens.

### Conteúdo usado no exercício

#### Texto do modelo

```text
Este cartão foi feito de forma muito rápida e eficiente para {nome}| com a ajuda de {programa}|!
```

#### Primeira colagem: coluna `nome`

```text
Ana Silva
Bruno Costa
Carla Souza
Daniel Lima
Elisa Rocha
Felipe Alves
Gabriela Nunes
Henrique Melo
Isabela Martins
João Ribeiro
```

#### Segunda colagem: coluna `programa`

```text
FORNAX Forge
FORNAX Forge
FORNAX Forge
FORNAX Forge
FORNAX Forge
FORNAX Forge
FORNAX Forge
FORNAX Forge
FORNAX Forge
FORNAX Forge
```

#### Terceira colagem: duas colunas simultâneas

```text
Ana Silva	FORNAX Forge
Bruno Costa	FORNAX Forge
Carla Souza	FORNAX Forge
Daniel Lima	FORNAX Forge
Elisa Rocha	FORNAX Forge
Felipe Alves	FORNAX Forge
Gabriela Nunes	FORNAX Forge
Henrique Melo	FORNAX Forge
Isabela Martins	FORNAX Forge
João Ribeiro	FORNAX Forge
```

Os nomes são dados fictícios usados somente na demonstração.

---

### Etapa 1 — Apresentação

**Alvo:** nenhum; cartão centralizado.

**Texto:**

> Você criará um modelo, preencherá dez itens e gerará o primeiro trabalho. O tutorial acompanhará suas ações diretamente nos controles do programa.

**Ações:** `Pular tutorial` e `Começar`.

### Etapa 2 — Abrir o menu Modelo

**Alvo para ação:** menu `Modelo` da barra superior.

**Texto:**

> Os modelos definem o visual e os campos personalizados. Clique em **Modelo** para acessar as ações da biblioteca.

**Avanço:** menu realmente aberto.

### Etapa 3 — Criar o modelo

**Alvo para ação:** opção `Novo modelo`.

**Texto:**

> Clique em **Novo modelo** para abrir um documento vazio no editor.

**Avanço:** editor criado e exibido.

### Etapa 4 — Área do documento

**Alvo de resultado:** página branca no canvas.

**Texto:**

> Esta é a área do documento. O que estiver dentro dela fará parte do material gerado. A área externa continua disponível para organizar objetos durante a edição.

**Ações:** `Voltar`, `Pular tutorial` e `Continuar`.

### Etapa 5 — Adicionar texto

**Alvo para ação:** botão `Texto`.

**Texto:**

> Clique em **Texto** para adicionar o conteúdo personalizado.

**Avanço:** clique real e criação da caixa.

### Etapa 6 — Resultado da adição

**Alvo de resultado:** caixa recém-criada no canvas.

**Texto:**

> A caixa foi criada e já está selecionada. Os marcadores ao redor dela permitem mudar seu tamanho.

**Ação:** `Continuar`.

### Etapa 7 — Redimensionar a caixa

**Alvo para ação:** marcador de redimensionamento da caixa selecionada.

**Texto:**

> Arraste um dos marcadores para deixar a caixa mais larga. O texto se adapta ao novo espaço.

**Avanço:** detectar uma alteração real na largura ou altura da caixa.

### Etapa 8 — Resultado do redimensionamento

**Alvo de resultado:** limite atualizado da caixa.

**Texto:**

> A caixa agora possui mais espaço. Você pode redimensionar textos e outros objetos dessa mesma forma.

**Ação:** `Continuar`.

### Etapa 9 — Propriedades do texto

**Alvo de resultado:** painel `TEXTO` da barra lateral direita.

**Texto:**

> Este painel reúne fonte, tamanho, cor, estilo, alinhamento, entrelinha e recuo. Vamos experimentar os dois alinhamentos da caixa.

**Ação:** `Continuar`.

### Etapa 10 — Centralizar horizontalmente

**Alvo para ação:** botão de alinhamento horizontal centralizado.

**Texto:**

> Clique em **Centralizar** para alinhar cada linha horizontalmente no centro da caixa.

**Avanço:** alinhamento horizontal central aplicado.

### Etapa 11 — Resultado horizontal

**Alvo de resultado:** texto centralizado no canvas.

**Texto:**

> O conteúdo agora está centralizado entre as laterais da caixa.

**Ação:** `Continuar`.

### Etapa 12 — Centralizar verticalmente

**Alvo para ação:** botão de alinhamento vertical central.

**Texto:**

> Clique em **Meio** para posicionar o texto no centro vertical da caixa.

**Avanço:** alinhamento vertical central aplicado.

### Etapa 13 — Resultado vertical

**Alvo de resultado:** caixa no canvas.

**Texto:**

> O texto está centralizado nos dois sentidos. Os alinhamentos horizontal e vertical são independentes.

**Ação:** `Continuar`.

### Etapa 14 — Preparar o conteúdo personalizado

**Alvo de resultado:** caixa de texto.

**Preparação automática:** guardar o clipboard atual e copiar o texto definido neste roteiro.

**Texto:**

> O texto do exercício foi copiado para sua área de transferência. Dê dois cliques na caixa, selecione todo o conteúdo com **Ctrl+A** e cole com **Ctrl+V**.

**Avanço:** conteúdo editado e confirmado. O tutorial deve exigir os placeholders `{nome}` e `{programa}` e o trecho opcional `| com a ajuda de {programa}|`. Não avançar com sintaxe incompleta.

### Etapa 15 — Placeholders e trecho opcional

**Alvos de resultado:** texto no canvas e itens `nome` e `programa` em `Campos da tabela`.

**Texto, em dois cartões curtos:**

> `{nome}` e `{programa}` são placeholders. Cada linha da tabela poderá fornecer conteúdos diferentes para eles.

> O trecho entre barras verticais é opcional. `| com a ajuda de {programa}|` aparece somente quando `programa` possui conteúdo. Se um placeholder obrigatório ficar vazio, a caixa inteira não será exibida naquele item.

O primeiro cartão destaca o texto. O segundo destaca o trecho opcional e depois a lista com os dois campos.

### Etapa 16 — Salvar o modelo

**Alvo para ação:** botão `Salvar modelo`.

**Texto:**

> Clique em **Salvar modelo** para adicioná-lo à biblioteca.

**Avanço:** abertura da solicitação de nome.

### Etapa 17 — Nomear o modelo

**Alvo para ação:** campo de nome do diálogo.

**Texto:**

> Digite um nome para reconhecer este modelo. Neste exercício, você pode usar **Meu primeiro modelo**.

**Avanço:** nome válido preenchido. Em seguida, destacar o botão afirmativo e aguardar seu clique.

### Etapa 18 — Sair do editor

**Alvo para ação:** ação afirmativa da mensagem posterior ao salvamento.

**Texto:**

> O modelo foi salvo. Volte à tela principal para alimentar os campos personalizados.

**Avanço:** editor fechado e workspace ativo.

### Etapa 19 — Modelo e colunas criadas

**Alvos de resultado:** modelo selecionado e cabeçalhos `nome` e `programa`.

**Texto, em dois cartões:**

> O modelo salvo está selecionado na biblioteca.

> Os dois placeholders criaram as colunas **nome** e **programa**. Uma caixa só aparece quando seus placeholders obrigatórios estão preenchidos. O trecho opcional pode desaparecer sem ocultar o restante da caixa.

Destacar primeiro a seleção do modelo e depois as duas colunas.

### Etapa 20 — Colar dez nomes

**Preparação automática:** copiar a lista de dez nomes para o clipboard.

**Alvo para ação:** primeira célula da coluna `nome`.

**Texto:**

> Dez nomes foram copiados. Clique na primeira célula da coluna **nome** e pressione **Ctrl+V**.

**Avanço:** dez linhas preenchidas corretamente na coluna `nome`.

### Etapa 21 — Resultado da primeira colagem

**Alvo de resultado:** intervalo preenchido da coluna `nome`.

**Texto:**

> Uma única colagem preencheu dez linhas. O FORNAX preserva a estrutura copiada de uma planilha.

**Ação:** `Continuar`.

### Etapa 22 — Colar o nome do programa

**Preparação automática:** copiar dez linhas com `FORNAX Forge`.

**Alvo para ação:** primeira célula da coluna `programa`.

**Texto:**

> Agora foram copiadas dez ocorrências de **FORNAX Forge**. Clique na primeira célula da coluna **programa** e pressione **Ctrl+V**.

**Avanço:** as dez células da coluna `programa` preenchidas.

### Etapa 23 — Resultado das duas colunas

**Alvos de resultado:** tabela preenchida e preview.

**Texto:**

> As dez linhas agora possuem os dois placeholders. Selecione linhas diferentes para conferir como o preview acompanha o item escolhido.

O cartão aponta primeiro a tabela e, após uma troca real de linha, aponta o preview atualizado.

### Etapa 24 — Excluir os dados do exercício

**Alvo para ação:** seleção das dez linhas e botão `Excluir` do bloco `LINHAS`.

**Texto:**

> Vamos repetir o preenchimento de uma forma ainda mais rápida. Selecione as dez linhas e clique em **Excluir**.

**Avanço:** dados do exercício removidos e tabela novamente disponível para a colagem seguinte.

### Etapa 25 — Colar duas colunas de uma vez

**Preparação automática:** copiar a tabela de dez linhas e duas colunas definida neste roteiro.

**Alvo para ação:** primeira célula da coluna `nome`.

**Texto:**

> Os nomes e o programa foram copiados juntos. Clique na primeira célula de **nome** e pressione **Ctrl+V** para preencher as duas colunas e as dez linhas de uma só vez.

**Avanço:** confirmar os vinte valores esperados na tabela.

### Etapa 26 — Fluxo com planilhas externas

**Alvos de resultado:** intervalo preenchido e preview.

**Texto:**

> Você pode copiar várias linhas e colunas de uma só vez. A proposta do FORNAX é aproveitar a planilha que sua equipe já usa no Excel, Google Sheets, LibreOffice ou outro sistema, evitando redigitação.

> O preview permite conferir os dados antes da geração. Navegue entre dois itens para observar a atualização.

**Avanço:** usuário seleciona ao menos duas linhas diferentes; depois, `Continuar`.

### Etapa 27 — Escolher a pasta de destino

**Alvo para ação:** botão de três pontos ao lado de `Salvar em`.

**Texto:**

> Clique neste botão e escolha a pasta onde os trabalhos produzidos serão armazenados.

**Avanço:** pasta válida selecionada.

### Etapa 28 — Pasta principal

**Alvo de resultado:** campo `Salvar em` preenchido.

**Texto:**

> Esta é a pasta principal de destino. Cada geração será guardada dentro dela em uma pasta exclusiva.

**Ação:** `Continuar`.

### Etapa 29 — Abrir o menu Exibir

**Alvo para ação:** menu `Exibir` da barra superior.

**Texto:**

> Antes de gerar, vamos abrir o log para acompanhar o processamento. Clique em **Exibir**.

**Avanço:** menu aberto.

### Etapa 30 — Mostrar o log

**Alvo para ação:** opção `Log de processamento`.

**Texto:**

> Ative o **Log de processamento**.

**Avanço:** log visível.

### Etapa 31 — Conhecer o log

**Alvo de resultado:** painel do log.

**Texto:**

> O log mostra o andamento, avisos e o resultado da geração. Ele ajuda a acompanhar trabalhos maiores e a identificar dados que precisam de atenção.

**Ação:** `Continuar`.

### Etapa 32 — Gerar o material

**Alvo para ação:** botão `Gerar material`.

**Texto:**

> Clique em **Gerar material**. O programa usará as dez linhas para produzir dez cartões personalizados.

**Avanço:** clique real. A etapa permanece ativa até o processamento terminar.

### Etapa 33 — Acompanhar a velocidade

**Alvo de resultado:** linhas acrescentadas ao log durante e após a geração.

**Texto:**

> Acompanhe o processamento no log. Um trabalho que exigiria editar os dez cartões individualmente é concluído automaticamente em poucos segundos.

Não prometer um tempo fixo: destacar o tempo real informado pelo programa, pois ele depende do computador, do modelo e do formato escolhido.

**Avanço:** sinal real de conclusão e confirmação da pasta criada.

### Etapa 34 — Resultado da geração

**Alvo de resultado:** mensagem ou registro que informa o sucesso e o diretório produzido.

**Texto:**

> Os dez itens foram gerados. O log é opcional: você pode mantê-lo visível quando quiser acompanhar detalhes ou ocultá-lo para ampliar a área de trabalho.

Se houver uma ação real para abrir a pasta produzida, destacá-la como opção, sem torná-la obrigatória.

### Etapa 35 — Organização em Forjas

**Alvo de resultado:** caminho ou nome da pasta criada, como `FORNAX - Forja nº 1`.

**Texto:**

> Cada geração cria uma nova **Forja**, com numeração contínua. Assim, arquivos de trabalhos diferentes não se misturam e a pasta principal continua organizada mesmo depois de muitas produções.

**Ações:** `Voltar` e `Concluir`.

Ao concluir, manter a tela principal, o modelo, as dez linhas e os arquivos exatamente como estão, e restaurar a área de transferência anterior ao tutorial.

---

## Regras técnicas específicas

- Não abrir o editor automaticamente: aguardar `Modelo > Novo modelo`.
- Não usar `Continuar` quando o roteiro exigir uma ação no programa.
- Guardar a referência da caixa criada para destacar seu canvas, seus marcadores e seu resultado.
- Considerar o redimensionamento concluído somente após uma mudança real de geometria.
- Validar o alinhamento horizontal e vertical no estado do objeto, não apenas pelo clique nos botões.
- Validar o conteúdo rico da caixa e exigir exatamente os placeholders `nome` e `programa`.
- Validar a sintaxe do trecho opcional que contém `programa`.
- Aguardar a lista `Campos da tabela` mostrar os dois placeholders antes de salvar.
- Acompanhar os diálogos sem deixar o cartão atrás deles.
- Depois do salvamento, aguardar a atualização do modelo, da tabela e do preview.
- Preparar o clipboard somente quando a respectiva colagem começar.
- Validar o conteúdo colado por valores, linhas e colunas, independentemente da ordem visual das colunas adicionais do sistema.
- Na exclusão, confirmar que os dados das dez linhas foram removidos antes da colagem conjunta.
- Na colagem conjunta, começar pela coluna `nome` e mapear corretamente a segunda coluna para `programa`.
- Aguardar a atualização real do preview após cada seleção usada no exercício.
- Não aceitar uma pasta inexistente ou vazia como destino concluído.
- Detectar a visibilidade real do log antes de liberar a geração.
- Aguardar o término do gerador e verificar a criação da pasta da Forja.
- Usar o nome localizado da pasta: `Forja`, `Forge` ou o equivalente do idioma ativo.
- Em caso de erro, manter o tutorial ativo, mostrar a mensagem normal e retornar ao controle que precisa de correção.
- Restaurar o clipboard original em toda saída possível do tutorial.

## Decisões aplicadas na implementação

- Manter **Meu primeiro modelo** como sugestão, sem obrigar o usuário a adotar esse nome.
- Explicar `PNG`, `PDF por item` e `PDF agrupado` em três partes antes da geração, permitindo que o usuário escolha qualquer formato.
- Ensinar a seleção das dez linhas por `Ctrl+A` a partir de uma célula antes de acionar `Excluir`.
- Destacar a explicação de placeholders e trechos opcionais em um cartão central de atenção, com borda amarela.
- Exibir o tempo real da geração e informar o nome e o caminho exatos da pasta criada.
