# Plano de modernização da interface do C.O.M.S.O.C.

> Documento vivo de planejamento, execução e acompanhamento.
>
> **Criado em:** 6 de agosto de 2026  
> **Última atualização:** 6 de agosto de 2026  
> **Estado geral:** planejamento inicial  
> **Próxima etapa:** Fase 0 — registrar a interface atual e definir a direção visual

---

## 1. Finalidade deste documento

Este arquivo é a fonte principal de acompanhamento da modernização visual do C.O.M.S.O.C. Ele deve registrar:

- o objetivo do trabalho;
- as decisões já tomadas;
- o que faz e o que não faz parte do escopo;
- a ordem das etapas;
- as tarefas concluídas, em andamento e pendentes;
- os critérios usados para aceitar cada entrega;
- problemas encontrados durante a execução;
- mudanças de direção e suas justificativas.

O documento deve ser atualizado junto com cada mudança relevante da interface. Uma tarefa não deve ser marcada como concluída apenas porque o código foi escrito: ela precisa atender ao respectivo critério de aceite e ter sua evidência registrada.

### 1.1 Como atualizar este plano

Usar os seguintes estados:

- `[ ]` — não iniciado;
- `[ ] **EM ANDAMENTO**` — trabalho iniciado, mas ainda não aceito;
- `[x]` — concluído e verificado;
- `[ ] **BLOQUEADO**` — não pode prosseguir; explicar o motivo no registro da fase;
- `[ ] **DESCARTADO**` — decisão consciente de não executar; explicar o motivo.

Ao concluir uma tarefa:

1. marcar o item com `[x]`;
2. acrescentar a data de conclusão;
3. registrar a evidência, como arquivos alterados, imagens comparativas ou testes executados;
4. atualizar o resumo de progresso da fase;
5. adicionar uma entrada no histórico ao final deste documento se houver decisão, risco ou mudança relevante.

---

## 2. Objetivo do projeto de modernização

O objetivo principal é transformar a interface atual, que ainda apresenta características visuais de protótipo, em um software desktop com aparência profissional, identidade própria e comportamento visual consistente, sem comprometer o motor de produção que já funciona.

O resultado esperado deve:

- parecer um produto concluído, e não uma ferramenta experimental;
- transmitir clareza, confiança e qualidade institucional;
- reduzir poluição visual e inconsistências;
- organizar melhor ações, propriedades, informações e estados;
- funcionar corretamente em Windows, macOS e Linux;
- preservar todos os fluxos de trabalho existentes;
- manter o renderer, PDF, imposição e processamento em PySide6;
- permitir a introdução gradual de Qt Quick/QML;
- possibilitar, se os testes confirmarem sua adequação, um frontend integralmente QML no longo prazo.

### 2.1 Definição de sucesso

O trabalho será considerado bem-sucedido quando:

1. toda a interface possuir uma linguagem visual única;
2. não houver estilos arbitrários espalhados pelas telas;
3. controles equivalentes tiverem aparência e comportamento equivalentes;
4. as ações mais importantes estiverem visualmente claras;
5. os estados de carregamento, sucesso, alerta, erro e ausência de conteúdo estiverem bem comunicados;
6. a interface permanecer utilizável em diferentes escalas de tela e DPI;
7. os fluxos funcionais atuais continuarem operando;
8. as partes migradas para QML apresentarem qualidade igual ou superior às versões em Qt Widgets;
9. o editor QML, caso seja concluído, atingir paridade funcional comprovada antes da aposentadoria do editor legado;
10. o produto puder ser empacotado e distribuído de maneira previsível.

---

## 3. Decisões arquiteturais já tomadas

Estas decisões representam o entendimento atual e só devem ser alteradas mediante registro no histórico de decisões.

### DEC-001 — PySide6 permanece no projeto

**Decisão:** manter PySide6 como tecnologia permanente do motor de produção.

O PySide6 não é tratado como bloqueio técnico ou comercial. Suas obrigações LGPL serão administradas no processo de distribuição.

Continuam em Python/Qt:

- renderização por `QPainter`;
- medição e resolução de fontes;
- geração por `QPdfWriter`;
- imposição;
- previews de produção;
- processamento paralelo por `QThread`;
- integração com `pypdf` para links;
- regras de geração e persistência que não sejam exclusivamente visuais.

### DEC-002 — Tauri e Electron não fazem parte do plano atual

**Decisão:** não introduzir Tauri, Electron, React, Rust ou sidecar como parte desta modernização.

Essas tecnologias podem ser reavaliadas no futuro, mas não são proporcionais ao problema atual. QML permite modernizar a interface mantendo o mesmo ecossistema Qt e comunicação direta com o backend Python.

### DEC-003 — Modernização em duas camadas

**Decisão:** executar primeiro uma padronização visual completa da interface Qt Widgets atual e, depois, introduzir QML gradualmente.

A padronização inicial serve para:

- melhorar o produto mais cedo;
- definir a identidade visual antes de reescrever telas;
- criar uma referência concreta para os componentes QML;
- evitar que cada tela nova invente seu próprio estilo;
- separar problemas de design de problemas de tecnologia.

### DEC-004 — QML é frontend, Python é backend

**Decisão:** manter regras de negócio e operações de produção em Python. QML deve concentrar apresentação, composição visual, animações e interação imediata.

Não colocar em QML, sem justificativa registrada:

- gravação direta de arquivos de modelo;
- regras de migração de dados;
- geração de PDF ou imagem final;
- gerenciamento destrutivo de assets;
- planejamento de imposição;
- lógica complexa de negócio;
- operações longas ou bloqueantes.

### DEC-005 — Editor novo convive com o legado

**Decisão:** o novo editor QML será desenvolvido paralelamente ao editor Qt Widgets atual.

Durante a migração:

- o editor legado permanece funcional como referência;
- o editor QML fica atrás de uma opção de desenvolvimento ou recurso experimental;
- ambos trabalham com cópias controladas dos mesmos modelos de teste;
- o renderer de produção continua sendo a autoridade do resultado final;
- o editor legado só é retirado do pacote depois da paridade comprovada.

### DEC-006 — RapidRAW é somente referência estética

**Decisão:** não consultar, copiar, adaptar ou traduzir código-fonte do RapidRAW.

Sua licença AGPL-3.0 não é compatível com os objetivos de distribuição do C.O.M.S.O.C. Podem ser observados apenas aspectos visuais e comportamentos disponíveis ao usuário, como hierarquia, espaçamento, organização, feedback e fluidez.

---

## 4. Fora do escopo deste trabalho

Não fazem parte do objetivo atual:

- substituir o renderer Qt por Rust, JavaScript ou outro motor;
- remover PySide6;
- mudar a forma como o PDF é produzido sem necessidade funcional;
- reescrever a imposição;
- trocar `pypdf` sem motivo técnico ou de licença;
- alterar formatos de saída apenas por causa da modernização visual;
- adicionar serviços em nuvem;
- criar versão web, mobile ou servidor;
- copiar interfaces ou código de projetos AGPL;
- adicionar recursos de produto não relacionados à modernização, salvo quando aprovados e registrados separadamente.

Correções necessárias descobertas durante a modernização devem ser registradas. Elas não devem ser misturadas silenciosamente com mudanças visuais.

---

## 5. Princípios de execução

### 5.1 Preservar o que já funciona

Uma melhoria estética não pode alterar silenciosamente:

- posição ou dimensão dos elementos do documento;
- funcionamento de snap, resize ou rotação;
- formato dos modelos;
- resultado do renderer;
- ordem das páginas;
- links em PDF;
- regras de imposição;
- interpretação dos dados colados;
- nomes e caminhos dos arquivos gerados.

### 5.2 Uma única fonte visual

Cores, fontes, espaçamentos, tamanhos, raios, ícones e estados não devem ser definidos arbitrariamente dentro de cada tela.

Durante a fase Qt Widgets, criar uma fonte central de estilos. Durante a fase QML, criar tokens e componentes QML equivalentes.

### 5.3 QML gradual e reversível

Cada tela QML deve ser introduzida separadamente, com uma forma clara de retornar à versão anterior durante o desenvolvimento.

### 5.4 Resultado antes de tecnologia

QML só deve substituir uma tela quando trouxer benefício perceptível em pelo menos um destes pontos:

- qualidade visual;
- clareza de uso;
- fluidez;
- manutenção;
- acessibilidade;
- adaptação a tamanhos e DPI;
- capacidade de evolução.

### 5.5 Evidência antes de aposentadoria

Nenhuma implementação legada será removida apenas por impressão subjetiva de que a nova “parece funcionar”. A substituição exige uma lista explícita de paridade e testes dos fluxos principais.

---

## 6. Visão do sistema ao final da modernização

```text
Frontend Qt Quick/QML
├── Janela principal
├── Biblioteca e gerenciamento de modelos
├── Planilha e configuração de geração
├── Previews, diálogos e notificações
├── Painéis de propriedades
└── Editor visual QML
        │
        ▼
Backend Python/PySide6
├── Modelo do documento e persistência
├── Gerenciamento de assets
├── Parsing de planilhas e rich text
├── Histórico e comandos reutilizáveis
├── Geração e progresso
├── Renderer QPainter/QTextDocument
├── PDF e links
└── Imposição e processamento paralelo
```

Durante a transição:

```text
Aplicação modernizada
├── Telas já migradas para QML
├── Telas ainda padronizadas em Qt Widgets
├── Editor legado Qt Widgets
└── Editor QML experimental
```

---

## 7. Regras do sistema de design

As decisões concretas de cor e aparência ainda serão definidas na Fase 0. A estrutura abaixo deve ser respeitada.

### 7.1 Tokens obrigatórios

- **Cores:** fundo principal, superfícies, superfícies elevadas, bordas, texto primário, texto secundário, texto desabilitado, destaque, sucesso, alerta e erro.
- **Tipografia:** família, títulos, subtítulos, corpo, rótulos, ajuda e valores técnicos.
- **Espaçamento:** escala reutilizável, preferencialmente baseada em múltiplos de 4 px.
- **Dimensões:** alturas padrão de campos, botões, barras e linhas.
- **Raios:** poucos valores padronizados, sem arredondamento arbitrário.
- **Elevação:** regras discretas para sombras e separação entre superfícies.
- **Ícones:** um único conjunto visual, com licença permissiva registrada.
- **Movimento:** durações e curvas padronizadas para animações úteis.
- **Foco:** indicação visível e consistente para navegação por teclado.

### 7.2 Estados obrigatórios dos componentes

Todo componente interativo deve definir, quando aplicável:

- normal;
- hover;
- pressionado;
- selecionado;
- em foco;
- desabilitado;
- carregando;
- erro;
- sucesso.

### 7.3 Hierarquia das ações

- **Primária:** principal avanço da tela, no máximo uma ação dominante por região.
- **Secundária:** ação disponível, mas não dominante.
- **Terciária:** ação de baixa ênfase, normalmente textual ou iconográfica.
- **Destrutiva:** ação que remove, substitui ou perde dados; deve ter semântica própria e confirmação quando necessária.

### 7.4 Requisitos de experiência

- Evitar excesso de bordas e caixas.
- Usar espaço e agrupamento para comunicar relação entre elementos.
- Não depender apenas de cor para transmitir estado.
- Exibir unidade de medida junto a valores técnicos.
- Manter nomes de ações claros e consistentes.
- Não esconder funções essenciais apenas em ícones sem tooltip.
- Preservar atalhos e navegação por teclado.
- Respeitar escalonamento de interface e fontes do sistema.
- Preferir animações curtas que expliquem mudança de estado; não usar movimento decorativo excessivo.

