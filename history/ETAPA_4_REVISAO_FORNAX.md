# Etapa 4 — Revisão de segurança do formato FORNAX

Atualização de 20/09/2026: a validação Windows posterior, suas correções e os
artefatos compilados estão em [VALIDACAO_WINDOWS_FORNAX.md](VALIDACAO_WINDOWS_FORNAX.md).
Os resultados Linux abaixo são preservados como histórico.

Revisão interna iniciada pelo checkpoint 4.1, por solicitação do usuário.
A etapa 4 inteira não está concluída. O checkpoint 3.11 (textos, ajuda e
traduções) continua pendente; iniciar esta etapa não o conclui implicitamente.

Esta revisão de código e testes locais não é certificação nem auditoria
independente. Uma revisão especializada externa ainda não foi realizada.

## 4.1 — Revisão criptográfica e testes adversariais

Estado: revisão interna concluída; revisão independente não realizada.

### Componentes examinados

- Contêiner: parsing do manifesto/JSON, inventário ZIP, referências e SVG.
- Criptografia: Argon2id fixo em 64 MiB, 3 passagens e 1 lane; KEK de 256 bits;
  DEK aleatória de 256 bits por salvamento; AES-GCM com nonces aleatórios de
  96 bits; cabeçalho canônico como AAD e domínios distintos para chave/payload.
- Senha: NFC, 8–64 caracteres, sem remover espaços; primitivas da biblioteca
  cryptography, sem implementação própria dos algoritmos.
- Compartilhamento: destino, snapshot autorizado, senha de transporte,
  troca de senha local, limites de entrada e aviso de alteração pública.
- Cancelamento do aviso de alteração no workspace.

### Falhas corrigidas

1. **Exportação podia substituir o próprio original.** A checagem posterior à
   publicação não impedia a perda. Agora o destino coincidente é recusado antes
   da gravação, inclusive por link simbólico/hard link. Hashes em streaming
   substituem a retenção de todos os arquivos originais completos em memória.
2. **Exportação aceitava snapshot de outro modelo.** A cópia agora exige
   correspondência integral do descritor da autorização com o modelo/revisão.
3. **Importação copiava antes de validar todos os limites.** Limite físico
   verificado antes do hash/cópia; inventário inteiro validado antes do primeiro
   candidato; limite individual de 512 MiB aplicado antes da materialização.
   Caminhos não canônicos, dois-pontos e caracteres de controle são recusados.
4. **Entradas malformadas escapavam como exceções inesperadas.** Tipos inválidos
   em `mode` e JSON excessivamente profundo agora geram erros do contêiner.
5. **SVG: CSS e eventos não estavam cobertos.** Referências externas em `url()`,
   `@import`, CSS escapado, eventos, `script` com namespace e `foreignObject`
   são recusados. Gradientes por `url(#id)` continuam aceitos. SVGs legítimos
   que dependam de CSS escapado precisam ser simplificados: rejeição deliberada
   para o subconjunto aceito pelo formato.
6. **Aviso de alteração pública omitido no compartilhamento.** Importação,
   exportação, duplicação e renomeação agora pedem revisão quando o desbloqueio
   informa alteração pública. Cancelar interrompe a ação ou ignora o item.
7. **Cancelar aviso mantinha autorização em tolerância.** O workspace agora
   esquece a autorização. Retornar ao modelo exige uma nova decisão.

### Evidências

Testes novos em `tests/test_fornax_adversarial.py` cobrem adulteração de IDs,
versão, modo, perfil, salt e nonces; transplante de ciphertext; tipos hostis e
profundidade JSON; exportação sobre a origem por três caminhos; snapshot de outro
modelo; nomes não canônicos e pré-validação do lote; SVG/CSS/eventos; aceite
explícito da alteração pública e descarte da autorização ao cancelar.

Testes anteriores cobrem senha errada, ciphertext/chave encapsulada adulterados,
Unicode, troca de senha/material criptográfico e alteração pública válida.

Validação executada:

