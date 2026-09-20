# Etapa 3 — Registro da implementação do `.fornax`

Data de início: 20/09/2026.

Este registro acompanha somente o que foi implementado e efetivamente testado. As decisões normativas permanecem em `ETAPA_2_ESPECIFICACAO_FORMATO_FORNAX.md`.

## Checkpoint 3.1 — Contêiner e validação de entradas

Estado: **concluído**.

Implementado em `core/fornax_container.py`:

- envelope ZIP público `.fornax` v1 com manifesto, identidade e revisão UUIDv4;
- escrita determinística dos JSONs e incorporação de assets com nomes aleatórios;
- snapshot de documento e resolvedor de assets em memória, sem `extractall()` ou diretório descriptografado;
- publicação por arquivo pendente no mesmo volume, `fsync`, reabertura, validação lógica e substituição atômica;
- rejeição de assinaturas no modo sem proteção;
- limites de arquivo, entradas, JSON, asset e soma descompactada;
- rejeição de traversal, paths absolutos, barras invertidas, symlinks, duplicatas, nomes ambíguos, criptografia ZIP tradicional, compressão desconhecida e entradas fora da whitelist;
- JSON estrito contra chaves repetidas, números não finitos, profundidade e quantidade excessivas;
- validação de PNG/JPEG/SVG, dimensões/pixels e bloqueio de scripts, entidades e referências externas em SVG.

Validação executada:

- `python -m pytest -q tests`: **144 testes + 10 subtestes aprovados**;
- suíte isolada do editor em modo offscreen: **63 testes aprovados**;
- teste focado do contêiner e contratos de documento: aprovado, incluindo round-trip de duas páginas, assets, falha antes da publicação e entradas hostis.

O aplicativo ainda não enumera nem abre `.fornax` na interface. Isso é intencional: a biblioteca só será conectada depois do núcleo criptográfico e da sessão autorizada. Os modos `signatures` e `full` retornam erro explícito neste checkpoint; serão implementados no 3.2.

Próximo checkpoint: **3.2 — Criptografia e três modos**.

## Checkpoint 3.2 — Criptografia e três modos

Estado: **concluído**.

Implementado no núcleo:

- modos `none`, `signatures` e `full` com layouts externos distintos;
- senha NFC de 8 a 64 caracteres e perfil fixo Argon2id de 64 MiB, três passagens e uma lane;
- DEK aleatória por revisão, AES-256-GCM, nonces novos e AAD separado para chave e payload;
- ZIP protegido processado somente em memória, sem materialização de conteúdo aberto;
- separação integral das camadas, assets, configuração e inventário de origem das assinaturas;
- restauração da ordem das camadas e das duas páginas após desbloqueio;
- referência SHA-256 autenticada da parte pública, permitindo desbloqueio com sinalização quando o público válido foi alterado;
- proteção integral sem documento, asset, preview ou nome interno no lado público;
- recriptografia/troca de senha e cópias com novos salts, nonces, DEKs, revisões e identidade opcional;
- cópia pública sem assinaturas com identidade nova e bloqueio de sobrescrita do original;
- dependência `cryptography==50.0.1` fixada nos requisitos, Flatpak e inclusão do Nuitka, com inventário de licença atualizado.

Validação executada:

- `python -m pytest -q tests`: **156 testes + 10 subtestes aprovados**;
- suíte isolada do editor em modo offscreen: **63 testes aprovados**;
- contratos criptográficos focados: senha incorreta, chave embrulhada e payload adulterados não liberam conteúdo; alteração pública válida sinaliza divergência e preserva restauração;
- vetor público da etapa 2 reproduzido pela implementação de produção;
- probe isolado repetido com `cryptography 50.0.1`: mediana Argon2id de **115,736 ms** neste ambiente e todas as cinco rejeições previstas aprovadas.

As chaves e documentos autorizados ainda não possuem ciclo de vida de sessão, tolerância de cinco minutos nem integração com workers. Essa fronteira pertence ao checkpoint 3.3; a interface e a biblioteca continuam sem consumir `.fornax`.

Próximo checkpoint: **3.3 — Sessão e acesso autorizado aos assets**.

## Checkpoint 3.3 — Sessão e acesso autorizado aos assets