---

## 8. Resumo das fases

| Fase | Nome | Estado | Resultado principal |
|---|---|---|---|
| 0 | Baseline e direção visual | Não iniciada | Referência do estado atual e identidade aprovada |
| 1 | Fundação visual Qt Widgets | Não iniciada | Tema e componentes centralizados |
| 2 | Padronização completa das telas atuais | Não iniciada | Aplicativo atual visualmente coerente |
| 3 | Polimento de UX e acessibilidade | Não iniciada | Estados, feedback e navegação profissionais |
| 4 | Gate de avaliação Qt Widgets × QML | Não iniciada | Decisão baseada no produto já modernizado |
| 5 | Fundação QML e integração Python | Não iniciada | Base técnica QML reutilizável |
| 6 | Migração gradual das telas não editoriais | Não iniciada | Shell e fluxos principais em QML |
| 7 | Novo editor QML paralelo | Não iniciada | Editor QML com paridade funcional |
| 8 | Aposentadoria do frontend legado | Não iniciada | Frontend final e código legado fora do pacote |
| 9 | Preparação final para distribuição | Não iniciada | Builds verificadas e conformidade organizada |

---

## 9. Fase 0 — Baseline e direção visual

**Objetivo:** registrar o estado atual e aprovar uma direção visual antes de modificar as telas.

### Tarefas

- [ ] **VIS-001** Capturar screenshots da aplicação atual nos temas claro e escuro.
- [ ] **VIS-002** Registrar as telas e estados existentes: principal, editor, propriedades, tabela, preview, exportação, importação, logs e mensagens.
- [ ] **VIS-003** Registrar resoluções e escalas mínimas que precisam ser atendidas.
- [ ] **VIS-004** Identificar inconsistências de tipografia, espaçamento, alinhamento, ícones, cores, bordas e hierarquia.
- [ ] **VIS-005** Definir três a cinco adjetivos para a personalidade visual do produto.
- [ ] **VIS-006** Criar painel de referências visuais sem consultar código de projetos incompatíveis.
- [ ] **VIS-007** Definir a paleta inicial dos temas claro e escuro.
- [ ] **VIS-008** Definir tipografia e escala de tamanhos.
- [ ] **VIS-009** Definir escala de espaçamentos, dimensões de controles e raios.
- [ ] **VIS-010** Selecionar conjunto de ícones e registrar sua licença.
- [ ] **VIS-011** Criar mockup da janela principal.
- [ ] **VIS-012** Criar mockup do editor, preservando o canvas e os fluxos atuais.
- [ ] **VIS-013** Aprovar os mockups antes da implementação geral.

### Critério de aceite

- Existe uma referência visual aprovada para a janela principal e para o editor.
- Tokens fundamentais estão registrados.
- As principais telas e estados atuais possuem screenshots de referência.
- A direção visual pode ser explicada sem citar apenas “parecido com o programa X”.

### Evidências da fase

Ainda não registradas.

---

## 10. Fase 1 — Fundação visual Qt Widgets

**Objetivo:** substituir estilos fragmentados por um sistema visual centralizado, ainda sem migrar telas para QML.

### Tarefas

- [ ] **WID-001** Inventariar todos os `setStyleSheet` e usos manuais de `QPalette`.
- [ ] **WID-002** Criar módulo central de tokens visuais.
- [ ] **WID-003** Criar stylesheet global organizado por componente e estado.
- [ ] **WID-004** Definir estratégia para tema claro e escuro sem duplicação desnecessária.
- [ ] **WID-005** Padronizar botões primários, secundários, terciários, iconográficos e destrutivos.
- [ ] **WID-006** Padronizar campos de texto, números, combos, checkboxes e seletores.
- [ ] **WID-007** Padronizar barras, menus, tabs, splitters, scrollbars e tooltips.
- [ ] **WID-008** Padronizar tabela, cabeçalhos, seleção e células editáveis.
- [ ] **WID-009** Padronizar painéis, grupos, títulos de seção e separadores.
- [ ] **WID-010** Padronizar diálogos e seus rodapés de ação.
- [ ] **WID-011** Substituir ícones improvisados ou caracteres inconsistentes pelo conjunto aprovado.
- [ ] **WID-012** Remover estilos inline que já estejam representados no sistema central.
- [ ] **WID-013** Garantir que componentes customizados exponham `objectName` ou propriedades apropriadas para estilização específica.
- [ ] **WID-014** Criar uma pequena galeria interna de componentes para inspeção visual dos estados.

### Critério de aceite

- A maior parte da aparência comum é controlada centralmente.
- Não existem cores ou dimensões duplicadas arbitrariamente nas telas migradas.
- Temas claro e escuro possuem contraste e hierarquia coerentes.
- A galeria permite visualizar estados normais, hover, foco, pressionado e desabilitado.

### Riscos específicos

- Stylesheets globais podem alterar métricas de controles e quebrar layouts apertados.
- Seletores amplos podem afetar componentes não relacionados.
- Cores fixadas dentro de delegates podem não acompanhar o tema.

### Mitigação

- Aplicar a fundação por pequenos grupos de componentes.
- Preferir seletores específicos quando um estilo tiver efeito estrutural.
- Testar tabela, editor de texto, dialogs e estados desabilitados após cada grupo.

---

## 11. Fase 2 — Padronização completa das telas atuais

**Objetivo:** aplicar o sistema visual e reorganizar a hierarquia de cada tela sem mudar as regras de produção.

### 11.1 Janela principal e workspace