- Suíte geral `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests`:
  **241 testes e 12 subtestes aprovados**, com o aviso preexistente de API Qt
  obsoleta na cópia de alinhamento da tabela.
- Após acrescentar mais dois cenários, bateria final de
  `test_fornax_adversarial.py`, `test_fornax_session.py` e `test_fornax_editor.py`:
  **49 testes aprovados** (32 adversariais). Os números se sobrepõem, não somar.
- Bateria anterior de contêiner, criptografia, importação, exportação,
  adversariais e traduções: **75 testes aprovados**.
- `git diff --check` sem erros.

### Limites e próximos checkpoints

- Revisão independente especializada permanece pendente.
- 4.2: caches, temporários, clipboard, logs, retenção em memória, fila de abertura
  externa e resultados tardios.
- 4.3: substituição de modelos, recuperação, backups, origem/destino da
  importação, concorrência e interrupções na migração/publicação.
- 4.4: orçamento agregado de memória em lotes/arquivos grandes; instalação,
  IPC e duplo clique nativos. Os testes anteriores de IPC usam socket simulado;
  não comprovam comunicação real entre processos.
- 4.5: consolidar evidências e pendências antes da distribuição.

## 4.2 — Auditoria de dados derivados e sessão

Estado: revisão interna concluída no escopo dos fluxos locais examinados.

### Correções realizadas

- Ao fechar um editor protegido, descartamos cena, histórico, clipboard interno,
  documento e provedor de assets; a janela é destruída. O workspace reconhece
  referências Qt já destruídas antes de encaminhar arquivos externos.
- Geradores aguardam seus workers antes de liberar renderizadores, tarefas e
  snapshots protegidos. O preview libera documento, linhas e provedor também
  em cancelamentos e falhas. Resultados de revisões antigas são ignorados.
- Uma manutenção periódica efetiva a expiração das autorizações fora do modelo
  ativo. Divergência entre relógios invalida a tolerância após suspensão; não
  bloqueia o modelo ativo.
- Fechar o workspace interrompe trabalhos e libera renderizadores, imagem
  exibida, documentos, fila externa, sessões e diretórios temporários.
- IPC local recebe limites de mensagem, quantidade de caminhos/clientes, tempo
  de leitura e acesso ao usuário local. Um servidor ativo não é removido ao
  tentar iniciar outra instância.

### Evidências e alcance

`tests/test_fornax_data_lifecycle.py` adiciona 11 cenários: proteção integral e
parcial no editor/preview, clipboard interno, fechamento, expiração, callback
tardio, interrupção abrupta em subprocesso, IPC excessivo, geração autorizada,
cancelamento e falha de preview.

Os testes usam assets e marcador sintéticos. A varredura dos diretórios
monitorados procura o marcador, imagens raster abertas e entradas públicas
do contêiner. Após interrupção abrupta, só permanecem modelo e recuperação
cifrados; a recuperação é aberta com a senha e preserva a alteração realizada.
Comparações de pixels verificam a renderização normal e o PNG final autorizado.
A saída final solicitada pelo usuário permanece aberta por definição.

Validação:

- Suíte geral: **254 testes e 12 subtestes aprovados** em 132,83 s.
- Bateria funcional complementar: **56 testes aprovados** em 12,47 s.
- Após a limpeza final da imagem exibida no fechamento, regressão focal de
  ciclo de vida, layout e abertura externa: **19 testes aprovados** em 5,89 s.
- `git diff --check` sem erros.
- Há sobreposição entre baterias; não somar os totais. Permanece um aviso
  preexistente de API Qt obsoleta em alinhamento da tabela.

### Limites

- Descartar referências não garante zerar fisicamente RAM, swap, dumps ou
  caches do sistema operacional. O clipboard do sistema não é apagado.
- A varredura comprova os diretórios e cenários monitorados, não a ausência
  universal de vazamentos. Arquivos legados anteriores e imagens comuns
  deliberadas não são reclassificados como assinaturas protegidas.
- O teste de IPC usa socket simulado. Comunicação real, reinício de idioma,
  disputa de inicialização e abertura nativa em Windows/macOS continuam no 4.4.
