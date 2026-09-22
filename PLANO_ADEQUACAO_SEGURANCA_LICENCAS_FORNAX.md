# FORNAX Forge — plano de adequação para publicação

Data: 21/09/2026.

Base: [relatório de revisão](RELATORIO_REVISAO_SEGURANCA_LEGADO_LICENCAS.md). Os códigos S, L e J abaixo correspondem aos achados desse relatório.

## Objetivo e limites

Resolver os riscos demonstrados, acertar as condições de distribuição e produzir releases verificáveis. Priorizar mudanças pequenas nos pontos compartilhados do programa, sem reconstruir a arquitetura ou acrescentar funcionalidades.

O aplicativo continuará offline, com atualização manual por releases. A proteção de assinaturas continuará opcional. Não serão acrescentados login, telemetria, bloqueio automático por inatividade ou restrições à geração de documentos assinados.

Este documento é planejamento; não executa as correções. Cada checkpoint deverá registrar arquivos alterados, validação realizada e pendências. Uma etapa não será considerada concluída apenas porque seus testes unitários passaram quando depender de verificação do aplicativo instalado.

## Etapa 1 — Corrigir os dois riscos de maior prioridade

**Situação: concluída em 21/09/2026.** Foram adicionadas barreiras no contrato do modelo e no carregamento de recursos do Qt, limites de canvas, geometria e imposição, além de orçamento de memória para workers. A suíte completa terminou com 441 testes aprovados, 1 pulado, 1 aviso e 12 subtestes aprovados.

### 1.1 — Impedir recursos externos nas caixas de texto — S1

**Solução:** centralizar a criação de documentos de texto com uma política de recursos que negue carregamentos externos. Caixas de texto permanecem textuais; imagens continuam sendo inseridas pelas camadas próprias de imagem.

- Identificar todos os caminhos que criam ou recebem HTML no editor, prévia e geração, incluindo colagem e importação.
- Preservar a formatação suportada, como fonte, tamanho, negrito, itálico, sublinhado e parágrafos.
- Remover recursos não suportados do HTML na entrada, com aviso quando houver descarte de conteúdo; bloquear também o carregamento em `loadResource`, sem depender apenas da limpeza de marcação.
- Reutilizar essa implementação nos três fluxos, evitando uma proteção exclusiva da prévia.

**Verificação:** transformar o ensaio do relatório em teste de regressão. Cobrir referências absolutas, relativas, `file://`, UNC e CSS; verificar que não carregam recursos externos. Conferir textos ricos, placeholders e trechos opcionais existentes.

**Conclusão esperada:** abrir um modelo não permite que seu HTML busque imagens externas ao conteúdo autorizado. Validar também no Windows os caminhos específicos desse sistema.

### 1.2 — Limitar dimensões antes de alocar imagens — S2

**Solução:** uma validação compartilhada para dimensões do documento e imagens de saída, aplicada antes de criar buffers do Qt.

- Levantar os maiores tamanhos e resoluções legítimos já suportados; documentar limites por lado e quantidade total de pixels.
- Usar os limites de assets existentes como referência, sem presumir que o mesmo teto seja seguro para vários buffers simultâneos.
- Validar números finitos, positivos e inteiros nos pontos que exigem pixels inteiros. Validar também escala, geometria e dimensões resultantes da imposição.
- Estimar o consumo dos buffers por trabalho e reduzir a concorrência quando necessário. Recusar com mensagem clara quando nem um trabalho couber no orçamento definido.
- Aplicar a mesma regra ao abrir, editar dimensões e gerar; preservar o arquivo original em caso de rejeição.

**Verificação:** dimensões extremas devem falhar antes de qualquer alocação; testar valores nos limites e formatos legítimos, incluindo frente e verso e imposição. Não provocar esgotamento real de memória nos testes.

**Conclusão esperada:** um modelo pequeno em disco não consegue solicitar uma imagem desproporcional sem validação prévia.

## Etapa 2 — Confinar leitura e gravação aos destinos corretos

**Situação: concluída em 21/09/2026.** A nomenclatura foi unificada e passou a tratar caminhos, nomes reservados, tamanho, colisões sem distinção de caixa e arquivos preexistentes. Toda gravação dos workers confirma o confinamento no diretório autorizado. Imagens variáveis agora são resolvidas pelo destino real e recusam links que saiam da pasta selecionada. A suíte completa terminou com 456 testes aprovados, 1 pulado, 1 aviso e 12 subtestes aprovados.

