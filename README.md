# C.O.M.S.O.C.

## Construtor Otimizado de Material Social Oficial e Cerimonial

**Automated Graphical Engine for Institutional Communication, Ceremonial Documentation and Data-Driven Visual Standardization.**

O **C.O.M.S.O.C.** é um sistema de automação gráfica desenvolvido para criar, padronizar e gerar em escala materiais visuais e documentos institucionais personalizados, como cartões comemorativos, diplomas, prismas de mesa, etiquetas, identificadores, crachás, bolachas de identificação e outros itens de uso cotidiano em seções de Comunicação Social, cerimonial, administração e apoio institucional.

O projeto nasceu a partir de uma demanda real de trabalho: reduzir o tempo gasto na produção manual de materiais repetitivos, diminuir erros humanos, mitigar retrabalho, economizar insumos e permitir que usuários sem formação em design gráfico consigam produzir documentos padronizados com qualidade profissional.

> **Resumo estratégico:** o C.O.M.S.O.C. transforma modelos visuais em um fluxo de produção orientado por dados, permitindo que uma única planilha alimente centenas de documentos personalizados em poucos segundos.

---

## 1. Visão geral

Em muitos ambientes institucionais, a produção de documentos visuais personalizados ainda depende de processos manuais em softwares genéricos de edição gráfica. Mesmo quando há modelos prontos e planilhas organizadas, cada item precisa ser editado, conferido, exportado e, muitas vezes, corrigido manualmente.

Esse fluxo gera quatro gargalos principais:

1. **Baixa escalabilidade:** a produção de dezenas ou centenas de itens exige muitas horas de trabalho repetitivo.
2. **Risco de erro humano:** nomes, cargos, datas, graduações e textos variáveis podem ser digitados ou copiados incorretamente.
3. **Retrabalho e desperdício:** erros percebidos somente após exportação ou impressão geram perda de tempo, papel, toner e material gráfico.
4. **Curva de aprendizagem longa:** o domínio de ferramentas de design pode levar meses, especialmente em ambientes com alta rotatividade de pessoal.

O C.O.M.S.O.C. foi projetado para resolver esse problema de forma sistêmica, combinando **editor visual**, **modelos reutilizáveis**, **variáveis dinâmicas**, **planilha integrada**, **imposição gráfica**, **exportação em lote** e **processamento multithread**.

---

## 2. Problema que o projeto resolve

### 2.1 Produção manual lenta e sujeita a falhas

No fluxo tradicional, um operador precisa abrir o modelo, substituir manualmente cada informação, conferir, ajustar alinhamentos, exportar o arquivo e repetir o processo para cada pessoa ou item. Um profissional treinado pode levar de **1 a 2 minutos por item**, ainda com risco de erro de digitação, desalinhamento ou esquecimento de atualização de algum campo.

Em cenários com 100, 200 ou 500 itens, esse processo deixa de ser apenas uma tarefa de design e passa a ser um gargalo administrativo.

### 2.2 Curva de aprendizagem incompatível com a rotatividade

Em organizações com troca frequente de pessoal, o conhecimento operacional de design costuma ser perdido periodicamente. Um militar ou servidor pode levar meses para atingir boa produtividade em ferramentas livres ou comerciais. Quando se torna eficiente, muitas vezes já está próximo de ser transferido, licenciado ou substituído.

O C.O.M.S.O.C. reduz essa dependência de especialistas: com modelos previamente preparados e uma planilha organizada, um novo operador pode ser treinado em poucos minutos para gerar documentos personalizados em escala.

### 2.3 Falta de padronização institucional

Quando cada unidade produz seus próprios materiais com os recursos humanos e técnicos disponíveis localmente, a qualidade visual e documental tende a variar. O C.O.M.S.O.C. introduz um fluxo de **padronização por modelos exportáveis**, permitindo que um órgão central crie modelos oficiais e os distribua para unidades subordinadas, mantendo identidade visual, qualidade e consistência documental.

---

## 3. Solução proposta

O C.O.M.S.O.C. é uma solução desktop, leve e multiplataforma, construída em Python, capaz de unir criação visual e processamento de dados em um único ambiente de trabalho.

Com ele, o usuário pode:

- criar e armazenar modelos gráficos personalizados;
- inserir textos, imagens, assinaturas, fundos e elementos variáveis;
- usar placeholders como `{Nome}`, `{Cargo}`, `{Graduação}`, `{Data}` ou qualquer outra variável necessária;
- colar dados diretamente de planilhas externas;
- gerar automaticamente uma versão personalizada do modelo para cada linha da tabela;
- exportar os resultados em PNG ou PDF;
- montar múltiplos itens em folhas A4/A3 ou qualquer tamanho personalizado com marcas de corte e sangria;
- reutilizar, importar e distribuir modelos entre diferentes usuários ou unidades.

---

## 4. Indicadores de impacto

Os números abaixo representam metas e resultados observados em testes iniciais do projeto. Eles devem ser refinados com medições formais, logs de execução e relatórios comparativos durante a validação institucional.

| Indicador | Fluxo tradicional | C.O.M.S.O.C. |
|---|---:|---:|
| Tempo médio por item | 1 a 2 minutos por item, mesmo após prática e repetição operacional | até ~1,5 segundo por item em máquina antiga testada; em equipamento atual, como processadores de 6 núcleos, o processamento atinge escala de centésimos de segundo por item, com 100 cartões gerados em aproximadamente 10,4 segundos |
| Produção em lote | Manual, item por item | Centenas de arquivos em menos de 1 minuto, conforme tamanho do modelo |
| Treinamento operacional | Semanas ou meses de prática | Menos de 30 minutos com modelos prontos e planilha organizada |
| Risco de erro de digitação | Alto, mesmo quando os dados da planilha estão corretos, devido à edição manual repetitiva | Eliminado na etapa de geração, desde que os dados tabulares de origem estejam corretos |
| Retrabalho | Frequente em grandes lotes | Mitigado por automação, pré-visualização e padronização |
| Requisitos de hardware | Normalmente demanda computadores mais recentes, com maior capacidade de processamento e memória RAM, para uso fluido de softwares gráficos profissionais | Otimizado para computadores modestos e legados, ampliando a viabilidade de uso em unidades com infraestrutura limitada |
| Padronização entre unidades | Variável conforme operador local e meios disponíveis | Reforçada por modelos exportáveis e reutilizáveis, com execução viável em equipamentos legados |

### Teste em hardware legado

Em testes em um computador com **Windows 10, 6 GB de RAM e processador dual-core de 2009**, o sistema manteve viabilidade operacional. Mesmo com desempenho inferior ao de máquinas modernas, o software foi capaz de gerar cartões em aproximadamente **1,5 segundo por item**, evidenciando potencial de uso em ambientes com parque computacional antigo.

---

## 5. Funcionalidades principais

### 5.1 Editor visual dinâmico

O editor permite construir modelos de forma livre, posicionando elementos visuais em uma área de trabalho gráfica.

Recursos previstos ou implementados:

- inserção de textos, imagens, fundos e assinaturas;
- movimentação, redimensionamento e rotação de elementos;
- sistema de camadas com hierarquia visual;
- ocultação, bloqueio e renomeação de objetos;
- guias e magnetismo para alinhamento preciso;
- histórico de ações com suporte a desfazer/refazer;
- controle visual mais seguro para evitar alterações acidentais em modelos complexos.

### 5.2 Motor de variáveis e placeholders

O sistema reconhece campos dinâmicos que podem ser inseridos livremente pelo usuário ao colocar o termo entre chaves, como:

```text
{Nome}
{Cargo}
{Posto_Graduacao}
{Data}
{Pelotao}
```

Essas variáveis são convertidas em colunas de dados, permitindo que cada linha da tabela gere uma versão personalizada do documento.

Benefícios:

- elimina digitação repetitiva;
- reduz divergência entre planilha e arte final;
- permite criar modelos genéricos e reaproveitáveis;
- facilita a conferência antes da geração final;
- permite ocultar campos vazios para evitar lixo visual no documento.

### 5.3 Texto rico limpo

O editor de texto foi pensado para aceitar conteúdo formatado sem carregar sujeiras visuais vindas da área de transferência. A proposta é preservar apenas informações úteis, como:

- negrito;
- itálico;
- alinhamento;
- recuo de parágrafo;
- espaçamento/entrelinha;
- estrutura textual necessária para diplomas, certificados e mensagens formais.

### 5.4 Planilha integrada

O C.O.M.S.O.C. trabalha com dados tabulares, permitindo colagem direta de planilhas externas e associação automática com as variáveis do modelo.

Recursos de controle por linha:

- quantidade de cópias por registro;
- ativação ou desativação de assinatura digital;
- campos personalizados;
- uso de imagens, logotipos ou QR codes individualizados;
- geração de nomes de arquivos com base em variáveis.