- [ ] **SCR-001** Reorganizar hierarquia visual da janela principal.
- [ ] **SCR-002** Destacar seleção e operações de modelo.
- [ ] **SCR-003** Padronizar painel de configuração e ação principal de geração.
- [ ] **SCR-004** Melhorar separação visual entre modelos, dados, preview e produção.
- [ ] **SCR-005** Padronizar barra de progresso e estados de geração.
- [ ] **SCR-006** Criar estado vazio para ausência de modelos ou seleção.

### 11.2 Preview

- [ ] **SCR-010** Padronizar moldura e fundo da área de preview.
- [ ] **SCR-011** Criar estados de carregamento, indisponibilidade e erro.
- [ ] **SCR-012** Verificar proporção, redimensionamento e nitidez em DPI diferentes.

### 11.3 Planilha integrada

- [ ] **SCR-020** Padronizar cabeçalhos, linhas, seleção e edição.
- [ ] **SCR-021** Tornar controles de quantidade e assinatura visualmente claros.
- [ ] **SCR-022** Melhorar comunicação de colagem, formatação e dados inválidos.
- [ ] **SCR-023** Preservar atalhos e comportamento de clipboard.
- [ ] **SCR-024** Verificar tabelas vazias, grandes e com textos extensos.

### 11.4 Editor legado Qt Widgets

- [ ] **SCR-030** Modernizar barras e ações sem alterar o `QGraphicsView`.
- [ ] **SCR-031** Reorganizar guias, documento, zoom e ações de edição.
- [ ] **SCR-032** Padronizar alças, destaque de seleção e guias quando possível sem modificar a semântica.
- [ ] **SCR-033** Padronizar painel de camadas.
- [ ] **SCR-034** Padronizar botões de salvar, fechar, desfazer e refazer.
- [ ] **SCR-035** Tornar ações destrutivas visualmente coerentes e seguras.

### 11.5 Painéis de propriedades

- [ ] **SCR-040** Criar hierarquia consistente de títulos, rótulos e valores.
- [ ] **SCR-041** Agrupar propriedades por assunto.
- [ ] **SCR-042** Padronizar unidades, campos numéricos, alinhamentos e controles tipográficos.
- [ ] **SCR-043** Melhorar indicação de estado misto em multisseleção, quando aplicável.
- [ ] **SCR-044** Garantir leitura adequada em painéis estreitos.

### 11.6 Diálogos, logs e mensagens

- [ ] **SCR-050** Padronizar importação, exportação e conflitos.
- [ ] **SCR-051** Padronizar diálogo de geração e imposição.
- [ ] **SCR-052** Padronizar confirmações de remoção, substituição e saída sem salvar.
- [ ] **SCR-053** Padronizar painel de logs.
- [ ] **SCR-054** Padronizar tooltips, avisos e mensagens de erro.
- [ ] **SCR-055** Substituir mensagens excessivamente técnicas por linguagem útil ao usuário, preservando detalhes diagnósticos nos logs.

### Critério de aceite

- Todas as telas ativas seguem o sistema visual.
- A janela principal e o editor parecem partes do mesmo produto.
- Não há perda funcional nos fluxos de fumaça definidos na seção 18.
- Os temas claro e escuro foram verificados.
- A aplicação continua utilizável em escala de 100%, 125%, 150% e 200%, conforme disponibilidade do sistema de teste.

---

## 12. Fase 3 — Polimento de UX e acessibilidade

**Objetivo:** melhorar comunicação, resposta e previsibilidade, não apenas aparência estática.

### Tarefas

- [ ] **UX-001** Definir estados de carregamento para operações demoradas.
- [ ] **UX-002** Garantir feedback imediato para salvar, importar, exportar e gerar.
- [ ] **UX-003** Diferenciar aviso recuperável de erro bloqueante.
- [ ] **UX-004** Revisar textos de botões, labels, tooltips e mensagens.
- [ ] **UX-005** Revisar ordem de tabulação e navegação por teclado.
- [ ] **UX-006** Garantir indicador de foco visível.
- [ ] **UX-007** Revisar contraste dos temas.
- [ ] **UX-008** Garantir áreas clicáveis adequadas para ícones.
- [ ] **UX-009** Revisar atalhos e conflitos entre janela principal, tabela e editor.
- [ ] **UX-010** Criar estados vazios instrutivos.
- [ ] **UX-011** Padronizar confirmação e possibilidade de cancelamento em operações longas.
- [ ] **UX-012** Evitar travamento visual durante geração e previews.
- [ ] **UX-013** Verificar comportamento com nomes, caminhos e textos longos.
- [ ] **UX-014** Verificar acentos, Unicode e teclado PT-BR.
- [ ] **UX-015** Usar animações somente quando ajudarem a compreender mudança de estado.

### Critério de aceite

- O usuário sempre entende se uma operação começou, terminou, falhou ou foi cancelada.
- Funções essenciais podem ser operadas por teclado.
- Textos importantes permanecem legíveis nos dois temas.
- Nenhuma animação prejudica desempenho ou velocidade de trabalho.

---

## 13. Fase 4 — Gate de avaliação Qt Widgets × QML

**Objetivo:** decidir o ritmo e a extensão da migração QML com base no resultado real da interface padronizada.

### Perguntas obrigatórias

- [ ] **GATE-001** A interface Widgets já atingiu aparência profissional suficiente?
- [ ] **GATE-002** Quais limitações concretas permanecem?
- [ ] **GATE-003** Essas limitações são de tecnologia ou de design ainda incompleto?
- [ ] **GATE-004** QML melhora claramente animação, composição, manutenção ou adaptação?
- [ ] **GATE-005** O custo de reescrever cada tela é proporcional ao benefício?
- [ ] **GATE-006** O produto já pode ser distribuído antes da migração QML completa?

### Possíveis decisões