Estado: **concluído**.

Implementado em `core/fornax_session.py` e no núcleo criptográfico:

- estados público, bloqueado, autorizado, tolerância, expirado, cópia sem assinatura, alteração externa e encerrado;
- modelo ativo sem expiração e tolerância individual de 300 segundos iniciada ao sair;
- retorno anterior ao limite reaproveita o acesso; nova saída reinicia o prazo integral;
- expiração no limite exato, encerramento do processo e suspensão do sistema descartam autorizações aplicáveis;
- KEK mantida como `bytearray` somente durante a sessão e sobrescrita antes de liberar a referência, dentro dos limites da memória gerenciada do Python;
- hash físico do pacote para invalidar sessão quando o arquivo muda externamente, exigindo recarga explícita;
- tokens de identidade, revisão e geração para descartar resultados atrasados de preview;
- snapshots imutáveis de documento/assets para jobs já autorizados concluírem após troca ou expiração, sem carregar KEK e sem renovar acesso da UI;
- modo temporário e cópia pública com o aviso exato “Cópia sem assinaturas — o original está preservado” e obrigação de salvar como novo modelo;
- Argon2id limitado a uma derivação por processo, com cancelamento permitido enquanto a solicitação ainda espera na fila.

Validação executada:

- `python -m pytest -q tests`: **166 testes + 10 subtestes aprovados**;
- suíte isolada do editor em modo offscreen: **63 testes aprovados**;
- **10 contratos de sessão** com relógio simulado, prazo exato, retorno, nova saída, suspensão, mudança externa, fechamento, cópia, temporário, token e job tardio;
- **35 testes focados** dos checkpoints 3.1–3.3 aprovados.

A sessão ainda não está conectada aos controles da tela principal, preview ou tabela. Essa integração, incluindo os diálogos e o descarte visual de resultados atrasados, pertence ao checkpoint 3.4.

Próximo checkpoint: **3.4 — Biblioteca, preview e tabela**.

## Checkpoint 3.4 — Biblioteca, preview e tabela

Estado: **concluído**.

Implementado na tela principal e no renderizador:

- inventário único para pastas legadas e arquivos `.fornax`, com chave estável por `model_id` e restauração da última seleção;
- nome externo neutro para proteção integral, sem abrir nem revelar o documento interno na listagem;
- fluxos de desbloqueio, abertura sem assinaturas, cancelamento e alerta de possível alteração externa;
- preview e tabela montados a partir do snapshot autorizado e de assets fornecidos em memória;
- cópia sem assinaturas sem colunas ou camadas residuais de assinatura;
- sessão protegida liberada ao mudar para modelo legado e descartada ao excluir ou renomear o arquivo;
- renomeação, duplicação, exclusão e informações compatíveis com a biblioteca mista;
- renderização de imagens, assinaturas, máscaras e fundos internos sem extração; imagens dinâmicas continuam resolvidas somente na pasta externa escolhida;
- preview protegido autorizado mantido em memória, sem cache gráfico aberto em disco;
- textos novos incluídos nos catálogos em inglês e espanhol.

Validação executada:

- biblioteca mista ignora resíduos transacionais e pacotes inválidos sem impedir os demais modelos;
- proteção integral cancelada permanece neutra, sem documento, tabela ou preview liberado;
- renderização por provider em memória possui paridade visual com a origem em disco;
- seleção de `.fornax` público cria tabela e preview sem `.render_cache`;
- suíte geral: **171 testes + 10 subtestes aprovados**;
- suíte isolada do editor: **63 testes aprovados**.

A edição e o salvamento de `.fornax` continuam deliberadamente bloqueados neste checkpoint. A geração final, imposição e política completa de caches pertencem ao checkpoint 3.6.

Próximo checkpoint: **3.5 — Editor, salvamento e recuperação**.

## Checkpoint 3.5 — Editor, salvamento e recuperação

Estado: **concluído**.

Implementado no editor, na sessão e na persistência:

- abertura de modelos `.fornax` públicos, parcialmente protegidos e integralmente protegidos no editor;
- decodificação de fundos, imagens e assinaturas diretamente de bytes autorizados em memória, sem diretório descriptografado;
- snapshot próprio de assets do editor, permitindo preservar trabalho mesmo se o arquivo original mudar externamente;
- novos modelos publicados diretamente como `.fornax`;
- escolha inicial entre modelo público e proteção integral quando não existem assinaturas;
- escolha entre proteção das assinaturas e proteção integral quando existem assinaturas;
- senha obrigatória de 8 a 64 caracteres, confirmação e comparação após normalização NFC;
- nova revisão protegida salva com a KEK da sessão ativa, sem solicitar novamente a senha e sem repetir Argon2id;
- remoção da última assinatura permite escolher entre retirar a proteção ou elevar o modelo a proteção integral, sempre a partir de sessão previamente autorizada;
- cópia aberta sem assinaturas exige novo nome, nova identidade e nunca sobrescreve o original;
- alteração externa durante a edição bloqueia a sobrescrita e oferece salvar como nova cópia ou recarregar o disco;
- backup lateral da revisão anterior conserva o pacote fechado, inclusive quando protegido;
- restauração automática do último pacote fechado válido quando a publicação principal está corrompida;
- autosave lateral oculto no mesmo modo de proteção, sem alterar a revisão original nem apagar alertas de mudança pública;
- oferta de recuperação ao entrar no editor e limpeza dos snapshots ao salvar ou descartar;
- configurações de exportação gravadas corretamente no contêiner ativo;
- textos novos traduzidos para inglês e espanhol.

Validação executada:

- **178 testes + 10 subtestes aprovados** na suíte geral;
- **63 testes aprovados** na suíte isolada do editor;
- salvamento protegido comprovado sem nova derivação da senha;
- cópia sem assinaturas preserva o original byte a byte, recebe identidade nova e não carrega assinaturas;
- autosave protegido pode ser lido apenas no escopo autorizado e não modifica o original;
- mudança externa nunca é sobrescrita pelo editor;
- reabertura e nova gravação de assets em memória não criam pasta descriptografada.

A geração final e a imposição ainda usam a rota legada quando acionadas pelo workspace. Sua integração com snapshots autorizados e a auditoria completa dos caches pertencem ao checkpoint 3.6.

Próximo checkpoint: **3.6 — Geração e caches**.

## Checkpoint 3.6 — Geração e caches

Estado: **concluído**.

Implementado no workspace e no pipeline de produção:

- geração de `.fornax` a partir de snapshot imutável do documento e dos assets autorizados, sem depender da sessão visual depois do início do trabalho;
- término normal de jobs já autorizados mesmo após troca de modelo ou expiração do acesso da interface;
- mesma rota de renderer para PNG, PDF por item, PDF agrupado, frente/verso e imposição;
- prévia de folhas protegidas mantida como `QImage` em memória, sem diretório temporário;
- conteúdo público conserva o cache rápido de prévia e o pipeline híbrido existente;
- PDF agrupado protegido montado diretamente a partir de imagens em memória, sem a pasta `.temp_hybrid`;
- saídas protegidas individuais publicadas sem arquivos `.partial` e injeção de links reescrita em memória;
- snapshots encerrados ao concluir, cancelar ou falhar a geração e a prévia;
- falhas removem a saída protegida incompleta do trabalho corrente;
- mensagens novas incluídas nos catálogos em inglês e espanhol.

Validação executada:

- PNG protegido de uma e duas páginas sem intermediários;
- PDF protegido por item e agrupado, preservando ordem de frente/verso e links;
- imposição duplex protegida com correspondência de faces e sem cache gráfico em disco;
- prévia protegida de folha emitida em memória e descarte do snapshot confirmado;
- pipeline público anterior preservado nos testes de regressão;
- suíte geral: **182 testes + 12 subtestes aprovados**;
- suíte isolada do editor: **63 testes aprovados**.

Os arquivos finais solicitados pelo usuário continuam sendo gravados normalmente na pasta de saída. A restrição deste checkpoint se aplica a assets descriptografados, thumbnails, cartões e folhas intermediárias; modelos públicos mantêm caches regeneráveis para conservar o desempenho.

Próximo checkpoint: **3.7 — Conversão de legado ao selecionar**.

## Checkpoint 3.7 — Conversão de legado ao selecionar

Estado: **concluído**.

Implementado na biblioteca e no núcleo de migração:

- conversão somente quando a pasta legada é selecionada, sem varredura destrutiva ou conversão em lote na inicialização;
- normalização dos documentos antigos para o esquema gráfico atual sem criar uma segunda página;
- modelos sem assinatura convertidos automaticamente para `.fornax` público;
- modelos com assinatura exigem escolha entre proteção das assinaturas e proteção integral, seguida de senha com 8 a 64 caracteres e confirmação normalizada;
- cancelamento mantém a pasta original intacta e não libera o modelo assinado na interface;
- diário sem segredos nos estados `PREPARED`, `VERIFIED`, `PUBLISHED` e `CLEANED`;
- inventário com tamanho e SHA-256 de cada arquivo antes da conversão;
- rejeição de links simbólicos e de assets ausentes, inclusive assinaturas ocultas;
- publicação do pacote validado antes de qualquer remoção da origem;
- limpeza somente de arquivos que permanecem idênticos ao inventário; arquivos novos ou modificados são preservados;
- retomada automática de pacote verificado ainda não publicado e de limpeza interrompida após publicação;
- biblioteca mostra apenas o `.fornax` validado quando uma pendência de limpeza conserva a pasta antiga;
- modelo inicial de uma instalação limpa também termina convertido para `.fornax` na primeira seleção;
- textos novos incluídos nos catálogos em inglês e espanhol.

Validação executada:

- paridade visual antes/depois para modelo público com asset incorporado;
- modelo de uma página continua com uma página;
- assinatura oculta preservada no pacote parcial e ausente da parte pública;
- asset gráfico ou assinatura oculta ausente bloqueia publicação e mantém a origem;
- interrupções simuladas antes da publicação e depois dela são retomadas sem reconversão;
- alteração concorrente e arquivo acrescentado não são apagados;
- link simbólico é rejeitado sem tocar no alvo externo;
- suíte geral: **191 testes + 12 subtestes aprovados**;
- suíte isolada do editor: **63 testes aprovados**.

Próximo checkpoint: **3.8 — Exportação individual e em lote**.

## Checkpoint 3.8 — Exportação individual e em lote

Estado: **concluído**.

Implementado no núcleo de exportação e na tela principal:

- exportação individual como um novo arquivo `.fornax` e exportação de vários modelos em um único ZIP;
- cada modelo exportado recebe identidade nova e material criptográfico independente;
- modelos públicos são copiados sem alterar o original;
- modelos com proteção de assinaturas podem ser enviados com as assinaturas ou como cópia pública sem qualquer bloco oculto de assinatura;
- modelos com proteção integral sempre exigem desbloqueio, inclusive para produzir uma cópia sem assinaturas;
- uma senha local comum pode ser tentada no lote, com nova tentativa apenas nos modelos que falharem;
- falhas individuais podem ser ignoradas; no modo parcial, também é possível enviar somente aquele modelo sem assinaturas;
- exportações com assinaturas exigem uma senha exclusiva de transporte, sem reutilizar a senha local no arquivo enviado;
- nomes repetidos no lote recebem sufixos sem sobrescrever entradas;
- limites de quantidade e tamanho do lote e publicação atômica do arquivo final;
- modelos legados precisam ser convertidos pela seleção antes de entrar no fluxo novo;
- textos do fluxo incluídos nos catálogos em inglês e espanhol.

Validação executada:

- cópia pública independente e original preservado byte a byte;
- proteção parcial recriptografada com senha de transporte, rejeitando a senha local anterior;
- cópia parcial sem assinaturas não contém `protected.bin`, registros nem assets de assinatura;
- proteção integral não permite exportação sem desbloqueio;
- lote com os três modos aberto em diretório limpo, incluindo escolha por modelo;
- falha de senha não publica saída incompleta nem altera a origem;
- suíte geral: **197 testes + 12 subtestes aprovados**;
- suíte funcional indicada no README: **56 testes aprovados**.

Próximo checkpoint: **3.9 — Importação e novas senhas locais**.

## Checkpoint 3.9 — Importação e novas senhas locais

Estado: **concluído**.

Implementado no núcleo de importação e na tela principal:

- recepção de um `.fornax` individual ou de até 1000 modelos em um lote ZIP;
- leitura restrita a membros `.fornax` de primeiro nível, sem `extractall()`, caminhos externos, links simbólicos, nomes ambíguos, criptografia ZIP tradicional ou compressão não permitida;
- escolha dos modelos e resolução de conflitos antes da incorporação;
- opção de importar com assinaturas ou produzir uma cópia pública sem assinaturas;
- modelo parcial sem assinaturas não exige a senha de transporte;
- modelo integral sempre exige desbloqueio, inclusive para reduzir a cópia local a pública;
- tentativa de uma senha de transporte comum, seguida de nova tentativa apenas para os modelos que falharem;
- falha parcial permite ignorar o modelo; no modo parcial também permite incorporá-lo sem assinaturas;
- criação de uma senha local comum ou de senhas individuais para os modelos protegidos;
- senha de transporte deixa de abrir a cópia local, que recebe nova identidade, novos salts, chaves e nonces;
- publicação independente por modelo, preservando sucessos quando outra unidade for ignorada ou falhar;
- arquivo recebido permanece intacto e nenhuma falha publica um modelo parcial;
- compatibilidade com ZIPs legados mantida, agora com validação prévia de caminhos, tipos, compressão, quantidade e tamanho;
- textos incluídos nos catálogos em inglês e espanhol.

Validação executada:

- importação pública com identidade nova e origem recebida preservada;
- importação parcial sem assinatura e sem senha;
- modos parcial e integral recriptografados com senha local diferente;
- senha de transporte rejeitada pela cópia local;
- redução integral para cópia pública somente após desbloqueio;
- lote misto incorporado unidade por unidade em ambiente limpo;
- caminhos absolutos, travessia de diretórios, subdiretórios e entradas não `.fornax` rejeitados;
- senha incorreta não publica saída nem modifica o recebido;
- suíte geral: **208 testes + 12 subtestes aprovados**;
- suíte funcional indicada no README: **56 testes aprovados**.

Próximo checkpoint: **3.10 — Abertura externa e distribuição**.

## Checkpoint 3.10 — Abertura externa e distribuição

Estado: **implementação concluída; validação nativa dos instaladores reservada ao gate 4.4**.

Implementado na inicialização, workspace e empacotamento:

- leitura de caminhos `.fornax` e ZIP recebidos pela linha de comando, inclusive com espaços e caracteres acentuados;
- tratamento de `QFileOpenEvent` para abertura de documentos pelo Finder no macOS;
- instância única por usuário com encaminhamento local dos arquivos para o processo já aberto;
- restauração e ativação da janela ao receber uma nova solicitação;
- pergunta única para adicionar o `.fornax` à biblioteca ou abri-lo temporariamente;
- uso temporário sobre uma cópia isolada, removida no encerramento e ausente da biblioteca na próxima execução;
- edição temporária exige “salvar como novo”, preservando o arquivo recebido;
- renomeação direta do modelo temporário bloqueada para evitar incorporação implícita;
- solicitações recebidas durante uma edição ficam em fila até o editor ser encerrado, sem tocar no trabalho atual;
- associação `.fornax` no instalador Windows, com ícone e comando contendo caminho entre aspas;
- MIME `application/x-fornax-template` e `%F` no Flatpak e AppImage;
- declaração UTI e tipo de documento no `Info.plist` do pacote macOS;
- textos novos incluídos em português, inglês e espanhol.

Validação executada:

- argumentos com espaços, acentos, `.fornax`, ZIP e extensões ignoradas;
- protocolo local com payload Unicode e validação dos arquivos de associação dos três sistemas;
- ciclo de fechamento do editor preservado após o novo sinal de fila;
- suíte geral: **211 testes + 12 subtestes aprovados**;
- suíte funcional indicada no README: **56 testes aprovados**;
- sintaxe Python e consistência das traduções verificadas.

Limite registrado: o ambiente atual validou código, protocolo e descritores estaticamente, mas não gera nem instala pacotes Windows/macOS. Duplo clique, registro real, Launch Services, portal de documentos e integração AppImage devem ser exercitados nos respectivos pacotes nativos no checkpoint 4.4; não são presumidos a partir dos testes Linux.

Próximo checkpoint: **3.11 — Textos, ajuda e traduções**.
