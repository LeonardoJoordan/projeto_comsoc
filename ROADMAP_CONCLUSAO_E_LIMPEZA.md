# FORNAX Forge — Roadmap de conclusão e limpeza

Este documento orienta a sequência de trabalho até a conclusão das funcionalidades previstas e a eliminação da dívida técnica identificada. Não é um plano detalhado de implementação: o projeto deverá ser reavaliado ao iniciar cada etapa.

## Como seguir este roadmap

- Antes de cada etapa, conferir o código e os comportamentos atuais, alinhar as decisões pendentes e definir seu escopo concreto.
- Fazer somente as preparações estruturais necessárias à etapa em execução. A limpeza ampla acontece depois de estabilizar as funcionalidades.
- Preservar o layout aprovado, a responsividade e a equivalência entre editor, prévia e arquivos gerados.
- Não confundir compatibilidade necessária com código descartável. Remoções exigem conferir consumidores, modelos antigos e distribuição.
- Marcar uma etapa como concluída somente após verificar seu resultado. Registrar abaixo o que terminou e qualquer pendência para a próxima sessão.

## Sequência prevista

### 1. Imagens dinâmicas por registro

**Status:** concluída e verificada em 16/09/2026.

**Direção:** permitir que uma forma receba uma fotografia indicada na tabela, localizada em uma pasta externa. Revisar as decisões de interface e tratamento de erros antes da implementação.

**Cuidados principais:** manter a pasta como preferência local por modelo; preservar a posição do cabeçalho e das primeiras linhas da tabela; definir nomes ambíguos, arquivos ausentes e enquadramento; compartilhar a resolução e o desenho da imagem entre prévia e geração; não aumentar desnecessariamente o custo de colar grandes lotes.

**Resultado esperado:** personalizar imagens por linha, com pasta lembrada no rodapé do painel de dados e resultados consistentes na prévia, PNG e PDF, inclusive em modelos de duas páginas.

### 2. Redimensionamento proporcional de grupos

**Status:** concluída e verificada em 16/09/2026.

**Direção:** revisar o agrupamento e as transformações já existentes antes de definir o comportamento que falta.

**Cuidados principais:** proporções, rotação, textos, imagens e máscaras; evitar deslocamentos ou escalas aplicados duas vezes; preservar vínculos, bloqueios e ordem de camadas; desfazer e refazer a operação como uma única alteração.

**Resultado esperado:** redimensionar o conjunto de forma previsível, preservando as relações entre seus elementos, com salvamento e histórico corretos.

### 3. Estabilização e fechamento do escopo funcional

**Status:** concluída e verificada em 16/09/2026.

**Direção:** revisar os fluxos completos após as duas funcionalidades e resolver regressões antes da limpeza ampla. Confirmar se ainda existe alguma função indispensável à versão pretendida.

**Cuidados principais:** modelos antigos e novos, cópia entre páginas, máscaras, grupos, fontes, dados em lote, frente e verso e imposição; medir responsividade e geração com cargas representativas.

**Resultado esperado:** uma versão funcional de referência, com verificações reproduzíveis e um marco no Git para comparar o comportamento durante a refatoração.

### 4. Construção direta da interface atual

**Status:** concluída e verificada em 17/09/2026.

**Direção:** eliminar a montagem de interfaces antigas que depois são ocultadas ou desmontadas. Começar pelo workspace e avançar por editor e tabela em mudanças separadas.

**Cuidados principais:** controles ocultos ainda podem sustentar sinais, atalhos e ações; substituir essas dependências antes de removê-los. Conferir foco, seleção, menus, tamanho dos painéis e ciclo de abertura e fechamento das janelas.

**Resultado esperado:** o programa cria diretamente o layout aprovado, sem containers legados usados como suporte e sem botões invisíveis intermediando ações.

### 5. Organização interna e isolamento da compatibilidade

**Status:** concluída e verificada em 17/09/2026.

**Direção:** reavaliar os controladores grandes e separar responsabilidades onde houver benefício concreto. Isolar a leitura e conversão de estruturas antigas.

**Cuidados principais:** preservar o caminho compartilhado de renderização, os contratos do JSON, os assets, o histórico e a recuperação de arquivos. Não remover suporte a modelos antigos ou migrações apenas por conterem referências ao legado.

**Resultado esperado:** responsabilidades claras, menos duplicação e compatibilidade concentrada em pontos identificáveis, sem mudar a aparência dos documentos nem os fluxos aprovados.

### 6. Consistência visual, recursos e organização do projeto

**Status:** concluída e verificada em 17/09/2026.

**Direção:** concluir a centralização das cores de interface; revisar ícones, fontes, textos, traduções, documentação, testes e arquivos incluídos nos pacotes.

**Cuidados principais:** distinguir cores da interface das cores da arte; comprovar que um recurso não é usado antes de excluí-lo; preservar licenças, fixtures e ferramentas úteis. Artefatos locais ignorados pelo Git e dados do usuário não são código morto e não devem ser apagados indiscriminadamente.

**Resultado esperado:** temas coerentes, recursos necessários bem definidos, documentação atual separada do histórico e empacotamento sem resíduos desnecessários.