- Falhas de disco, backups e interrupções da migração serão verificadas no 4.3.
- A revisão independente e o checkpoint 3.11 continuam pendentes.

## 4.3 — Migração e persistência sob falhas

Estado: revisão interna concluída no escopo local; validação nativa permanece no 4.4.

### Falhas encontradas e correções

1. **Limpeza legada e retomada.** O diário agora valida versão, identidade,
   estado, caminhos canônicos na raiz, inventário e hashes antes de autorizar
   qualquer remoção. Links simbólicos na origem, em pais de assets ou nos
   caminhos do diário não autorizam limpeza. Arquivos alterados/adicionados e
   diretórios não removíveis permanecem pendentes. O inventário é capturado
   antes de ler o documento, fechando uma janela de alteração concorrente.
2. **Publicação concorrente.** Migrações usam lock cooperativo; publicação de
   destinos novos usa criação atômica sem sobrescrita. Salvamentos/importações
   verificam identidade física e SHA-256 do destino, além do lock de escrita.
   Conflitos preservam o arquivo encontrado e são informados como erro.
3. **Importação e substituição.** Sobrescrever exige decisão explícita; o arquivo
   recebido nunca é destino permitido. Substituição de pasta legada usa diário
   retomável, em vez de remoção recursiva direta. O ZIP legado agora normaliza e
   publica `.fornax` pelo mesmo fluxo; modelos assinados solicitam credenciais
   antes de entrar na biblioteca. Origem do ZIP e assets externos são preservados.
   Referências de assets para fora da pasta extraída são recusadas na importação,
   evitando incorporar arquivos locais alheios ao pacote recebido.
4. **Backups.** Um original com estrutura inválida ou conteúdo público inválido
   não substitui o backup válido no salvamento.
   Ao elevar proteção ou trocar salt/senha, o backup automático recebe uma cópia
   verificada da nova revisão protegida, evitando deixar a versão pública ou a
   senha anterior no backup local. Nos demais salvamentos, mantém a revisão
   anterior. Importações autorizadas também preservam backup conforme essa regra.
5. **Recuperação.** Formato/schema futuros não provocam restauração automática
   de uma versão antiga. Backups públicos têm conteúdo validado antes da troca;
   backup inválido ou falha de restauração preservam os arquivos para diagnóstico.
   Pacotes protegidos continuam exigindo senha para validar o conteúdo cifrado.
6. **Durabilidade.** Dados e entradas de diretório são sincronizados onde o
   sistema suporta. Erros reais de I/O não são silenciosamente ignorados como
   ausência de suporte a `fsync`. A limpeza só chega a CLEANED após sua conclusão.

### Evidências

`tests/test_fornax_persistence_failures.py` acrescenta **50 cenários** e injeta
disco cheio, permissão negada,
falha de sincronização, backup e publicação; interrupções antes/depois dos estados
VERIFIED/PUBLISHED/CLEANED; limpeza parcial e retomada; caminhos/diários inválidos;
concorrência; versões futuras; backup corrompido; substituição/importação e
recuperação cifrada. Os testes legados existentes continuam cobrindo asset ausente,
assinatura oculta ausente, paridade visual e assinatura protegida.

As falhas são simuladas por exceções nos pontos de persistência. Não são testes
com desligamento físico da máquina. Os arquivos usados são sintéticos.

Validação executada:

- Suíte geral: **301 testes e 12 subtestes aprovados**, em 141,99 s.
- Após os últimos ajustes de importação e sincronização, bateria focal final de
  persistência e traduções: **53 testes aprovados**, em 7,19 s. Inclui os três
  cenários adicionados após a coleta da suíte geral; os resultados se sobrepõem.
- Bateria anterior de persistência, migração, biblioteca, importação, editor,
  sessão, contêiner e criptografia: **110 testes aprovados**, em 24,63 s.
- Catálogos inglês/espanhol atualizados e recompilados para a nova mensagem de
  limpeza pendente. Isso não conclui o checkpoint 3.11.
