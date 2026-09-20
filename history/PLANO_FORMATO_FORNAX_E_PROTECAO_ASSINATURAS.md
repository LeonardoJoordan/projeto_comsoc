# Formato .fornax e proteção de modelos e assinaturas

Data: 19/09/2026.
Atualizado em: 20/09/2026 — decisões de segurança aprovadas, proteção integral opcional e reorganização em quatro grandes etapas com checkpoints.
Status: Etapa 4 em andamento; revisões internas 4.1, 4.2 e 4.3 concluídas. Checkpoint 4.4 com revisão local Linux, correções e medições registradas; pacotes nativos e hardware modesto ainda pendentes. O checkpoint 3.11 continua pendente; a revisão especializada independente ainda não foi realizada.

## Objetivo e limites

Substituir a pasta de cada modelo por um `.fornax`, preservando modelos antigos e os resultados do editor, preview e geração. Proteger obrigatoriamente assinaturas e permitir proteção integral opcional, compartilhamento com senha independente e migração segura.

A proteção busca impedir leitura do conteúdo protegido sem senha. Não autentica documentos gerados, não identifica pessoas, não impede cópia de resultados autorizados e não protege contra comprometimento da máquina ou uso de uma sessão já desbloqueada. Não haverá token de instalação, login, servidor, assinatura digital dos resultados, bloqueio manual, bloqueio por tentativas ou miniaturas no explorador de arquivos nesta atualização.

Apenas elementos classificados como assinatura recebem a proteção obrigatória. Imagens comuns continuam imagens comuns, mesmo se visualmente iguais a uma assinatura. Não implementar comparação de imagens, detecção automática ou bloqueio por duplicidade de conteúdo. Documentar esse limite sem alegar proteção universal de representações de assinatura.

## Como executar este plano

- Executar um checkpoint por vez, na ordem das dependências, conferindo o código atual antes de alterar.
- Cada checkpoint tem objetivo, escopo e aceite verificável. Interface pronta não basta para concluir proteção ou migração.
- Registrar arquivos, comandos/testes, resultados e pendências no controle de execução. Não declarar testes não realizados como aprovados.
- Usar modelos sintéticos e cópias; nunca assinaturas reais nos testes/repositório.
- Preservar alterações do usuário. Manter mudanças revisáveis e um ponto de recuperação no controle de versão antes de intervenções de alto risco.
- Não refatorar renderização ou tabela sem necessidade comprovada desta atualização. O armazenamento se adapta aos contratos existentes.
- As escolhas abaixo aprovadas não precisam ser rediscutidas. A etapa 2 fecha detalhes técnicos verificáveis; novas decisões de produto devem ser explicitadas antes de implementadas.
- Não iniciar a etapa 3 antes do aceite da especificação da etapa 2. A etapa 4 revisa o conjunto; testes locais são obrigatórios já durante a implementação.

## Decisões de produto aprovadas

### Arquivo, biblioteca e abertura externa

- Um `.fornax` representa um modelo completo, inclusive frente e verso. A biblioteca guarda um arquivo por modelo.
- Exportação individual: `.fornax`. Exportação múltipla: ZIP contendo `.fornax`; o ZIP externo não precisa ser criptografado.
- Continuar lendo pastas e ZIPs antigos para preservar o trabalho dos testers; não garantir leitura do formato novo pelo programa piloto.
- Duplo clique: perguntar “Deseja adicionar este modelo à sua biblioteca?”. Sim incorpora; Não abre temporariamente para tabela, preview e geração.
- Modelos protegidos incorporados precisam do fluxo de desbloqueio e nova senha local antes de publicação. Cancelar não incorpora parcialmente.
- Uso temporário não altera o arquivo externo implicitamente nem persiste na biblioteca/seleção ao fechar. Resultados gerados permanecem. Salvar alterações exige destino explícito.
- Tratar aplicativo já aberto, editor ativo e alterações não salvas sem descartar trabalho.
- Associar extensão e ícone nos pacotes suportados de Windows, Linux e macOS. Miniaturas do explorador ficam fora do escopo.

### Três modos de proteção

| Modo | Acesso sem senha | Conteúdo protegido |
|---|---|---|
| Sem proteção | Completo; permitido apenas sem assinatura | Nenhum |
| Proteger assinaturas | Cópia independente sem assinaturas | Assets, camadas, configurações e relações necessárias às assinaturas |
| Proteger modelo inteiro | Nenhum conteúdo ou preview; desbloquear ou cancelar | Documento, assets, assinaturas, informações internas e miniaturas |