### 2.1 — Unificar a construção dos nomes de saída — S3

**Solução:** aproveitar a sanitização já existente no fluxo individual e utilizá-la também na imposição. Antes de gravar, confirmar que o caminho final está dentro da pasta do trabalho.

- Tratar separadores, caminhos absolutos, `..`, nomes reservados do Windows e comprimento excessivo.
- Resolver colisões com um sufixo numérico, preservando arquivos existentes e considerando sistemas sem distinção entre maiúsculas e minúsculas.
- Manter a nomenclatura habitual para entradas válidas e a organização por forja.

**Verificação:** padrões problemáticos não escapam da pasta nem sobrescrevem arquivos externos; geração individual e por folha continuam produzindo nomes corretos.

**Conclusão esperada:** todos os modos compartilham a mesma regra de nome e destino seguro.

### 2.2 — Verificar o destino real das imagens variáveis — S4

**Solução:** resolver a pasta escolhida e o arquivo candidato para seus caminhos reais, exigindo que o arquivo permaneça dentro dessa pasta. Aplicar a regra também à busca automática por extensão.

- Permitir arquivos comuns, subpastas suportadas e links cujo destino continue dentro da raiz autorizada.
- Recusar links que apontem para fora, com a mensagem normal de imagem inválida.
- Verificar novamente no ponto de abertura, reduzindo a distância entre validação e leitura. Não apresentar essa checagem como eliminação de toda corrida possível no sistema de arquivos.

**Verificação:** arquivo normal e link interno funcionam; link externo é recusado. Testar links/junctions Windows quando disponíveis e registrar eventual limitação do ambiente.

**Conclusão esperada:** selecionar uma pasta não autoriza buscar imagens em outras pastas por atalhos indiretos.

## Etapa 3 — Reduzir resíduos e explicar o funcionamento offline

**Situação: concluída em 21/09/2026.** Logs operacionais e de falha agora possuem rotação limitada; a persistência omite caminhos, nomes de saídas e detalhes multilinha, mantendo a informação completa apenas na interface. Importação, exportação e geração intermediária usam a área temporária exclusiva do aplicativo, limpa ao terminar e na próxima inicialização após falha. O mapa de dados e seus limites foram documentados em `docs/PRIVACIDADE_E_ARMAZENAMENTO.md`. A suíte completa terminou com 460 testes aprovados, 1 pulado, 1 aviso e 12 subtestes aprovados.

### 3.1 — Limitar e higienizar os logs — S5

**Solução:** adotar rotação simples dos logs em disco e separar o que precisa aparecer na interface do que precisa ser persistido.

- Proposta inicial de retenção: até três arquivos de 1 MiB para o log operacional, com limite equivalente para registros de falha. Confirmar se atende ao diagnóstico antes de fechar o checkpoint.
- Evitar dados de células, nomes completos de arquivos gerados, conteúdo do modelo e credenciais nos logs persistentes. Preferir número do item, operação e categoria do erro.
- Preservar detalhes úteis na interface quando necessários ao usuário; revisar mensagens de exceção antes de gravá-las.
- Definir claramente se “limpar log” limpa somente a visualização ou também os arquivos; não manter uma indicação ambígua.

**Verificação:** geração com dados fictícios identificáveis e erros controlados não persiste esses dados indevidamente; rotação respeita os limites.

**Conclusão esperada:** diagnóstico continua útil, com retenção limitada e exposição reduzida.

### 3.2 — Documentar persistência e revisar temporários — S5

**Solução:** criar uma documentação curta de privacidade e armazenamento baseada no mapa do relatório.

- Explicar onde ficam modelos, configurações, backups, recuperação, caches, logs e arquivos gerados.
- Distinguir funcionamento offline de ausência de armazenamento: os arquivos locais e resultados existem e podem conter dados pessoais.
- Revisar limpeza dos temporários pertencentes ao aplicativo, incluindo falha e cancelamento; não apagar saídas, backups ou modelos do usuário para “limpar resíduos”.
- Confirmar que conteúdo protegido não reaparece em cache ou temporário sem proteção. Não prometer apagamento seguro de disco ou memória.

**Verificação:** executar salvar, desbloquear, bloquear, exportar, cancelar e recuperar usando dados fictícios; conferir os diretórios envolvidos.

**Conclusão esperada:** o usuário sabe o que fica no computador e os fluxos protegidos não deixam cópias indevidas nos caminhos examinados.

## Etapa 4 — Resolver licença, autoria e origem dos recursos