- `git diff --check` e compilação dos módulos alterados sem erros.
- Continua o aviso preexistente de API Qt obsoleta no alinhamento da tabela;
  nenhum ajuste na tabela foi realizado nesta etapa.


### Limites e continuidade

- Locks protegem escritores cooperativos do aplicativo. Hashes e rechecagens
  detectam alterações externas nas janelas verificadas, mas não oferecem exclusão
  absoluta contra outro processo com permissão para modificar os mesmos arquivos.
- A publicação nova exige suporte a hard links no volume de destino. Sem esse
  suporte, falha preservando os originais; não publica uma cópia parcial como
  fallback. Validar volumes/distribuições nativos no 4.4, inclusive restrições de
  FAT/exFAT e de compartilhamentos de rede.
- `fsync` não comprova resistência a falha física do disco/controlador. Sistemas
  que não permitem sincronizar diretórios têm garantia de durabilidade menor.
- Um erro posterior à substituição atômica pode significar que a nova revisão já
  existe; não se deve prometer que todo erro deixa necessariamente a revisão antiga
  como principal. Principal/backup permanecem verificáveis nos cenários testados.
- Na troca de proteção/credenciais, o backup local pode representar a **nova**
  revisão; isso não revoga cópias históricas externas.
- Recuperação automática não autentica ciphertext sem senha. Conteúdo protegido
  adulterado é recusado no desbloqueio; nunca aberto por fallback sem autorização.
- A extração de ZIP legado pode conter assinaturas abertas que já vieram assim
  no arquivo antigo. Essa retrocompatibilidade não transforma a origem recebida
  em um pacote protegido nem promete apagamento físico de dados antigos.
- Testes nativos, desempenho e revisão visual permanecem no 4.4; textos/traduções
  e ajuda de 3.11 ainda precisam ser concluídos antes da distribuição.

## Checkpoint 4.4 — regressão local e desempenho (20/09/2026)

**Estado: em andamento.** Revisão e medições locais realizadas em Linux x86_64,
Python 3.13.11/PySide6 6.11.0, plataforma Qt offscreen. Não equivale à aprovação
dos pacotes nativos nem à avaliação de uma máquina modesta.

### Correções encontradas nesta revisão

- Instância única: com `UserAccessOption`, publicar um socket Qt no Linux podia
  substituir o endpoint de uma instância viva. A eleição agora usa lock e sonda
  o endpoint antes de publicar. Falha na eleição não abre outra janela silenciosa.
  Arquivos recebidos durante a construção da janela ficam enfileirados.
- Reinício por idioma: acontece depois de encerrar a janela/event loop e liberar
  o socket. Não repete os argumentos de importação da execução anterior; distingue
  fonte, executável congelado/Nuitka e AppImage.
- Sessão inativa: o período de tolerância guarda autorização (KEK e prazo), mas
  libera documento/assets decodificados. Voltar nesse prazo reconstrói o documento
  sem repetir Argon2id. Jobs existentes mantêm seus snapshots independentes.
- Cache: QImages usam LRU compartilhado dentro da família de renderizadores,
  limitado a 256 MiB e 4.096 entradas. Não é limite da memória total do processo:
  cena, documentos, buffers de saída e imagens em uso também ocupam memória.
- Importação/exportação em lote: a aprovação não acumula todos os documentos
  abertos. Guarda credencial e SHA-256, reabre um por vez e recusa alteração desde
  a aprovação. Isso repete a derivação da chave no processamento de cada modelo,
  em troca de menor retenção agregada de assets; não solicita a senha novamente.
- Editor: preserva os pixels do canvas gravados, em vez de recalculá-los ao carregar
  pelo tamanho em milímetros. Alterações explícitas de tamanho continuam seguindo
  o fluxo físico existente. O adaptador normaliza IDs de camada sem colisões com
  o fundo e traduz IDs persistidos das máscaras para a representação da cena,
  sem alterar o documento de origem.

### Comparação com a referência 1.3