- Detectar assinaturas em todas as páginas, inclusive ocultas/desmarcadas.
- Ao adicionar assinatura em modelo ainda desprotegido, exigir senha no salvamento e oferecer proteção das assinaturas ou integral.
- Modelo sem assinatura pode receber proteção integral opcional.
- Modelo integralmente protegido que recebe assinatura mantém sua senha, sem segunda proteção/senha sobreposta.
- Reduzir/remover proteção exige desbloqueio. Com assinaturas, o mínimo permitido é proteger assinaturas.
- Remover a última assinatura não deve remover proteção integral automaticamente.
- Preview integral bloqueado: painel neutro “Modelo protegido” com “Desbloquear”, sem conteúdo. Cancelar mantém estado bloqueado, sem mostrar outro modelo como se fosse o selecionado.
- Nome do arquivo continua visível no sistema. O cabeçalho público integral contém apenas dados técnicos mínimos; não publicar fontes, textos, camadas ou miniaturas.

### Cópia sem assinaturas

Disponível sem senha somente no modo de proteção das assinaturas. Remover imagens, camadas e colunas de assinatura; reconstruir relações válidas, sem espaços reservados artificiais.

- Exibir exatamente “Cópia sem assinaturas — o original está preservado”.
- Qualquer salvamento pede novo nome/destino e cria novo modelo; nunca sobrescrever o protegido por salvar, autosave ou recuperação.
- Adicionar assinatura nessa cópia exige senha; sem assinatura pode salvar desprotegida ou receber proteção integral opcional.
- No modo integral, só é possível produzir cópia sem assinaturas depois de desbloquear o documento inteiro.

### Senhas e sessão

- Aceitar de 8 a 64 caracteres, com espaços, acentos e possibilidade de colar; sem exigência de maiúsculas/números/símbolos.
- Confirmação, mostrar/ocultar e orientação discreta para preferir frase longa. Não truncar nem remover espaços silenciosamente; especificar representação Unicode interoperável na etapa 2.
- Não salvar senha em configuração, arquivo ou log. Sem recuperação da senha pelo FORNAX.
- Enquanto o modelo estiver ativo, não expirar. Ao sair, iniciar cinco minutos individuais; retorno antes do prazo cancela a contagem e nova saída reinicia.
- Expiração interna descarta acesso e previews protegidos. Não abrir modal sobre outro trabalho: perguntar ao retornar ao modelo.
- No retorno expirado: senha ou abrir sem assinaturas no modo parcial; senha ou cancelar no integral.
- Fechar o programa descarta desbloqueios. Alteração externa invalida a revisão em memória e exige recarregamento/verificação; isso não é recusa permanente do modelo público alterado.
- Não bloquear por tentativas incorretas. Limitar custo e concorrência de derivação sem criar bloqueio por erros.
- Jobs legítimos já autorizados podem concluir; não revogar geração em andamento por troca de modelo. Recursos retidos pelo job não podem reabrir o acesso da interface após expiração.

### Alteração externa: alerta, não bloqueio do conteúdo público

Decisão do usuário: detectar alteração do conteúdo público em modelo com assinaturas protegidas e alertar, permitindo revisão e continuidade, sem tornar a assinatura irrecuperável por esse motivo.

Proposta técnica para cumprir essa decisão, a especificar/testar na etapa 2:

- Guardar dentro do bloco autenticado um resumo de referência do documento público e seus assets. Compará-lo ao conteúdo atual após desbloqueio válido.
- Não usar o resumo do conteúdo público atual como condição obrigatória para descriptografar: isso bloquearia exatamente a recuperação aprovada.
- Divergência abre alerta antes de exibir/usar assinaturas: “Foi identificada uma possível alteração no conteúdo deste modelo desde o último salvamento protegido. Confira os textos, imagens e configurações antes de gerar materiais.” Oferecer continuar para revisar ou cancelar a abertura.
- Continuar permite edição e uso autorizados. Não destruir, corrigir ou sobrescrever o arquivo automaticamente. Somente salvamento explícito do modelo completo desbloqueado estabelece nova referência.
- Durante a mesma sessão/revisão já reconhecida, evitar repetição do alerta em cada preview. Nova alteração exige nova verificação; não persistir aceite como se fosse um salvamento.
- Antes da senha, não é possível confirmar criptograficamente esse resumo. A checagem confiável ocorre depois do desbloqueio e antes do acesso completo; abrir sem assinaturas não depende da senha nem promete essa verificação.
- Distinguir conteúdo público válido mas alterado de estrutura inválida, limites excedidos ou conteúdo protegido adulterado. Nestes últimos casos não ignorar validação nem liberar dados parciais.
- Senha incorreta ou falha de autenticação criptográfica: informar que a senha está incorreta ou o conteúdo protegido está danificado/alterado. Um alerta não torna possível decifrar bytes inválidos com segurança.
- No modo integral não há documento público editável: adulteração do bloco cifrado impede a abertura. Preservar o arquivo e oferecer recuperação válida quando disponível, sem opção de ignorar autenticação.
- O alerta não certifica autoria, não detecta necessariamente retorno a uma versão antiga válida e não substitui revisão do documento pelo usuário.

### Exportação e importação