1. **Widgets suficientes:** distribuir a versão modernizada e tratar QML como evolução futura.
2. **Migração parcial:** usar QML em telas com benefício claro e manter o editor legado.
3. **Migração integral gradual:** seguir para frontend QML completo, incluindo novo editor paralelo.

### Critério de aceite

- A decisão está registrada com exemplos visuais e motivos concretos.
- Não se inicia uma migração integral apenas porque QML é “mais moderno”.

---

## 14. Fase 5 — Fundação QML e integração Python

**Objetivo:** criar uma base QML consistente e conectada ao backend atual, sem duplicar regras de negócio.

### Tarefas técnicas

- [ ] **QML-001** Definir estrutura de diretórios QML.
- [ ] **QML-002** Criar tokens QML equivalentes aos tokens usados nos Widgets.
- [ ] **QML-003** Criar biblioteca de componentes reutilizáveis.
- [ ] **QML-004** Definir estilo-base: customizado, FluentWinUI3, Material, Universal ou combinação controlada.
- [ ] **QML-005** Criar bootstrap com `QQmlApplicationEngine`.
- [ ] **QML-006** Definir padrão de exposição Python–QML por `QObject`, `Signal`, `Slot` e `Property`.
- [ ] **QML-007** Definir padrão de listas e tabelas com modelos Qt.
- [ ] **QML-008** Definir propriedade e ciclo de vida dos objetos expostos.
- [ ] **QML-009** Definir tratamento central de erros entre Python e QML.
- [ ] **QML-010** Definir navegação, dialogs e gerenciamento de janelas.
- [ ] **QML-011** Criar galeria QML dos componentes e estados.
- [ ] **QML-012** Verificar tema claro, escuro, DPI e teclado.
- [ ] **QML-013** Adaptar o build Nuitka para incluir arquivos e plugins QML.
- [ ] **QML-014** Gerar executável de teste em pelo menos uma plataforma.

### Guardas arquiteturais

- QML não deve ler ou gravar diretamente os arquivos de modelo.
- Operações longas não podem bloquear a thread da interface.
- Movimentos de alta frequência devem evitar chamadas Python pesadas a cada frame.
- Componentes não devem acessar singletons globais indiscriminadamente.
- Toda API exposta ao QML deve ter finalidade documentada.

### Critério de aceite

- Existe uma aplicação QML mínima empacotável.
- A galeria visual reproduz a identidade aprovada.
- QML consegue ler estado, executar uma ação Python e receber progresso/erro.
- Temas e escalas funcionam sem warnings críticos.

---

## 15. Fase 6 — Migração gradual das telas não editoriais

**Objetivo:** migrar as telas de menor risco antes do editor visual.

### Ordem recomendada

#### 6.1 Componentes auxiliares

- [ ] **MIG-001** Notificações e mensagens não modais.
- [ ] **MIG-002** Diálogos simples.
- [ ] **MIG-003** Tela de informações/sobre.
- [ ] **MIG-004** Configurações de aparência e preferências.

#### 6.2 Biblioteca e gerenciamento de modelos

- [ ] **MIG-010** Lista/biblioteca de modelos.
- [ ] **MIG-011** Criar, duplicar, renomear e remover.
- [ ] **MIG-012** Importar e exportar modelos.
- [ ] **MIG-013** Estados vazios, conflitos e erros.

#### 6.3 Preview e geração

- [ ] **MIG-020** Preview dinâmico.
- [ ] **MIG-021** Configurações de nomenclatura e saída.
- [ ] **MIG-022** Diálogo de exportação e imposição.
- [ ] **MIG-023** Progresso, cancelamento e resumo de geração.
- [ ] **MIG-024** Abertura da pasta ou resultado final.

#### 6.4 Planilha

- [ ] **MIG-030** Modelo de dados Python para exposição ao QML.
- [ ] **MIG-031** TableView com cabeçalhos e seleção.
- [ ] **MIG-032** Edição de células.
- [ ] **MIG-033** Colagem de Google Sheets, Excel, LibreOffice, HTML e TSV.
- [ ] **MIG-034** Rich text e formatação por atalhos.
- [ ] **MIG-035** Quantidade e assinatura por linha.
- [ ] **MIG-036** Desempenho com tabelas grandes.

#### 6.5 Shell principal

- [ ] **MIG-040** Janela principal QML como entrada padrão experimental.
- [ ] **MIG-041** Integração de todos os painéis migrados.
- [ ] **MIG-042** Abertura do editor legado em janela Qt Widgets separada.
- [ ] **MIG-043** Persistência de tamanho, posição, painéis e preferências.
- [ ] **MIG-044** Teste completo do fluxo modelo → dados → preview → geração.

### Critério de aceite

- O fluxo principal pode ser realizado no shell QML.
- O editor legado abre e salva corretamente a partir do shell QML.
- O resultado produzido pelo backend permanece equivalente.
- A versão Widgets continua acessível durante a fase experimental.

---

## 16. Fase 7 — Novo editor QML paralelo

**Objetivo:** criar um editor visual QML com paridade funcional, mantendo o editor legado como referência durante todo o processo.

### 16.1 Contrato e ambiente de comparação

- [ ] **EDQ-001** Documentar o estado de documento consumido pelo renderer.
- [ ] **EDQ-002** Criar conjunto controlado de modelos de teste.
- [ ] **EDQ-003** Criar abertura por cópia para impedir dano acidental aos modelos reais.
- [ ] **EDQ-004** Criar opção “Editor legado” e “Editor QML experimental”.
- [ ] **EDQ-005** Definir comparação do JSON produzido pelos dois editores.
- [ ] **EDQ-006** Definir comparação de preview e exportação final.

### 16.2 Canvas e documento