Dados completos preservados em `ETAPA_4_4_MEDICOES_FORNAX.json`. O script original
foi repetido sem modificar seu código nem sobrescrever a coleta inicial.

| Operação | Inicial (ms) | Atual (ms) |
|---|---:|---:|
| Leitura aquecida do modelo legado | 0,339 | 0,334 |
| Adaptação das duas páginas | 0,482 | 0,485 |
| Abertura do editor | 34,130 | 34,879 |
| Renderização aquecida de duas páginas | 2,665 | 2,647 |
| 100 itens / 200 páginas PDF | 862,192 | 853,828 |
| Descoberta de ZIP com 100 modelos | 8,079 | 8,356 |
| Instalação de 20 modelos legados na bancada original | 170,662 | 165,167 |

Pico de RSS dessa bancada: 128.584 → 139.036 KiB. Variações de amostra única não
provam aceleração/regressão estatística. A instalação acima é o cenário de
referência legado; não mede toda a nova migração com diálogos, proteção e limpeza.

### Três modos do novo contêiner

`tools/capture_fornax_stage4.py` registra renderização, salvamento, geração e
preview com dados sintéticos. Tempos em milissegundos:

| Operação | Público | Assinaturas protegidas | Modelo integral |
|---|---:|---:|---:|
| Abrir/desbloquear | 1,424 | 116,199 | 116,250 |
| Salvar com autorização existente | 17,946 | 19,860 | 16,435 |
| Renderizar duas páginas, aquecido | 2,880 | 3,144 | 3,127 |
| Gerar 100 itens / 200 páginas PDF | 883,127 | 896,796 | 875,269 |
| Preview: 500 linhas, primeiras 4 faces | 242,048 | 190,751 | 198,363 |

A derivação de senha é medida no desbloqueio, fora do custo recorrente de render.
Os modos foram executados sequencialmente no mesmo processo; não interpretar
caches aquecidos e picos acumulados de RSS como comparação isolada entre modos.
A coleta completa chegou a 304.652 KiB de RSS. Este fixture pequeno não comprova
limite de memória para fotos grandes; o LRU tem testes próprios de orçamento,
concorrência e isolamento por copy-on-write.

Os PNGs de frente e verso dos dois modos protegidos são **idênticos byte a byte**
aos da referência inicial. O modo público corresponde à referência sem assinaturas.
Um asset invisível ausente foi retirado apenas da entrada sintética a empacotar;
a comparação com a referência original verifica que não muda os pixels.
Cada modo gerou 100 PDFs de duas páginas. Metadados tornam o hash do PDF inteiro
inadequado para comparação direta; contagem e conteúdo têm testes específicos.

### Evidências e limites visuais/de distribuição

- Inspeção das capturas sintéticas de workspace/editor em
  `.validation/fornax_stage4/visual/`; confirmou e orientou as correções de canvas
  e vínculo da máscara. Não é inspeção em display nativo de cada SO.
- IPC real entre processos Linux, incluindo caminhos Unicode, concorrente sem
  remoção do endpoint vivo e liberação ao fechar: bateria de **6 testes aprovada**
  em 0,68 s. Ativar com `FORNAX_RUN_NATIVE_IPC=1`; a suíte comum pula esse teste
  real por exigir sockets locais. Executado fora do sandbox com autorização.
- `desktop-file-validate` e `update-mime-database` aceitam os arquivos extraídos
  do manifesto em diretório isolado. Há aviso de múltiplas categorias principais
  do desktop, que pode duplicar entrada no menu; não é erro do formato MIME.
- Sintaxe do AppImage e compilação Python do script Nuitka verificadas. Isso não
  substitui empacotar, instalar e dar duplo clique. Clang exigido pelo script não
  está instalado neste ambiente; nenhum pacote Linux foi declarado aprovado.
- Windows/macOS, FAT/exFAT/rede, permissões/portais Flatpak, associação real e
  desempenho em máquina modesta continuam pendentes. Não foram instaladas
  associações nem alterada a biblioteca real do usuário.