- Modelo parcial: exportar/importar sem assinaturas não exige senha e remove efetivamente os elementos protegidos. Originais permanecem intactos.
- Para incluir assinaturas, desbloquear; permitir tentar a mesma senha em todos os selecionados. Preservar sucessos e reapresentar só falhas, com nova tentativa ou opção de omitir assinaturas.
- Modelo integral: desbloqueio obrigatório mesmo para gerar exportação sem assinaturas. Falha permite tentar novamente ou retirar esse modelo do lote; não prometer exportação pública sem acesso.
- Preservar proteção integral por padrão nas cópias exportadas/importadas. Remover/reduzir proteção exige ação explícita após desbloqueio e respeita presença de assinaturas.
- Criar e confirmar uma senha de exportação compartilhada por todos os modelos protegidos do lote. Dispensar apenas se nenhuma cópia exportada mantiver proteção.
- Recriptografar cópias exportadas com novas chaves, salts e nonces, sem alterar originais ou transportar senha local. Mesma senha não significa mesma chave.
- Na importação, tentar senha do pacote uma vez para todos; ZIPs de terceiros podem misturar senhas e modos. Exibir apenas falhas restantes.
- Antes de incorporar conteúdo protegido, exigir nova senha local individual ou uma para todos, com confirmação. Recriptografar; senha de exportação não permanece chave alternativa, salvo escolha deliberada da mesma senha local.
- Temporário usa senha recebida durante a sessão; nova senha local somente ao incorporar.
- Recebido permanece intacto. Conflitos, cancelamentos, resultados parciais e modelos ignorados devem ser claros; nunca sobrescrever silenciosamente.

### Migração dos modelos antigos

- Listar pastas e `.fornax` sem converter tudo ao iniciar. Converter quando selecionar, inclusive o último modelo selecionado automaticamente na abertura.
- Sem assinatura: converter automaticamente. Com assinatura: cadastrar/confirmar senha e escolher escopo da proteção antes de exibir assinatura; converter e abrir já desbloqueado.
- Cancelamento: oferecer cópia sem assinaturas ou retorno à seleção anterior. Cópia não substitui o legado; eventual salvamento pede novo modelo.
- Normalizar JSON com adaptadores existentes. Página única vira página 1/frente sem criar verso. Manter dimensões, fontes, formatação, camadas, placeholders, links, máscaras, grupos, assinaturas e assets.
- Usar defaults compatíveis com o comportamento antigo, não padrões novos indiscriminadamente.
- Gravar temporário, reabrir, validar conteúdo e proteção, publicar atomicamente e somente depois remover pasta antiga e caches correspondentes.
- Falha antes da publicação preserva original. Interrupção depois da publicação retoma limpeza e evita duplicidade. Não manter backup aberto de assinaturas como solução de recuperação.
- Não remover arquivo compartilhado por outro modelo ou pasta externa de imagens variáveis. Isso é proteção contra perda de dados, não detecção proibida de imagens iguais a assinaturas.
- Legados não selecionados permanecem intactos e não são considerados protegidos. Não haverá migração obrigatória em lote.
- Remoção normal não garante apagamento físico de SSD, backup externo ou sincronização anterior.

## Diretrizes técnicas aprovadas e detalhamento pendente

### Contêiner e criptografia

- ZIP versionado como envelope; manifesto declara modo, versão e recursos obrigatórios. Versão do contêiner é independente do JSON. Rejeitar recursos obrigatórios desconhecidos sem ignorar proteção.
- Biblioteca `cryptography`, AES-256-GCM e derivação Argon2id. Chave de dados aleatória protegida por chave derivada da senha; sem algoritmos próprios ou criptografia ZIP tradicional.
- Parâmetros iniciais de benchmark: 64 MiB e três passagens no Argon2id; meta aproximada de 0,5–1 segundo em máquina modesta, não promessa. Fechar paralelismo e parâmetros versionados no checkpoint 2.2 com medições.
- Salts aleatórios por proteção, nonces únicos para cada chave, fonte aleatória do sistema. Separar propósitos de chave/nonces; definir bytes autenticados, serialização e tratamento de erros na especificação.
- Autenticar metadados essenciais e conteúdo protegido; no modo parcial, checagem do resumo público é separada, permitindo alerta recuperável.
- Leitor aceita perfis explicitamente suportados e impõe limites antes de executar KDF. Não obedecer a custos arbitrários declarados por arquivos externos.
- Fixar limites de entradas, bytes comprimidos/descomprimidos, expansão, dimensões/pixels de imagens, profundidade e custo agregado de lote com base na etapa 1; verificar durante leitura, não só cabeçalhos.
- Rejeitar caminhos absolutos/traversal, links simbólicos, duplicatas, versões incompatíveis e pacotes aninhados não previstos. Não extrair arbitrariamente todo ZIP recebido.
- Não prometer eliminação perfeita de bytes da memória Python/Qt. Minimizar referências e duração do acesso.

### Persistência e renderização