- [ ] **EDQ-010** Área de trabalho, fundo e dimensões do documento.
- [ ] **EDQ-011** Conversão consistente entre milímetros e pixels.
- [ ] **EDQ-012** Zoom, pan, enquadrar documento e reset.
- [ ] **EDQ-013** Réguas ou indicadores necessários.
- [ ] **EDQ-014** Guias horizontais e verticais.

### 16.3 Elementos

- [ ] **EDQ-020** Imagem de fundo.
- [ ] **EDQ-021** Elemento de imagem.
- [ ] **EDQ-022** Elemento de texto.
- [ ] **EDQ-023** Elemento de assinatura.
- [ ] **EDQ-024** Placeholders e conteúdo dinâmico.
- [ ] **EDQ-025** Visibilidade e bloqueio.

### 16.4 Interação e geometria

- [ ] **EDQ-030** Seleção simples.
- [ ] **EDQ-031** Multisseleção e seleção por área.
- [ ] **EDQ-032** Movimento e limites do documento.
- [ ] **EDQ-033** Oito alças de redimensionamento.
- [ ] **EDQ-034** Proporção bloqueada e livre.
- [ ] **EDQ-035** Rotação.
- [ ] **EDQ-036** Resize sensível à rotação e preservação da âncora.
- [ ] **EDQ-037** Snap em guias e limites.
- [ ] **EDQ-038** Snap de grupo e comportamento com zoom.
- [ ] **EDQ-039** Teclas de deslocamento, exclusão e modificadores.

### 16.5 Texto e tipografia

- [ ] **EDQ-040** Edição de texto simples.
- [ ] **EDQ-041** Negrito, itálico e sublinhado.
- [ ] **EDQ-042** Alinhamento horizontal e vertical.
- [ ] **EDQ-043** Recuo e altura de linha.
- [ ] **EDQ-044** Cor, família e tamanho da fonte.
- [ ] **EDQ-045** Aviso e fallback de fonte ausente.
- [ ] **EDQ-046** Comparação de quebras de linha com o renderer de produção.
- [ ] **EDQ-047** Preview canônico pelo renderer quando necessário.

### 16.6 Camadas, propriedades e histórico

- [ ] **EDQ-050** Lista e ordem de camadas.
- [ ] **EDQ-051** Renomear, duplicar, remover, ocultar e bloquear.
- [ ] **EDQ-052** Painel de propriedades reativo à seleção.
- [ ] **EDQ-053** Estado de propriedades em multisseleção.
- [ ] **EDQ-054** Undo e redo.
- [ ] **EDQ-055** Atalhos do editor.
- [ ] **EDQ-056** Estado modificado e confirmação ao fechar.

### 16.7 Persistência e assets

- [ ] **EDQ-060** Abrir modelos atuais sem alteração inesperada.
- [ ] **EDQ-061** Salvar e reabrir preservando todos os campos.
- [ ] **EDQ-062** Importar imagens e fundos com nomes seguros.
- [ ] **EDQ-063** Evitar colisão e exclusão indevida de assets.
- [ ] **EDQ-064** Compatibilidade com modelos antigos selecionados.
- [ ] **EDQ-065** Recuperação segura em erro de gravação.

### 16.8 Paridade e ativação

- [ ] **EDQ-070** Executar matriz completa de paridade.
- [ ] **EDQ-071** Resolver todas as diferenças classificadas como bloqueantes.
- [ ] **EDQ-072** Usar editor QML como padrão em builds de teste.
- [ ] **EDQ-073** Coletar feedback de uso real.
- [ ] **EDQ-074** Definir período de estabilidade antes de remover o legado.

### Critério de aceite

- Todos os itens obrigatórios da matriz de paridade estão aprovados.
- Modelos criados no editor QML produzem resultados corretos no renderer atual.
- Não há perda de dados ao abrir e salvar os modelos de teste.
- Snap, rotação, resize e texto foram verificados nos casos combinados, não apenas isoladamente.
- O novo editor foi usado em tarefas reais antes da aposentadoria do legado.

---

## 17. Fase 8 — Aposentadoria do frontend legado

**Objetivo:** remover as implementações visuais antigas do pacote distribuído somente após a estabilização do frontend QML.

### Tarefas

- [ ] **LEG-001** Confirmar que nenhuma tela ativa depende do frontend legado.
- [ ] **LEG-002** Confirmar cobertura da matriz de paridade do editor.
- [ ] **LEG-003** Criar tag ou release de referência anterior à remoção.
- [ ] **LEG-004** Remover o editor legado do ponto de entrada do usuário.
- [ ] **LEG-005** Excluir arquivos legados do pacote de distribuição.
- [ ] **LEG-006** Remover adaptadores temporários não utilizados.
- [ ] **LEG-007** Manter histórico acessível pelo Git, sem duplicação permanente no produto.
- [ ] **LEG-008** Executar testes completos após a limpeza.

### Critério de aceite

- O frontend QML opera sozinho nos fluxos do usuário.
- A remoção não altera o renderer nem os arquivos produzidos.
- O instalador não leva telas ou recursos legados desnecessários.

---

## 18. Matriz mínima de regressão funcional

Esta matriz deve ser executada após mudanças visuais amplas e antes de cada gate importante.

### Modelos

- [ ] Criar modelo.
- [ ] Duplicar modelo.
- [ ] Renomear modelo.
- [ ] Remover modelo com confirmação.
- [ ] Importar modelos.
- [ ] Exportar modelos com assets.
- [ ] Resolver conflito por substituição e renomeação.

### Editor

- [ ] Abrir e fechar sem alteração.
- [ ] Sair com alteração não salva.
- [ ] Adicionar cada tipo de elemento.
- [ ] Selecionar e multisselecionar.
- [ ] Mover, redimensionar e rotacionar.
- [ ] Testar proporção bloqueada e livre.
- [ ] Testar snap em guias e bordas.
- [ ] Criar, mover, bloquear e limpar guias.
- [ ] Reordenar, ocultar, bloquear e renomear camadas.
- [ ] Desfazer e refazer ações variadas.
- [ ] Salvar, fechar e reabrir.
- [ ] Testar fonte ausente.
- [ ] Testar texto multilinha e formatado.