### 5.5 Imposição gráfica e preparação para impressão

O motor de imposição gráfica calcula automaticamente como distribuir múltiplos itens menores em uma folha. O usuário define o tamanho da folha, pode ser A3, A4 ou qualquer valor personalizado.

Aplicações:

- cartões múltiplos por página;
- prismas de mesa;
- etiquetas;
- bolachas de identificação;
- crachás;
- identificadores de armário;
- materiais de cerimônia.

Recursos:

- agrupamento automático por folha;
- marcas de corte;
- margens de segurança (sangria);
- melhor aproveitamento de papel;
- redução de desperdício em impressão.

### 5.6 Exportação híbrida

O sistema pode gerar arquivos de saída em diferentes formatos conforme a finalidade:

- **PNG:** ideal para envio por WhatsApp, e-mail, redes internas ou publicação digital.
- **PDF único e multipágina:** indicado para impressão, arquivamento, envio formal e produção gráfica. O sistema permite consolidar centenas de cartões, diplomas ou documentos personalizados em um único arquivo PDF, distribuídos em múltiplas páginas. Quando configurado para impressão em lote, o C.O.M.S.O.C. pode organizar vários itens por página, já com marcas de corte, facilitando o processo de produção física. Dessa forma, o usuário precisa apenas abrir um único documento e enviar todas as páginas para impressão, evitando o trabalho manual de abrir e imprimir arquivo por arquivo.
- **PDF interativo com hiperlinks vivos:** quando aplicável, elementos visuais do layout podem receber links clicáveis reais por meio da integração com PyMuPDF. Esse recurso permite criar convites digitais, cartões institucionais e documentos interativos com botões para confirmação de presença via Google Forms, WhatsApp ou e-mail, além de mapas ou ícones de localização que direcionam o destinatário ao Google Maps ou a aplicativos de GPS para traçar a rota até o local do evento com apenas um clique.

### 5.7 Processamento em lote com multithreading

A geração em massa pode ser distribuída em múltiplas threads, aproveitando melhor os núcleos do processador e reduzindo o tempo total de processamento.

Esse recurso é essencial para situações em que centenas de documentos precisam ser entregues rapidamente, especialmente em datas comemorativas, formaturas, solenidades, campanhas internas e eventos institucionais.

### 5.8 Importação e exportação de modelos

Uma das capacidades estratégicas do C.O.M.S.O.C. é permitir que modelos sejam empacotados, exportados e compartilhados.

Isso viabiliza um fluxo de padronização institucional:

1. um órgão central cria um modelo oficial;
2. o modelo é exportado;
3. unidades subordinadas importam o modelo;
4. cada unidade preenche apenas a planilha com seus próprios dados;
5. o resultado mantém identidade visual e padrão documental comum.

Esse fluxo reduz discrepâncias entre unidades, facilita atualização de identidade visual e cria uma base reutilizável de modelos oficiais.

---

## 6. Casos de uso

### 6.1 Cartões institucionais

- aniversários;
- promoção na carreira;
- boas-vindas;
- despedidas;
- agradecimentos;
- condolências;
- datas comemorativas;
- dia da arma, quadro ou serviço;
- mensagens do comando.

### 6.2 Diplomas e certificados

- diploma de honra ao mérito;
- melhor aptidão física;
- melhor atirador combatente;
- amigo do regimento;
- conclusão de curso;
- participação em instruções ou estágios;
- reconhecimento por apoio institucional;
- certificados de agradecimento.

### 6.3 Cerimonial e eventos

- prismas de mesa para autoridades;
- identificadores de convidados;
- bolachas de identificação;
- crachás;
- convites nominais;
- cartões interativos com links;

### 6.4 Administração e rotina de unidade

- etiquetas de armário;
- identificação de material;
- identificação de mochilas, caixas e equipamentos;
- etiquetas para operações e exercícios;
- identificação funcional ou interna da Organização Militar;
- modelos repetitivos de comunicação visual.

### 6.5 Expansão para outras instituições

Embora o projeto tenha origem em uma demanda ligada à Comunicação Social e ao cerimonial no contexto militar, sua arquitetura é aplicável a diversos ambientes:

- Exército Brasileiro;
- Marinha do Brasil;
- Força Aérea Brasileira;
- forças auxiliares;
- escolas;
- universidades;
- prefeituras;
- órgãos públicos;
- organizações privadas com produção documental em escala.

---

## 7. Arquitetura técnica

### 7.1 Base tecnológica