- Introduzir camada de armazenamento e resolvedor de assets, preservando renderer compartilhado entre editor, preview e geração.
- Modelo parcial: miniaturas persistentes sem assinaturas; preview completo somente em memória. Integral: nenhum preview/conteúdo em claro no disco; placeholder genérico bloqueado.
- Backup, histórico persistido e recuperação que incluam conteúdo protegido devem continuar criptografados.
- Não materializar assets protegidos em arquivos abertos como atalho para APIs que esperam caminhos; adaptar acesso ou definir alternativa segura antes de integrar.
- Invalidar resultados atrasados de workers por identidade/revisão/autorização. Conteúdo de um modelo não pode aparecer no preview de outro.
- Publicar atomicamente, validar antes de substituir última versão válida e recuperar interrupções.
- Resultados finais solicitados pelo usuário podem conter assinaturas; são distintos de caches internos.

## Pontos atuais do código

Levantamento inicial, a confirmar antes das alterações:

| Área | Arquivos e dependências relevantes |
|---|---|
| Documento, versões e recuperação | `core/model_document.py`: normalização v3/v4, páginas, assinatura com identidade própria, leitura, publicação atômica e backup JSON |
| Biblioteca e fluxos principais | `features/workspace/main_window.py`: enumeração atual por pastas, seleção, duplicação, renomeação, importação/exportação ZIP, preview e geração |
| Interface de importação/exportação | `features/workspace/import_models_dialog.py`, `features/workspace/export_models_dialog.py` |
| Editor e salvamento | `features/editor/editor_window.py`, `features/editor/document_session.py`, `features/editor/model_adapter.py` |
| Caches e miniaturas | `core/render_cache.py`: `.render_cache`, imagens de preview e identificação por caminho do modelo |
| Histórico e informações | `core/history_manager.py`, `core/model_info.py` e recuperação do editor |
| Assets e renderização | `features/editor/canvas_items.py`, `features/generator/renderer.py`, `features/generator/workers.py`, `features/generator/imposition.py` |
| Colunas de assinatura | `features/spreadsheet/headers.py`, `features/spreadsheet/table_panel.py` e atualização de campos no workspace |
| Inicialização e distribuição | `main.py`, entradas em `features/workspace/`, `script_nuitka.py`, `script_appimage.sh` e `com.leobelisario.FornaxForge.yaml` (fonte; `.flatpak` é binário) |
| Regressão existente | `tests/test_model_document.py`, `tests/test_model_info.py`, `tests/test_editor_model_adapter.py`, testes de geração, campos da tabela e editor |

O armazenamento atual assume diretórios e caminhos físicos. Evitar substituir essas referências de forma indiscriminada: introduzir uma camada de acesso ao modelo e um resolvedor de assets, preservando o contrato de renderização existente.

## Etapa 1 — Mapear dependências, criar testes de referência e levantar caminhos de arquivos

Risco baixo. Objetivo: produzir evidência reproduzível do comportamento atual antes de mudar armazenamento.

### 1.1 — Inventário de leitura e escrita
- **Objetivo:** localizar todo acesso a documento, assets e dados derivados.
- **Entregas:** mapa com funções/arquivos, chamadas e destinos de biblioteca, preview, editor, workers, geração, importação/exportação, logs, temporários, backup e recuperação. Confirmar caminhos do levantamento inicial e dependências de empacotamento.
- **Aceite:** cada fluxo de abrir até fechar tem seus pontos de leitura/escrita identificados; busca por operações de arquivo confrontada com fluxos em execução. Registrar lacunas, sem marcá-las resolvidas por suposição.

### 1.2 — Modelos sintéticos e contratos funcionais
- **Objetivo:** fixar o que não pode regredir.
- **Entregas:** fixtures antigas/atuais, uma/duas páginas, fontes ricas, assinaturas distintas visíveis/ocultas, máscaras, grupos, links, imagens variáveis e assets ausentes; testes de normalização, relações, colunas e ordem de geração.
- **Aceite:** testes passam no código atual ou falhas preexistentes ficam reproduzidas e separadas. Não usar material sensível real.

### 1.3 — Referências visuais, desempenho e volume
- **Objetivo:** estabelecer comparação objetiva e dimensionar limites.
- **Entregas:** referências de pixels editor/preview/PNG/PDF e imposição frente/verso; medições repetíveis de abertura, troca, geração e lote com ambiente/amostras descritos; tamanhos, entradas, pixels e memória dos casos representativos.
- **Aceite:** procedimento reexecutável e resultados registrados, distinguindo cache frio/quente e variação. Tolerâncias de comparação justificadas. Etapa 2 recebe dados para definir limites.

## Etapa 2 — Definir a estrutura do .fornax, a proteção das assinaturas e a estratégia de migração

Risco alto. Objetivo: fechar uma especificação implementável, sem decisões criptográficas implícitas.

### 2.1 — Esquema dos três modos e contratos de acesso
- **Objetivo:** definir como reconstruir o mesmo documento a partir de cada modo.
- **Entregas:** manifesto e exemplos sem segredos reais; versões, IDs/revisões, organização público/protegido, relações/ordem de camadas, resolvedor de assets e transições de modo. Especificar quais informações ficam públicas.
- **Aceite:** exemplos permitem reconstrução integral e cópia sem assinatura sem objetos órfãos; integral não expõe conteúdo. Uma senha por modelo; nenhuma heurística de imagem duplicada.