Esta etapa pode avançar em paralelo à sequência técnica, mas depende de duas informações do autor. Não escolher uma licença em seu nome nem presumir a origem de um ícone.

**Situação: concluída no escopo documental em 22/09/2026.** Autoria e GPL-3.0-only definidas, EULA contraditória retirada. O autor declarou concluída a substituição dos SVGs por recursos de Lucide, Google Material e Bootstrap Icons. Os textos oficiais ISC/MIT/Apache-2.0 foram preservados em `docs/licenses/`, com inventário individual em `docs/ASSET_PROVENANCE.md`. Os 11 arquivos sem identificação externa foram confirmados pelo autor como criações próprias no Inkscape; a origem dos 67 SVGs está registrada. A origem da marca foi esclarecida: imagem gerada com ChatGPT e editada pelo autor no Photoshop para arredondar as bordas e incluir a constelação ao fundo. O autor informou geração em 13 de setembro às 01:33, sem preservação do PSD; a declaração, os PNGs/ICO finais e seus hashes foram registrados como evidência disponível, com seus limites. Os termos de conteúdo da OpenAI foram consultados e referenciados no inventário. A ausência do PSD não é tratada como impedimento para este registro documental. A presença das licenças no pacote instalado será validada na Etapa 5. Não é necessário redesenhar ícones cuja origem e licença estejam confirmadas.

### 4.1 — Unificar a licença do FORNAX — J1 e J5

**Decisão:** adotar a GNU General Public License versão 3 exclusivamente (`GPL-3.0-only`) para o código e a documentação próprios do projeto. O nome e o logotipo são tratados separadamente pela política de marca.

Depois da decisão:

- Criar `LICENSE` e registrar a autoria do código próprio em `AUTHORS.md`, com o nome aprovado pelo autor.
- Substituir a EULA contraditória e alinhar instalador, README e tela Sobre.
- Criar uma orientação de uso institucional: permissões de instalação e redistribuição, condições aplicáveis, ausência de vínculo ou endosso institucional e distinção entre licença do programa e direitos sobre modelos, dados e imagens.
- Preservar créditos e obrigações de terceiros. Não declarar autoria exclusiva das bibliotecas ou assets externos.

**Verificação:** nenhuma tela ou documento proíbe uma redistribuição que a licença escolhida permite. Conferir os termos exatos da licença antes da publicação.

**Conclusão esperada:** uma instituição consegue identificar o que pode instalar, copiar e distribuir. O registro de autoria e o histórico são evidências documentais, não substitutos de registro no INPI ou parecer jurídico.

### 4.2 — Registrar a origem dos ícones e fontes — J4

**Solução:** um inventário simples, agrupando arquivos quando compartilham origem, com autor, URL ou declaração de criação própria, licença e localização do texto de licença.

**Informação necessária:** o autor deverá fornecer a origem dos recursos sem comprovação no repositório. Metadados de edição não demonstram licença.

- Manter recursos com origem e permissão verificáveis.
- Substituir apenas os recursos cuja autorização não possa ser comprovada, por criação própria ou equivalente de licença conhecida.
- Incluir Inter/OFL e conferir também logo, PNG e ICO, sem redesenhar a interface por conveniência.

**Verificação:** cada recurso distribuído está coberto pelo inventário e pelos avisos necessários.

**Conclusão esperada:** não resta asset com origem desconhecida no pacote publicado.

## Etapa 5 — Adequar dependências e construir releases verificáveis

**Situação: implementação e validação local realizadas em 22/09/2026; aceite multiplataforma pendente.** Runtime sem Addons validado, locks com hashes, seleção explícita de conteúdo, standalone Linux compilado, avisos e fontes Qt/Rust arquivados, CI preparada e análises locais executadas. pypdf atualizado para 6.16.1 e parser SVG endurecido com defusedxml. Suíte: 472 aprovados, 1 ignorado, 1 aviso e 12 subtestes; quatro testes de empacotamento passaram após o ajuste final. Fontes/avisos finais por artefato, execução de CI no GitHub, distribuição instalada por plataforma e política de assinatura ainda exigem fechamento. Evidências e próximos checkpoints: [registro da etapa 5](history/ETAPA_5_DISTRIBUICAO_E_DEPENDENCIAS.md).

### 5.1 — Inventariar e reduzir o que realmente é distribuído — J3 e L4

**Solução:** gerar builds limpos e conferir seus componentes, em vez de usar apenas a lista do ambiente de desenvolvimento.