- **Linguagem:** Python
- **Tipo de aplicação:** desktop
- **Modelo de operação:** local/offline-first
- **Plataformas-alvo:** Windows, Linux e macOS
- **Processamento:** geração em lote com suporte a multithreading
- **PDF:** exportação e injeção de hiperlinks por PyMuPDF, quando aplicável

### 7.2 Componentes conceituais

```text
+-----------------------------+
| Editor Visual / Canvas      |
| Camadas, guias, textos,     |
| imagens e elementos         |
+-------------+---------------+
              |
              v
+-----------------------------+
| Motor de Variáveis          |
| Placeholders -> colunas     |
| Dados tabulares -> modelo   |
+-------------+---------------+
              |
              v
+-----------------------------+
| Planilha Integrada          |
| Linhas, campos, quantidade, |
| assinatura e imagens        |
+-------------+---------------+
              |
              v
+-----------------------------+
| Motor de Renderização       |
| Geração individual ou lote  |
| PNG / PDF                   |
+-------------+---------------+
              |
              v
+-----------------------------+
| Print Prep / Imposição      |
| personalizada, sangria,     |
| marcas de corte e           |
| orte e aproveitamento       |
+-----------------------------+
```

---

## 8. Instalação e execução

> Esta seção deve ser ajustada conforme a estrutura final do repositório e o nome real do arquivo principal da aplicação.

### 8.1 Clonar o repositório

```bash
git clone https://github.com/LeonardoJoordan/projeto_comsoc
cd COMSOC
```

### 8.2 Criar ambiente virtual

#### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 8.3 Instalar dependências

```bash
pip install -r requirements.txt
```

### 8.4 Executar

```bash
python main.py
```

Caso o projeto utilize outro arquivo de entrada, substitua `main.py` pelo arquivo correto.

---

## 9. Fluxo básico de uso

1. Criar ou abrir um modelo visual.
2. Inserir textos, imagens, fundo, assinaturas e demais elementos.
3. Adicionar placeholders nos textos, como `{Nome}` ou `{Cargo}`.
4. Colar os dados vindos de uma planilha.
5. Conferir a pré-visualização dos registros.
6. Ajustar quantidade, assinatura e campos especiais por linha.
7. Escolher o formato de exportação: PNG, PDF individual ou PDF único.
8. Configurar imposição gráfica, caso o material vá para impressão.
9. Gerar os arquivos finais.
10. Arquivar, imprimir ou distribuir digitalmente.

---

## 10. Impacto institucional esperado

O C.O.M.S.O.C. foi concebido para atuar como uma ferramenta de **transformação digital aplicada à produção documental e visual institucional**.

### 10.1 Eficiência administrativa

Ao automatizar tarefas repetitivas, o sistema libera o operador para atividades de maior valor, como revisão de conteúdo, planejamento de comunicação, padronização institucional e atendimento a demandas urgentes.

### 10.2 Economia de recursos

A redução de erros e retrabalho contribui para menor desperdício de:

- papel;
- toner;
- tempo de trabalho;
- material gráfico especial;
- horas de conferência e correção.

### 10.3 Mitigação da rotatividade

O sistema reduz a dependência de um operador altamente treinado. Com modelos prontos, a produção pode ser transferida rapidamente para outro usuário, preservando continuidade operacional mesmo com mudanças de efetivo.

### 10.4 Padronização em larga escala

A capacidade de exportar e distribuir modelos cria uma base técnica para padronização visual entre múltiplas unidades, sem exigir que cada localidade recrie documentos do zero.

### 10.5 Inclusão tecnológica

A compatibilidade com máquinas antigas amplia a viabilidade de adoção em unidades com recursos computacionais limitados, evitando que a padronização dependa de computadores de alto desempenho ou licenças comerciais caras.

### 10.6 Segurança da informação e soberania operacional

Por operar localmente e permitir fluxo offline, o C.O.M.S.O.C. reduz a necessidade de envio de dados sensíveis para plataformas externas de design, preservando o controle institucional sobre nomes, cargos, imagens, documentos e demais informações internas.

O sistema também foi concebido para minimizar a retenção de dados sensíveis. Os dados oriundos de planilhas são utilizados apenas durante a sessão de trabalho, para alimentar os modelos e gerar os arquivos finais. Ao encerrar o aplicativo, essas informações são descartadas, não permanecendo armazenadas em banco de dados interno ou em repositório próprio do programa. Isso reduz riscos de exposição indevida e reforça a soberania operacional da instituição sobre suas informações.

---