### 2.2 — Especificação criptográfica e limites de entrada
- **Objetivo:** tornar cifragem, derivação e leitura segura reproduzíveis.
- **Entregas:** versões/dependências compatíveis com os pacotes, representação de senha de 8–64 caracteres, chaves, salts, nonces, AAD, perfis Argon2id medidos, limites numéricos por arquivo/lote e política de erro. Pequeno benchmark isolado permitido, sem integrar funcionalidade ao programa.
- **Aceite:** especificação suficiente para escrever testes conhecidos de round-trip e adulteração; nenhum custo de arquivo externo sem teto; mesmas senhas Unicode interoperáveis nas plataformas suportadas. Definir mudança de senha sem prometer revogar cópias antigas.

### 2.3 — Alerta de alteração, sessão e fluxos de acesso
- **Objetivo:** separar falhas recuperáveis de falhas de autenticação e evitar acessos laterais.
- **Entregas:** método canônico de resumo público/asset com referência autenticada interna, campos cobertos e casos ignorados; máquina de estados de sessão; sequência de alerta/aceite, expiração, jobs, cópia e temporário; telas de proteção e compartilhamento.
- **Aceite:** cenários escritos cobrem público alterado + senha correta (alerta e continuidade), cifrado adulterado (sem liberação), integral bloqueado, retornos antes/depois de cinco minutos e resultados atrasados. Nada dispara modal de expiração sobre outro modelo.

### 2.4 — Migração transacional e revisão da especificação
- **Objetivo:** fechar publicação, recuperação e limpeza antes de gravar dados reais.
- **Entregas:** sequência de migração e pontos de falha; contrato de backup/autosave; destino de cada dado sensível; matriz de importação/exportação dos três modos; política de conflitos e cancelamento.
- **Aceite:** walkthrough de interrupção em cada ponto preserva última versão válida, sem duplicidade silenciosa ou backup desprotegido final. Registrar revisão do conjunto 2.1–2.4 e questões resolvidas antes da etapa 3.

## Etapa 3 — Implementar com as decisões documentadas

Risco alto, exceto acabamento de distribuição. Objetivo: integrar em incrementos testáveis, preservando o resultado gráfico.

### 3.1 — Contêiner e validação de entradas
- **Objetivo:** ler/gravar envelope e modo público independentemente da interface.
- **Entregas:** leitor/escritor, manifesto, resolvedor, normalização existente e publicação atômica.
- **Aceite:** round-trip sintético preserva atributos/assets; entradas perigosas e limites são rejeitados, inclusive em leitura progressiva; falha não publica pacote incompleto.

### 3.2 — Criptografia e três modos
- **Objetivo:** implementar núcleo de proteção sem diálogos.
- **Entregas:** cifragem, desbloqueio, troca de senha, recriptografia de cópias, separação/restauração de assinaturas, modo integral e checagem de alteração pública.
- **Aceite:** senha incorreta/cifrado adulterado não liberam bytes; público alterado permite decifrar e sinaliza divergência; assinaturas não vazam em parte pública por erro de separação; imagens comuns permanecem comuns. Novas cópias usam material criptográfico independente.

### 3.3 — Sessão e acesso autorizado aos assets
- **Objetivo:** centralizar o acesso antes de conectar componentes visuais.
- **Entregas:** modos bloqueado/desbloqueado/temporário/cópia, relógio e expiração, identidade/revisão, acesso em memória e ciclo de workers.
- **Aceite:** testes com relógio controlado nos limites de cinco minutos, retorno/saída, fechamento, suspensão e alteração externa; job autorizado conclui sem renovar acesso da UI; nenhum caminho materializa asset protegido aberto no disco.

### 3.4 — Biblioteca, preview e tabela
- **Objetivo:** operar a seleção usando `.fornax` e estados de acesso.
- **Entregas:** listagem mista, seleção persistida, renomeação/duplicação/exclusão/informações; diálogo senha/sem assinatura, preview integral bloqueado e alerta de mudança pública.
- **Aceite:** cancelamento preserva seleção/estado coerente; tabela sem colunas de assinaturas removidas; preview atrasado não reaparece após expiração/troca; duplicar protegido exige fluxo autorizado e preserva proteção. Comparar preview à etapa 1.

### 3.5 — Editor, salvamento e recuperação
- **Objetivo:** salvar modos e transições sem sobrescrever originais indevidamente.
- **Entregas:** abertura completa/cópia, seleção de proteção, cadastro de senha, histórico/autosave/backup protegido e publicação atômica.
- **Aceite:** cópia pede nome e não sobrescreve original; assinatura nova exige proteção salvo integral já protegido; reduzir proteção exige desbloqueio; recuperação não escreve conteúdo protegido aberto. Público alterado não é salvo automaticamente para apagar alerta.