- Validar em ambiente limpo se o conjunto necessário de PySide6/Essentials/shiboken atende a todos os imports. Excluir Addons desnecessários somente após essa verificação.
- Inspecionar os artefatos para evitar módulos Qt não utilizados, especialmente componentes com condições de licença diferentes.
- Excluir testes, caches Python, documentos de planejamento, ambientes virtuais e resíduos antigos dos pacotes por uma lista explícita de conteúdo de distribuição.
- Registrar versões, licenças e dependências nativas efetivas por plataforma, incluindo OpenSSL, componentes Rust, fontes e runtimes redistribuídos.
- Separar ferramentas de build das bibliotecas incorporadas, verificando também as exceções e avisos do runtime Nuitka.

**Verificação:** o programa instalado funciona e o inventário corresponde ao conteúdo real de Windows, AppImage e Flatpak que forem publicados.

**Conclusão esperada:** distribuição menor, previsível e com inventário correto, sem remover funcionalidades necessárias.

### 5.2 — Entregar os textos e materiais exigidos pelas licenças — J2 e J3

**Solução:** manter uma pasta de avisos e textos integrais de terceiros e incluí-la de forma consistente em todos os empacotamentos.

- Corrigir o inventário atual com base nas versões efetivamente distribuídas.
- Para componentes que exigem fontes correspondentes, preparar junto ao release os fontes exatos, alterações e instruções pertinentes, conforme a licença aplicável. Não depender apenas de um link genérico para o upstream.
- Verificar as condições LGPL de substituição/recombinação das bibliotecas no empacotamento adotado e evitar termos próprios que proíbam os direitos exigidos pela licença.
- Conferir que a instalação entrega os materiais prometidos pela tela Sobre e pela documentação.

**Verificação:** checklist por componente e artefato, com caminho dos avisos, texto integral e fonte correspondente quando exigida; testar o procedimento pertinente de substituição das bibliotecas Qt.

**Conclusão esperada:** obrigações documentadas com evidência de cumprimento no pacote real. Usar PySide6 não significa, por si só, licenciar todo o FORNAX sob LGPL ou enviar seu código à Qt.

### 5.3 — Automatizar verificações de manutenção — S6

**Solução:** um fluxo de CI enxuto para testes, análise estática, dependências vulneráveis e segredos, executado no desenvolvimento e na publicação. Isso não acrescenta conexões ao aplicativo.

- Fixar dependências e ferramentas de build, registrar transitivas e hashes compatíveis com cada ambiente de distribuição.
- Rodar análise Python e scanner de dependências; tratar achados relevantes e registrar justificativas para falsos positivos, sem desativar regras indiscriminadamente.
- Verificar segredos também no histórico antes de qualquer publicação ou migração. Se houver segredo real, revogá-lo; apagar uma linha não basta.
- Gerar SBOM, checksums e registro de versão/commit por release. Assinar os artefatos ou manifestos conforme o mecanismo disponível, documentando como verificar e quem controla a chave.
- Criar `SECURITY.md` com canal de relato e política de suporte realista; verificar suporte do runtime Flatpak e demais bases de build.

**Verificação:** executar o fluxo e arquivar seus resultados. Checksums detectam alteração, mas não comprovam origem sozinhos; registrar claramente se e como o release foi assinado.

**Conclusão esperada:** cada release tem rastreabilidade de componentes e verificações repetíveis. Selos externos podem ser avaliados depois; não são requisito para resolver os achados.

## Etapa 6 — Atualizar documentação e validar a distribuição

**Situação: documentação e revisão local realizadas em 22/09/2026; aprovação dos pacotes nativos pendente.** Guias atualizados, referências legadas inventariadas e preservadas, empacotamento documental e momento do inventário macOS corrigidos. Suíte: 473 aprovados, 1 pulado, 1 aviso e 12 subtestes; IPC Linux executado à parte com 3 testes aprovados. Evidências e limites no [registro da etapa 6](history/ETAPA_6_DOCUMENTACAO_E_VALIDACAO.md).

### 6.1 — Corrigir documentação sem quebrar compatibilidade — L1, L2 e L3

**Solução:** atualizar instruções operacionais e preservar as referências antigas que ainda têm função de migração ou registro histórico.