- O fixture tem proporção entre pixels/mm diferente de 300 dpi: carregar a cena
  agora preserva os pixels. A apresentação de medidas/réguas em documentos desse
  tipo ainda precisa de conferência visual específica; o ajuste não reescreve
  todas as conversões físicas do editor.

### Retomada

Concluir a matriz nativa de instalação/abertura/reinício e filesystem nos sistemas
alvo; medir hardware modesto com o mesmo script e dados; conferir as medidas do
editor em modelos com DPI não padrão. Depois retomar 3.11 e o fechamento 4.5.
A revisão especializada independente continua não realizada.

### Resultado final dos testes locais

- Suíte geral `pytest tests`: **314 aprovados, 12 subtestes aprovados, 1 pulado**,
  em 141,23 s. O teste pulado é o IPC nativo, executado e aprovado separadamente
  na bateria de seis testes citada acima. Um aviso preexistente de API Qt obsoleta
  da tabela permanece; o código da tabela não foi alterado neste checkpoint.
- Bateria do editor (ciclo de vida, formas, camadas, texto, páginas, grupos e
  máscaras): **63 testes aprovados**, em 8,82 s.
- Adaptador/modelos e regressões novas: **7 aprovados**, em 1,56 s; incluídos
  também na suíte geral, portanto não somar os resultados como testes distintos.
- A primeira execução encontrou a expectativa antiga de IDs nulos no adaptador.
  O teste foi atualizado para validar IDs inteiros únicos e a preservação da
  origem; acrescentada cobertura de colisão com o ID do fundo. A suíte completa
  foi repetida após esse ajuste e passou.
- `git diff --check` e compilação dos módulos modificados passaram.

## Correção após teste real — ordem de camadas legada

O primeiro teste manual encontrou `layer_order inválido na página front` na
conversão. Causa reproduzida: a leitura v3 tolerava ausência/ordem incompleta,
mas `persistent_model_document()` removia o marcador interno de legado antes
de materializar uma ordem válida para v4. Os fixtures de migração anteriores
preenchiam essa lista manualmente e não cobriam o arquivo v3 bruto.

Correção: completar a ordem persistida usando as regras do renderer legado;
converter seu fundo separado para camada apenas no caminho que efetivamente o
desenhava. Manter a validação estrita dos documentos atuais. A origem não é
alterada pela normalização em memória; publicação/limpeza seguem a transação
já existente.

Novos testes partem de `template_v3.json` real sintético, sem ordem ou com
referências antigas/incompletas, nos três modos, e comparam os pixels após a
migração. Outro teste garante rejeição de documento atual sem `layer_order`.
Validação: 128 testes de migração/documento/contêiner/criptografia/persistência
aprovados; bateria complementar de migração/importação/renderização com 46
testes e 2 subtestes aprovados (há sobreposição). `git diff --check` passou.
A correção não conclui os gates nativos pendentes.

## Correção após abertura pela pasta da biblioteca

Ao abrir por duplo clique um `.fornax` que já pertencia à biblioteca, o fluxo
tratava o arquivo como externo e perguntava se deveria adicioná-lo novamente.
Agora o workspace procura primeiro o próprio arquivo e também reconhece uma
cópia com o mesmo `model_id` e a mesma `revision_id`; nesses casos apenas seleciona
o modelo existente. Uma revisão diferente continua no fluxo de importação para
não descartar silenciosamente uma atualização recebida.

O mesmo teste manual revelou um `readyRead` enfileirado depois que o Qt já havia
destruído o `QLocalSocket`. Os sinais agora usam o emissor vivo em vez de lambdas
que retinham o wrapper Python; a desconexão remove os callbacks e uma corrida
remanescente é encerrada sem acessar o objeto C++ apagado.

Validação: 17 testes de abertura, biblioteca e workspace aprovados; bateria real
de IPC e abertura externa com **9 testes aprovados** em 0,67 s. Inclui caminhos
Unicode, concorrência entre instâncias, liberação do endpoint, socket destruído,
arquivo já pertencente à biblioteca, cópia da mesma revisão e revisão nova.