### 3.6 — Geração e caches
- **Objetivo:** manter mesmos resultados sem resíduos intermediários desprotegidos.
- **Entregas:** integração renderer/workers/imposição com assets autorizados, caches públicos ou protegidos conforme especificação e invalidação.
- **Aceite:** PNG/PDF, frente/verso, ordem por item e imposição equivalentes à referência; nenhum temporário aberto contendo conteúdo protegido; geração já autorizada pode terminar após troca de modelo.

### 3.7 — Conversão de legado ao selecionar
- **Objetivo:** migrar sem perda e sem execução em lote na inicialização.
- **Entregas:** detecção, cadastro quando necessário, normalização, verificação, publicação, limpeza e retomada transacional.
- **Aceite:** uma página continua uma; fixtures antigas preservam pixels/campos; cancelamento não libera assinatura; falhas antes/depois da publicação testadas; não repetir conversão nem duplicar entrada; modelos não selecionados intactos.

### 3.8 — Exportação individual e em lote
- **Objetivo:** compartilhar sem revelar a senha local.
- **Entregas:** seleção de assinaturas, tentativas compartilhadas/só falhas, proteção integral preservada, senha de exportação e pacote final.
- **Aceite:** combinações dos três modos funcionam; integral não exporta conteúdo sem desbloqueio; originais permanecem byte a byte intactos; saída sem proteção não carrega bloco de assinatura oculto; pacote abre em ambiente limpo com senha de exportação.

### 3.9 — Importação e novas senhas locais
- **Objetivo:** incorporar pacotes sem herdar segredo do remetente como chave alternativa.
- **Entregas:** seleção de modelos, importação sem assinaturas quando possível, desbloqueio, senha individual/comum local, conflitos, cancelamento e relatório de falha parcial.
- **Aceite:** lotes mistos/senhas diferentes tratados; senha local diferente substitui acesso por senha de transporte na cópia; recebido permanece intacto; nada é incorporado parcialmente como modelo válido.

### 3.10 — Abertura externa e distribuição
- **Objetivo:** suportar duplo clique e uso temporário nos pacotes reais.
- **Entregas:** argumentos/eventos nativos, app já aberto, pergunta de incorporação, destinos explícitos e associação de ícone/extensão.
- **Aceite:** caminhos com espaços/acentos, editor ativo e trabalho não salvo preservados; temporários não reaparecem na próxima execução; testes nativos por SO suportado registrados, não presumidos por testes Linux.

### 3.11 — Textos, ajuda e traduções
- **Objetivo:** deixar os modos e limites compreensíveis.
- **Entregas:** português/inglês/espanhol, tutorial/ajuda, instruções de testers e documentação de formato/dependências.
- **Aceite:** nenhum fluxo protegido sem tradução prevista; explicar senha perdida, modos, alerta, cinco minutos, assinatura versus imagem comum e visibilidade do nome do arquivo. Nenhuma promessa de certificação/autoria/proteção absoluta.

## Etapa 4 — Revisar criptografia, migração e possíveis vazamentos em caches e temporários

Risco alto. Objetivo: revisar o conjunto com evidências antes de distribuir.

### 4.1 — Revisão criptográfica e testes adversariais
- **Objetivo:** verificar implementação contra especificação, além do caminho feliz.
- **Entregas:** revisão de KDF/chaves/nonces/AAD, limites, Unicode, troca de senha, alteração pública, adulteração de cabeçalhos/cifrados e pacotes maliciosos.
- **Aceite:** falhas relevantes corrigidas e retestadas; nenhum caminho permite ignorar autenticação do bloco; alterações públicas válidas permitem alerta e continuidade. Buscar revisão independente especializada antes de apresentar proteção como consolidada; registrar se não realizada.

### 4.2 — Auditoria de dados derivados e sessão
- **Objetivo:** procurar conteúdo sensível fora do armazenamento autorizado.
- **Entregas:** varredura com marcadores sintéticos em caches, miniaturas, logs, temporários, backup, histórico e recuperação; inspeção de imagens derivadas, não somente busca textual; cenários de fechamento/crash/troca/expiração e jobs tardios.
- **Aceite:** nenhuma cópia aberta criada pelo fluxo protegido fora dos resultados finais autorizados; integral também não vaza documento/miniatura. Não classificar imagem comum deliberada como falha da política aprovada. Registrar limites de memória/OS e arquivos legados anteriores.

### 4.3 — Migração e persistência sob falhas
- **Objetivo:** provar recuperação sem perda de dados.
- **Entregas:** injeção de disco cheio, permissão negada, interrupção antes/depois da publicação/limpeza, asset ausente, versão desconhecida e backup inválido.
- **Aceite:** última versão válida recuperável, nenhuma substituição silenciosa ou duplicidade de biblioteca, nenhuma limpeza apaga assets de terceiros; migração não é declarada concluída com resíduos pendentes.