- Ajustar menus, `.fornax`, importação em lote e orientações de frente e verso à interface atual.
- Substituir a antiga lista de pedidos de ícones pela documentação do conjunto realmente usado.
- Manter IDs e caminhos COMSOC necessários à migração e cobri-los com testes; L1 é um controle a preservar, não um defeito a eliminar.
- Manter documentos históricos identificados como históricos. Não apagar autoria ou decisões anteriores para esconder o nome antigo.
- Listar todos os URLs de repositório a trocar futuramente. Enquanto o novo repositório não existir, não inventar links nem alterar identidades de instalação que preservam atualizações.

**Verificação:** seguir as instruções como usuário e testar migração de configuração/modelo antigo com cópias fictícias.

**Conclusão esperada:** documentação atual coerente e compatibilidade preservada. A troca dos URLs fica explicitamente vinculada à futura criação do repositório.

### 6.2 — Revisão integrada dos instaladores e do aplicativo — S6, J2, J3, J5 e L4

**Solução:** uma rodada final sobre os artefatos efetivamente destinados à publicação.

- Executar a suíte completa e os novos testes de regressão; comparar falhas, pulos e avisos com a referência.
- Testar nativamente Windows e Linux: instalação, associação `.fornax`, ícone, abertura por duplo clique, IPC, migração, modelos protegidos e públicos, editor, prévia e geração.
- Conferir avisos/licenças incluídos, comportamento sem conexão e ausência de tentativas de rede iniciadas pelos fluxos normais do aplicativo. Separar ações explícitas de abrir links externos.
- Reexaminar caches e temporários após os fluxos protegidos, incluindo cancelamento e encerramento inesperado controlado.
- Registrar resultados, limitações e riscos residuais; não converter ausência de falha em promessa de “segurança absoluta” ou homologação governamental.

**Referência existente:** 423 testes passaram, 1 foi pulado e 12 subtestes passaram; houve 1 aviso. O IPC nativo ficou condicionado a `FORNAX_RUN_NATIVE_IPC=1`. O aviso precisa ser examinado, não apenas ocultado.

Comando usado no relatório:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest --import-mode=importlib -q tests features/editor --disable-warnings --maxfail=8
```

**Conclusão esperada:** evidências de funcionamento e conformidade dos pacotes publicados, com pendências visíveis e nenhuma regressão conhecida sem tratamento.

## Encerramento e futura separação do repositório

A criação do novo repositório FORNAX continua sendo o último passo, fora das correções imediatas. Após os checkpoints anteriores, preparar a migração com conteúdo selecionado, histórico de autoria preservado ou referenciado conforme a estratégia aprovada e varredura de segredos concluída. Não copiar indiscriminadamente a pasta de trabalho.

Nesse momento, atualizar os URLs inventariados em L3 e verificar novamente os links dos instaladores e da documentação. Pendências dependentes desse evento não devem aparecer como resolvidas antecipadamente.

## Cobertura dos achados

| Achado | Checkpoints | Tratamento |
|---|---|---|
| S1 | 1.1 | Bloqueio de recursos externos no texto |
| S2 | 1.2 | Limites de dimensão e orçamento de renderização |
| S3 | 2.1 | Nome seguro e contenção da saída |
| S4 | 2.2 | Contenção real de imagens variáveis |
| S5 | 3.1 e 3.2 | Logs, persistência e temporários |
| S6 | 5.3 e 6.2 | CI, evidências de release e testes nativos |
| L1 | 6.1 | Preservar compatibilidade já correta |
| L2 | 6.1 | Atualizar documentação operacional |
| L3 | 6.1 e encerramento | Inventariar agora; trocar URLs no novo repositório |
| L4 | 5.1, 6.2 e encerramento | Distribuir apenas conteúdo necessário |
| J1 | 4.1 | Escolher licença e eliminar contradições |
| J2 | 5.2 e 6.2 | Entregar avisos, textos e fontes exigidos |
| J3 | 5.1 e 5.2 | Inventário real e obrigações por componente |
| J4 | 4.2 | Comprovar origem ou substituir recursos |
| J5 | 4.1 e 6.2 | Documentar autoria, alcance e limites das conclusões |

**Próximo trabalho recomendado:** executar o checklist dos pacotes finais e fechar a correspondência de fontes/avisos por plataforma (5.2 e 6.2). A sequência de implementação e revisão local chegou à última etapa; isso não equivale a aprovar distribuição multiplataforma. Consultar os registros das [etapas 5](history/ETAPA_5_DISTRIBUICAO_E_DEPENDENCIAS.md) e [6](history/ETAPA_6_DOCUMENTACAO_E_VALIDACAO.md). A separação do repositório permanece posterior.