### Planilha

- [ ] Colar dados TSV simples.
- [ ] Colar do Google Sheets.
- [ ] Colar do Excel.
- [ ] Colar do LibreOffice.
- [ ] Preservar negrito, itálico e sublinhado.
- [ ] Alterar quantidade e assinatura.
- [ ] Navegar e editar por teclado.
- [ ] Testar tabela grande.

### Geração

- [ ] Gerar PNG individual.
- [ ] Gerar PDF individual.
- [ ] Gerar PDF único multipágina.
- [ ] Gerar PDF com links.
- [ ] Gerar com imposição.
- [ ] Verificar orientação, margens e marcas de corte.
- [ ] Testar cancelamento e erro durante geração.
- [ ] Verificar nomes e ordem dos arquivos.

### Plataforma e interface

- [ ] Tema claro.
- [ ] Tema escuro.
- [ ] DPI/escala diferentes.
- [ ] Teclado PT-BR e acentos.
- [ ] Caminhos e nomes longos.
- [ ] Windows.
- [ ] macOS.
- [ ] Linux.

---

## 19. Fase 9 — Preparação final para distribuição

**Objetivo:** transformar a versão modernizada em um produto instalável e operacionalmente sustentável.

### Licenças e documentação

- [ ] **DST-001** Definir licença do código próprio do C.O.M.S.O.C.
- [ ] **DST-002** Criar arquivo de avisos e licenças de terceiros.
- [ ] **DST-003** Documentar PySide6/Qt sob LGPLv3 e direitos do usuário.
- [ ] **DST-004** Confirmar linkagem dinâmica e possibilidade prática de substituição/relink.
- [ ] **DST-005** Disponibilizar o código-fonte correspondente das bibliotecas LGPL ou instrução juridicamente adequada.
- [ ] **DST-006** Auditar módulos Qt e demais dependências realmente incluídos no pacote.
- [ ] **DST-007** Gerar inventário/SBOM das dependências.
- [ ] **DST-008** Revisar o pacote final com profissional jurídico quando a comercialização estiver próxima.

### Builds e instalação

- [ ] **DST-010** Automatizar build limpo para Windows.
- [ ] **DST-011** Automatizar build limpo para macOS.
- [ ] **DST-012** Automatizar build limpo para Linux.
- [ ] **DST-013** Verificar inclusão de plugins, estilos, fontes autorizadas e arquivos QML.
- [ ] **DST-014** Testar instalação, primeira execução e remoção.
- [ ] **DST-015** Testar em máquina sem ambiente Python de desenvolvimento.

### Confiança das plataformas

- [ ] **DST-020** Assinar os executáveis e instalador do Windows.
- [ ] **DST-021** Documentar expectativa inicial do SmartScreen.
- [ ] **DST-022** Assinar todos os componentes do pacote macOS.
- [ ] **DST-023** Ativar hardened runtime conforme necessário.
- [ ] **DST-024** Notarizar e anexar o ticket ao pacote macOS.
- [ ] **DST-025** Definir canais Linux sem dependência do Flathub.

### Operação

- [ ] **DST-030** Definir versionamento do aplicativo.
- [ ] **DST-031** Definir canal de publicação e download.
- [ ] **DST-032** Definir como o usuário verifica novas versões, mesmo sem atualização automática.
- [ ] **DST-033** Criar backup e recuperação de dados do usuário.
- [ ] **DST-034** Criar manual básico e fluxo de primeiro uso.
- [ ] **DST-035** Definir como erros e diagnósticos serão coletados com consentimento do usuário.

---

## 20. Riscos e respostas planejadas

| Risco | Probabilidade | Impacto | Resposta |
|---|---|---|---|
| A padronização QSS alterar layouts | Média | Médio | Aplicar por componente e executar smoke tests |
| O trabalho visual virar reescrita funcional | Média | Alto | Separar commits e registrar qualquer mudança de regra |
| QML concentrar lógica de negócio | Média | Alto | Expor APIs Python pequenas e revisar fronteiras |
| Novo editor divergir na geometria | Alta | Alto | Modelos controlados e testes combinados de interação |
| Texto QML divergir do renderer | Alta | Alto | Renderer Qt como autoridade e comparação de quebras |
| Planilha QML perder recursos de clipboard | Média | Alto | Reaproveitar parser atual e criar matriz de colagem |
| Mistura QML/Widgets causar problemas de foco | Média | Médio | Preferir janelas separadas e testar atalhos |
| Animações ou delegates reduzirem desempenho | Média | Médio | Medir frame time e evitar trabalho Python por frame |
| Build não incluir plugins QML | Média | Alto | Testar executável limpo desde a fundação QML |
| Modelos reais serem danificados durante comparação | Baixa | Alto | Sempre trabalhar com cópias controladas |
| Dependência visual de projeto AGPL | Baixa | Alto | Referência somente estética e registro de procedência |
| Escopo crescer sem controle | Alta | Alto | Usar este documento como gate e registrar novas demandas |

---

## 21. Definição de pronto para qualquer tarefa de interface

Uma tarefa só pode ser marcada como concluída quando:

- [ ] o resultado atende ao mockup ou decisão visual registrada;
- [ ] funciona nos temas claro e escuro, quando aplicável;
- [ ] possui estados hover, foco, pressionado e desabilitado, quando aplicável;
- [ ] não introduz estilo inline sem justificativa;
- [ ] foi verificada em mais de uma escala de interface, quando estrutural;
- [ ] preserva navegação por teclado e atalhos relevantes;
- [ ] não altera regras de negócio silenciosamente;
- [ ] executa os testes ou smoke tests proporcionais ao risco;
- [ ] não introduz dependência sem auditoria de licença;
- [ ] possui evidência registrada neste documento ou no commit correspondente;
- [ ] atualiza este plano no mesmo conjunto de mudanças.