### 4.4 — Regressão funcional, visual e desempenho
- **Objetivo:** comparar o produto final com a referência inicial.
- **Entregas:** repetir medições 1.3 no mesmo ambiente, testar três modos, páginas/assinaturas, clipboard/grupos/máscaras, tabela, preview e exportações; testes dos pacotes nativos.
- **Aceite:** resultados equivalentes e desvios explicados/corrigidos; custo de desbloqueio separado do custo recorrente de preview/geração; máquinas modestas avaliadas sem reduzir proteção arbitrariamente. Plataforma não testada permanece pendente.

### 4.5 — Fechamento para distribuição
- **Objetivo:** consolidar evidências e pendências reais.
- **Entregas:** relatório final de checkpoints, riscos conhecidos, versões/dependências/licenças, instruções de migração/recuperação e checklist de instalação/associação.
- **Aceite:** pendências relevantes resolvidas, documentação coerente com testes e ausência de alegações de certificação. Não concluir por economia de tokens ou apenas por testes automatizados passarem.

## Controle de execução e retomada

A organização anterior de dez etapas foi substituída pelos checkpoints abaixo. Nenhuma etapa antiga deve ser tratada como concluída por esta reorganização. Referência/mapeamento ficam na etapa 1; especificação na 2; implementação, migração, compartilhamento, abertura e documentação na 3; auditoria e liberação na 4.

| Checkpoint | Estado | Evidência / próximo trabalho |
|---|---|---|
| 1.1 | Concluído | Inventário e fluxos registrados em `history/ETAPA_1_REFERENCIA_E_MAPA_FORNAX.md` |
| 1.2 | Concluído | Fixture sintética e 5 contratos novos; validação focada com 72 testes aprovados |
| 1.3 | Concluído | Captura reproduzível em `tools/capture_fornax_stage1_baseline.py`; métricas e hashes registrados |
| 2.1 | Concluído | Esquema dos três modos, exemplos, separação/reconstrução e contratos na especificação da Etapa 2 |
| 2.2 | Concluído | Perfil e limites definidos; experimento Linux com cryptography 50.0.1; mediana KDF 116,444 ms; validação nativa por SO prevista em 4.4 |
| 2.3 | Concluído | Resumo autenticado separado da descriptografia, alerta recuperável e estados de sessão especificados |
| 2.4 | Concluído | Transações, walkthrough de falhas, migração e política de dados derivados revisados |
| 3.1 | Concluído | Núcleo público em `core/fornax_container.py`; round-trip, limites, entradas hostis e publicação atômica validados por `tests/test_fornax_container.py` |
| 3.2 | Concluído | Argon2id + AES-256-GCM, modos parcial/integral, cópia sem assinatura, recriptografia e alerta de alteração pública validados em `tests/test_fornax_crypto.py` |
| 3.3 | Concluído | Sessão, tolerância individual de cinco minutos, suspensão, revisão física, tokens e snapshots imutáveis de jobs validados em `tests/test_fornax_session.py` |
| 3.4 | Concluído | Biblioteca mista, sessão visual, preview/tabela em memória e operações de biblioteca validados. |
| 3.5 | Concluído | Editor em memória, escolha de proteção, salvamento autorizado, backup e recuperação validados. |
| 3.6 | Concluído | Geração usa snapshots autorizados; prévia protegida e intermediários de imposição permanecem em memória; PNG/PDF, frente/verso e imposição validados. |
| 3.7 | Concluído | Conversão ao selecionar, diário retomável, proteção obrigatória de assinaturas, publicação verificada e limpeza condicionada por hashes validadas. |
| 3.8 | Concluído | Cópias individuais e lotes mistos, remoção integral de assinaturas, nova senha de transporte e preservação byte a byte dos originais validadas em `tests/test_fornax_export.py`. |
| 3.9 | Concluído | Importação individual/lote, retirada opcional de assinaturas, troca obrigatória da senha de transporte por senha local e publicação independente validadas em `tests/test_fornax_import.py`. |
| 3.10 | Concluído | Entrada por argumento/evento nativo, instância única, uso temporário, fila durante edição e associações de distribuição implementados; validação nativa dos pacotes por SO permanece no gate 4.4. |
| 3.11 | Pendente | — |
| 4.1 | Revisão interna concluída | Correções de sobrescrita na exportação, snapshot, limites de entrada, parsing, SVG e aceite de alterações públicas; evidências em `history/ETAPA_4_REVISAO_FORNAX.md`. Revisão independente não realizada. |
| 4.2 | Revisão interna concluída | Ciclo de vida, caches, recuperação cifrada e IPC; evidências em ETAPA_4_REVISAO_FORNAX.md. |
| 4.3 | Revisão interna concluída | Falhas de persistência, migração retomável, concorrência, backups e importação; relatório em ETAPA_4_REVISAO_FORNAX.md. Validação nativa no 4.4. |
| 4.4 | Em andamento | Regressão local Linux, IPC real, paridade de PNGs e medições dos três modos; correções de sessão/cache, reinício, geometria e IDs de máscara. Relatório em ETAPA_4_REVISAO_FORNAX.md e dados em ETAPA_4_4_MEDICOES_FORNAX.json. Pacotes nativos e máquina modesta pendentes. |
| 4.5 | Em andamento | Consolidação em ETAPA_4_5_FECHAMENTO_FORNAX.md; guia de uso/migração/recuperação e checklist nativo em docs/. Liberação depende de 3.11, gates de 4.4 e conteúdo/licenças dos pacotes. |