### 7. Auditoria final da limpeza

**Status:** pendente.

**Direção:** comparar o programa com a referência da etapa 3 e revisar novamente as dívidas identificadas, considerando a estrutura que existir neste momento.

**Cuidados principais:** conferir fluxos completos, desempenho, persistência, modelos antigos e resultado de impressão; testar os sistemas operacionais e pacotes disponíveis. Não declarar validação multiplataforma com base apenas nos testes do Linux.

**Resultado esperado:** dívida técnica identificada resolvida ou explicitamente justificada como compatibilidade necessária, sem regressões conhecidas nos fluxos verificados e com limitações de validação registradas.

## Depois deste roadmap

Com as funcionalidades e o layout estabilizados, criar o tutorial, revisar suas traduções e concluir a preparação para distribuição. O tutorial fica fora da limpeza técnica para evitar refazê-lo durante as mudanças.

## Registro de continuidade

Ao encerrar uma etapa ou sessão, registrar brevemente:

- **Etapa e estado:**
- **Concluído e verificado:**
- **Pendências ou decisões em aberto:**
- **Próximo ponto de retomada:**

### Registro — etapa 1

- **Etapa e estado:** imagens dinâmicas por registro concluídas.
- **Concluído e verificado:** formas fechadas podem criar um campo de imagem; a pasta externa fica lembrada localmente por modelo; nomes com ou sem extensão são resolvidos com diagnóstico de ausência e ambiguidade; há enquadramento por preenchimento/corte ou ajuste integral; prévia, cache estático e geração compartilham o mesmo renderizador; o recurso participa da união de campos das duas páginas sem incorporar a pasta ao arquivo do modelo; interface e mensagens foram traduzidas para inglês e espanhol.
- **Verificação executada:** 107 testes e 10 subtestes da suíte principal, 49 testes do editor, compilação dos módulos alterados e abertura básica do workspace em modo offscreen.
- **Pendências ou decisões em aberto:** validação visual manual com fotografias reais em PNG, PDF e imposição permanece para a etapa 3, junto da revisão integrada dos fluxos.
- **Próximo ponto de retomada:** reavaliar o agrupamento e definir o escopo concreto da etapa 2, redimensionamento proporcional de grupos.

### Registro — etapa 2

- **Etapa e estado:** redimensionamento proporcional de grupos concluído.
- **Concluído e verificado:** qualquer seleção de dois ou mais objetos, permanente ou temporária, recebe uma única moldura com oito alças e sem alças individuais; o redimensionamento aplica uma escala uniforme a toda a área selecionada; a seleção por arraste aceita somente itens totalmente contidos; a seleção múltipla também funciona pelo painel de camadas com Ctrl; posições relativas e rotações são preservadas; caixas de texto escalam dimensões, fonte global, recuo e tamanhos ricos por caractere; formas escalam contorno e arredondamentos; formas usadas como máscara escalam suas imagens internas uma única vez; linhas mantêm a direção durante a escala coletiva; itens bloqueados não são transformados.
- **Histórico e persistência:** cada gesto de redimensionamento gera uma única alteração no histórico, com undo e redo restaurando o conjunto; os valores finais continuam sendo gravados nas propriedades nativas dos objetos, sem transformações temporárias dependentes da interface.
- **Verificação executada:** 56 testes do editor, incluindo moldura coletiva, seleção por contenção integral, escala proporcional, tipografia rica, máscaras e histórico; 107 testes e 10 subtestes da suíte principal; compilação dos módulos e verificação de whitespace.
- **Pendências ou decisões em aberto:** a avaliação visual com composições reais e grupos grandes fica reunida na etapa 3 de estabilização.
- **Próximo ponto de retomada:** iniciar a etapa 3 revisando os fluxos completos e definindo uma matriz curta de regressões e desempenho antes de qualquer limpeza estrutural.

### Registro — etapa 3

- **Etapa e estado:** estabilização e fechamento do escopo funcional concluídos.
- **Concluído e verificado:** foi criada a referência [VALIDACAO_ETAPA_3.md](VALIDACAO_ETAPA_3.md), cobrindo modelos v3/v4, editor e histórico, duas páginas, cópia, máscaras, grupos, fontes, dados em lote, imagens dinâmicas, geração, links, imposição e duplex; workspace e editor também passaram pelo ciclo básico de abertura e fechamento.
- **Desempenho de referência:** colagem de 500 × 5 células em aproximadamente 40 ms; 200 renderizações do modelo A4 `teste2` em 3,833 s com cache estático; os três modelos reais versionados foram normalizados e renderizados sem erro.
- **Verificação executada:** 107 testes e 10 subtestes da suíte principal; 59 testes do editor; compilação e smoke test das janelas em modo offscreen.
- **Decisão de escopo:** não foi identificada outra funcionalidade indispensável antes da limpeza. O tutorial continua reservado para depois da refatoração.
- **Limites registrados:** testes nativos de Windows e macOS, prova física de duplex e revisão visual dos pacotes finais permanecem para a auditoria da etapa 7.
- **Próximo ponto de retomada:** iniciar a etapa 4 pelo workspace, mapeando e substituindo dependências dos containers legados antes de removê-los.