---

## 22. Registro de progresso por fase

### Fase atual

**Fase 0 — Baseline e direção visual**

### Trabalho em andamento

Nenhum item iniciado.

### Última entrega aceita

Revisão orientada à simplicidade do protótipo visual isolado em `features/editor_qml/`, preservando apenas controles correspondentes a funções reais do editor. O experimento não altera o estado das fases funcionais e não representa paridade com o editor legado.

### Próximas três ações

1. Capturar e organizar screenshots da interface atual.
2. Inventariar visualmente todas as telas e estados.
3. Definir e aprovar a direção visual antes de alterar estilos.

### Bloqueios atuais

Nenhum.

---

## 23. Histórico de decisões e atualizações

### 6 de agosto de 2026 — Criação do plano

- Consolidado o objetivo de modernizar a aparência sem reescrever o motor de produção.
- Definido PySide6 como componente permanente e administrável sob LGPL.
- Retirados Tauri e Electron do plano atual.
- Definida padronização completa de Qt Widgets como primeira entrega.
- Definida adoção gradual de QML, começando por fundação e telas de menor risco.
- Definida convivência temporária entre editor legado e novo editor QML.
- Registrado RapidRAW apenas como referência estética, sem uso de código-fonte.

### 6 de agosto de 2026 — Protótipo visual isolado do editor QML

- Criado o diretório `features/editor_qml/`, ao lado do editor legado e sem conexão com o aplicativo principal.
- Criada uma aplicação QML executável por `python features/editor_qml/main.py`.
- Criada uma proposta visual com barra principal, trilho de ferramentas, painel de inserção, canvas, documento demonstrativo, inspetor, camadas e barra de status.
- Criados tokens de tema e componentes QML reutilizáveis para botões, campos, seções e camadas.
- Adicionados modos de verificação de carregamento e captura de screenshot.
- Confirmado que o protótipo é apenas uma exploração de design: nenhuma tarefa das fases 5, 6 ou 7 foi marcada como concluída.
- O protótipo deverá servir como material para a Fase 0, podendo ser alterado ou descartado após a definição formal da identidade visual.

### 6 de agosto de 2026 — Rebranding profissional da exploração do editor

- A primeira composição, ainda próxima da organização do editor legado, foi substituída por uma direção visual independente chamada provisoriamente de “COMSOC Studio”.
- Adotada arquitetura de estação criativa com application bar, documentos em abas, opções contextuais, toolbox vertical compacto, canvas dominante com réguas e guias, inspector, camadas, rail de painéis e status de precisão.
- Removido da proposta o painel lateral largo de inserção; criação de objetos passou para ferramentas compactas e propriedades da seleção passaram para contexto superior e dock direito.
- Acrescentados affordances visuais para painéis recolhíveis, móveis e desacopláveis, sem implementar comportamento de backend nesta etapa.
- Criado conjunto de ícones vetoriais code-native em QML e refinados tokens de cor para uma identidade escura neutra com acento violeta e guias ciano.
- Preservados apenas conceitos úteis do produto atual, como campos variáveis, documento multipropósito, camadas e precisão geométrica; sua distribuição visual não ficou vinculada ao layout legado.
- A proposta foi carregada em modo offscreen e teve screenshot inspecionada visualmente em 1500 × 930.
- Esta entrega continua sendo exploração da Fase 0: não conclui integração, paridade funcional nem qualquer item da migração do editor.

### 6 de agosto de 2026 — Revisão de simplicidade orientada ao COMSOC

- Corrigida a direção do protótipo: acabamento profissional deixou de ser associado à quantidade de controles e passou a priorizar baixa carga cognitiva e correspondência com as funções reais do produto.
- Removidos menu tradicional, busca de comandos, seletor de workspace, exportação, organização genérica, documentos fictícios, toolbox vetorial, rail de painéis e barra flutuante de ações vagas.
- Mantidas somente as ações de criação existentes no editor: texto, imagem, assinatura, fundo e guias.
- Camadas retornaram ao painel esquerdo aberto, junto das ações de criação, com largura ajustável por `SplitView` e sem implementar docking livre.
- O painel direito passou a ser um inspector contextual único, com conteúdo, tipografia e comportamento do texto selecionado; transformação e alinhamento de objetos não são mais duplicados nele.
- Corrigidas as margens internas das propriedades para 14 px simétricos, alinhando títulos, campos e conteúdo sem contato com a borda esquerda.
- A barra superior foi reduzida a posição, dimensões em milímetros, proporção, rotação, opacidade e um único comando de alinhamento.
- A navegação passou a mostrar apenas `Página 1`, sem botão para adicionar páginas enquanto o schema multipágina não existir.
- A proposta revisada foi carregada em modo offscreen e inspecionada visualmente em 1500 × 930.
- Nenhuma integração com backend, renderer, persistência ou editor legado foi realizada.

---

## 24. Notas futuras

Usar esta seção para ideias ainda não aprovadas. Itens daqui não fazem parte do escopo até serem promovidos a uma fase e receberem identificador próprio.

- Avaliar se o frontend Widgets modernizado já é suficiente para a primeira distribuição pública.
- Avaliar FluentWinUI3, Material, Universal e estilo QML próprio por meio da galeria de componentes.
- Avaliar preview canônico produzido pelo renderer para reduzir divergência tipográfica no editor QML.
- Avaliar testes automatizados de screenshot e comparação perceptual quando a identidade visual estiver estável.