**Retomada: concluir 3.11 e os gates externos de 4.4 — pacotes nativos e máquina modesta.** Não repetir a referência inicial nem as correções locais já registradas sem mudança que justifique nova coleta. O checkpoint 3.11 permanece pendente e deve ser retomado antes da distribuição; 4.5 não está liberado como fechamento concluído.

### Registro da Etapa 2 — 20/09/2026

- Estado: especificação concluída; não equivale a implementação validada nem auditoria independente.
- Documento normativo: `history/ETAPA_2_ESPECIFICACAO_FORMATO_FORNAX.md`.
- Experimento isolado: `tools/probe_fornax_crypto_spec.py`; dependência instalada apenas em `/tmp/fornax-stage2-crypto`, sem alterar requirements ou ambiente do aplicativo.
- Comando: `PYTHONPATH=/tmp/fornax-stage2-crypto .venv/bin/python tools/probe_fornax_crypto_spec.py`.
- Resultados: round-trip, limites/Unicode, cinco rejeições criptográficas esperadas e alteração pública sem impedir decifrar. Argon2id 64 MiB / 3 passagens / 1 lane, sete amostras e mediana 116,444 ms.
- Cuidados explicitados: alerta só após senha válida; integridade criptográfica não pode ser ignorada; geração agrupada/preview de folhas não podem deixar intermediários sensíveis abertos; backups e redução de proteção têm regras próprias.
- Gates posteriores: execução em instaladores de Windows/macOS, equipamento modesto, carga de assets maiores e revisão especializada. Não foram testados aqui.
- Retomada: 3.1, usando a especificação; testes de contêiner/ZIP antes de integração com UI. Etapa 2 não altera renderer, tabela ou persistência em produção.

### Registro da Etapa 1 — 20/09/2026

- Estado: concluída.
- Documento de evidência: `history/ETAPA_1_REFERENCIA_E_MAPA_FORNAX.md`.
- Novos contratos: `tests/test_fornax_stage1_contracts.py` e fixture `tests/fixtures/fornax_stage1/`.
- Captura local: `.validation/fornax_stage1/report.json`, gerada pelo script versionado; artefatos de `.validation` permanecem ignorados.
- Validação focada: 72 testes aprovados. Regressão ampliada: 131 testes + 10 subtestes em `tests/` e 63 testes do editor aprovados, com um aviso preexistente de API Qt obsoleta na tabela.
- Riscos encaminhados à Etapa 2: extração integral de ZIP, caminhos físicos acoplados ao diretório, caches sem estado de autorização e ausência de limites de entrada.
- Retomada: iniciar 2.1 sem alterar renderer/tabela; definir manifesto, organização público/protegido e transições dos três modos.

Ao concluir ou interromper cada checkpoint, acrescentar registro:

- Checkpoint, data e estado: pendente / em andamento / concluído / bloqueado.
- Arquivos/documentos afetados e decisões técnicas fechadas.
- Comandos/testes executados, ambiente e resultados verificáveis.
- Pendências, riscos e desvios em relação ao aceite.
- Ponto exato de retomada e dependências do próximo checkpoint.

Não substituir evidências por “funcionou”. Não refazer trabalho já validado sem motivo; após mudanças, repetir verificações afetadas.

## Referências para a especificação e revisão

- Cryptography, AEAD: https://cryptography.io/en/stable/hazmat/primitives/aead/
- Cryptography, KDFs: https://cryptography.io/en/stable/hazmat/primitives/key-derivation-functions/
- OWASP Cryptographic Storage: https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- OWASP Key Management: https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html
- OWASP Password Storage: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP Authentication: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

Conferir documentação da versão efetivamente escolhida no checkpoint 2.2. Este plano não substitui especificação criptográfica nem revisão de segurança.

### Registro do checkpoint 4.5 — 20/09/2026

- Avanço solicitado pelo usuário: consolidação documental preparada, sem declarar liberação.
- Relatório: `history/ETAPA_4_5_FECHAMENTO_FORNAX.md`.
- Guias: `docs/GUIA_MODELOS_FORNAX.md` e `docs/CHECKLIST_DISTRIBUICAO_FORNAX.md`; README atualizado.
- Inventário local de versões conferido; não substitui o inventário dos pacotes finais.
- Identificadas mensagens técnicas sem tradução, ajuda ainda não empacotada e necessidade de conferir/incluir avisos completos por artefato.
- Próxima ação local: checkpoint 3.11; depois fechar os gates nativos/hardware do 4.4 e a liberação 4.5.