### Registro — etapa 4, corte 1

- **Etapa e estado:** em andamento; workspace e planilha concluídos, editor em migração.
- **Concluído e verificado:** o workspace agora cria diretamente o divisor, a área de prévia, a barra do modelo, o rodapé de saída e a lateral de dados; a antiga coluna invisível de ações foi removida e as ações de menu chamam diretamente os controladores. A planilha também deixou de criar e desmontar sua barra protótipo. O `ControlsPanel` legado foi excluído.
- **Correções encontradas durante o corte:** instalações limpas voltaram a criar um modelo de exemplo v4 válido com `layer_order`; workers de miniatura agora são rastreados e encerrados junto da janela.
- **Editor:** o container antigo deixou de permanecer oculto durante toda a sessão; controles sem consumidor atual são destruídos. Ainda falta impedir sua construção transitória no início do editor, substituindo a inicialização antiga por uma fábrica direta dos controles usados pelo frontend atual.
- **Verificação executada:** 109 testes e 10 subtestes da suíte principal; 59 testes do editor; smoke test e captura visual offscreen do workspace reconstruído.
- **Próximo ponto de retomada:** separar a criação dos controles do editor de seus layouts antigos, remover o último `takeCentralWidget()` e então concluir a etapa 4.

### Registro — etapa 4, conclusão

- **Etapa e estado:** construção direta da interface atual concluída.
- **Concluído e verificado:** workspace, planilha e editor agora criam diretamente os layouts aprovados. O editor deixou de montar três colunas antigas antes do frontend atual; foram removidos `takeCentralWidget()`, a barra legada de camadas, os controles antigos de fundo e guias e o botão invisível de zerar rotação. Cena, controles funcionais e sinais são inicializados sem uma árvore visual descartável.
- **Ciclo de vida:** os painéis funcionais de propriedades e texto têm propriedade Qt explícita e permanecem válidos após o processamento de exclusões adiadas. A auditoria dos atributos da janela não encontrou wrappers Qt destruídos.
- **Verificação executada:** 109 testes e 10 subtestes da suíte principal; 60 testes do editor; compilação, auditoria de objetos Qt e captura visual offscreen do editor.
- **Pendências ou decisões em aberto:** a separação dos painéis funcionais em controladores menores pertence à etapa 5; não há container legado sustentando a interface atual.
- **Próximo ponto de retomada:** iniciar a etapa 5 reavaliando responsabilidades do `EditorWindow`, dos painéis de propriedades e da compatibilidade de modelos antes de definir os cortes internos.

### Registro — etapa 5

- **Etapa e estado:** organização interna e isolamento da compatibilidade concluídos.
- **Responsabilidades separadas:** `controls.py` passou a criar cena e controles funcionais; `document_session.py` concentra página ativa, seleção por página, operações frente/verso e estado de histórico; `EditorWindow` permanece como coordenador dos fluxos de edição.
- **Compatibilidade:** `core/model_document.py` continua como única autoridade para leitura, validação e normalização v3/v4. A tolerância adicional exigida pela cena foi isolada em `model_adapter.py`, que trabalha sobre uma cópia e não modifica os dados recebidos. Nenhum suporte a modelos antigos, backups ou recuperação foi removido.
- **Clareza do renderer:** a visão entregue a editor e renderer passou a ser descrita como visão plana de página; o caminho realmente legado do renderer permanece explicitamente isolado apenas para modelos sem a estrutura moderna de camadas.
- **Verificação executada:** 111 testes e 10 subtestes da suíte principal; 60 testes do editor; testes específicos de adaptação sem mutação; compilação dos módulos reorganizados e auditoria de ciclo de vida Qt.
- **Próximo ponto de retomada:** iniciar a etapa 6 revisando temas, ícones, fontes, textos, traduções, documentação e recursos efetivamente incluídos na distribuição.

### Registro — etapa 6

- **Etapa e estado:** consistência visual, recursos e organização concluídos.
- **Temas:** cores visíveis da interface que ainda estavam presas ao tema escuro passaram a usar papéis semânticos do tema. As cores dos documentos, textos, formas e demais elementos da arte permaneceram independentes.
- **Recursos:** setas de campos numéricos e caixas de seleção foram movidas das pastas internas das funcionalidades para `assets/icons/ui/navigation`. O carregamento, os testes e o inventário de ícones agora usam a API central de recursos.
- **Distribuição:** o pacote Nuitka passou a incluir esses controles pelo diretório único `assets`, sem regras extras para pastas internas do editor e do workspace.
- **Textos e traduções:** mensagens obsoletas da antiga proteção de campos removidos foram retiradas dos catálogos em inglês e espanhol, e os arquivos compilados foram regenerados.
- **Verificação executada:** 111 testes e 10 subtestes da suíte principal; 60 testes do editor; compilação dos módulos alterados; validação dos SVGs e auditoria das referências estáticas de recursos.
- **Próximo ponto de retomada:** iniciar a etapa 7 comparando os fluxos completos com a referência funcional e registrando separadamente as validações que exigem Windows, macOS ou impressão física.
