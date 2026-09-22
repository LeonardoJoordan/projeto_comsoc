# Revisão do FORNAX Forge: segurança, legado e licenças

Data: 21/09/2026. Base: branch `novo_main`, commit `d09a399a746ad1bf263d61f58c1b7e27f8989a43`.

## 1. Parecer executivo

O FORNAX já possui uma arquitetura predominantemente local e controles relevantes para proteger modelos: AES-256-GCM, Argon2id, validação de contêineres, sessões de autorização, recuperação criptografada e geração de conteúdo protegido sem cache intermediário aberto. Não foi identificada uma rotina de telemetria, atualização automática ou envio automático de documentos no código próprio examinado.

**Ainda não recomendo declarar a revisão de segurança ou a conformidade de distribuição concluídas.** Foram reproduzidas lacunas fora da criptografia e encontradas pendências documentais de publicação. As prioridades são:

1. Bloquear leitura de recursos externos pelo HTML dos modelos.
2. Limitar dimensões e orçamento de renderização de documentos recebidos.
3. Confinar nomes de saída também no fluxo de imposição.
4. Conciliar a licença do aplicativo com a redistribuição institucional autorizada pelo autor.
5. Entregar licenças, avisos e fontes correspondentes exigidos pelos componentes realmente distribuídos.
6. Documentar a origem e os direitos de redistribuição dos ícones.

Não foi demonstrada quebra do AES-GCM, recuperação de senha ou execução arbitrária de código. A ausência dessas demonstrações não constitui garantia de ausência de vulnerabilidades.

## 2. Escopo, método e limites

- Inventário e varredura estática dos 84 arquivos Python em `core/`, `features/`, `shared/` e `tools/`, totalizando aproximadamente 29.500 linhas, incluindo testes existentes dentro do editor.
- Leitura dirigida dos fluxos de importação, migração, sessão, criptografia, persistência, renderização, logs, recursos e empacotamento. A varredura ampla não equivale a uma auditoria formal linha a linha de todas as dependências nativas.
- Conferência de `main.py`, requisitos, documentação vigente, assets e scripts Nuitka, AppImage, Flatpak e Inno Setup.
- Inventário dos pacotes instalados em `.venv` e consulta a textos oficiais de licenciamento.
- Ensaios com dados fictícios e diretórios temporários. Nenhuma assinatura real foi usada. O ensaio de dimensões extremas validou somente a aceitação do arquivo, sem tentar alocar sua imagem.
- Código de produção, testes e instaladores não foram alterados nesta revisão. Este relatório é o artefato entregue.

**Limites:** não foram reconstruídos ou auditados os binários finais de Windows/macOS/Flatpak/AppImage; não houve captura de rede do aplicativo instalado, auditoria dos servidores GitHub, varredura completa do histórico Git por segredos, fuzzing extensivo ou consulta automatizada integral de CVEs. Não se pode concluir “zero vulnerabilidades conhecidas” com estes resultados. `pip check` verifica compatibilidade de requisitos, não vulnerabilidades.

Este documento é uma revisão técnica de conformidade e riscos, não certificação, homologação governamental nem parecer jurídico sobre toda a legislação aplicável.

## 3. Segurança e privacidade

### S1 — HTML de modelo consegue carregar imagem local fora do pacote

**Prioridade: alta. Situação: reproduzida.**

Evidências: `core/text_layout.py`, função `build_document` (a partir da linha 115); `core/fornax_container.py`, `open_public_fornax` e `_document_asset_references`; `features/generator/renderer.py`.

O carregador valida os caminhos de imagens, assinaturas e fundos declarados nas coleções do documento, mas o HTML das caixas de texto chega a um `QTextDocument` comum. A limpeza remove links `<a>` e alguns estilos; não bloqueia `<img src="file:///...">` nem implementa uma política de recursos do documento.

Ensaio: foi criada uma pequena imagem fictícia fora do `.fornax`; uma caixa recebeu uma referência `file://` para essa imagem. O arquivo passou por `save_public_fornax` e `open_public_fornax`. Após construir o documento de texto, o recurso era um `QPixmap` válido carregado do disco.

Impacto: um modelo recebido pode incorporar ao conteúdo renderizado uma imagem local acessível ao usuário sem que ela esteja nos assets aprovados. O eventual compartilhamento do resultado pode expor essa imagem. Não foi demonstrado envio pela rede ou leitura de qualquer arquivo de texto; a prova é de carregamento de imagem local. Caminhos UNC no Windows e outros tipos de recursos exigem testes específicos.

Solução: definir uma política única de HTML/recursos para editor, prévia e geração. Para caixas exclusivamente textuais, rejeitar imagens, objetos e referências externas, preservando a formatação permitida. Bloquear carregamento externo também em `loadResource`, para não depender apenas de expressões regulares. Testar caminhos absolutos, relativos, `file://`, UNC e recursos de CSS.

Aceite: o mesmo pacote não carrega recursos locais externos nem origina acesso de rede por referências do HTML; formatação rica e placeholders continuam funcionando.

### S2 — Dimensões de documento sem limite de alocação

**Prioridade: alta. Situação: aceitação indevida reproduzida; esgotamento de memória não provocado.**

Evidências: `core/model_document.py:88`, `_validate_dimensions`; `features/generator/renderer.py`, `pre_render_static_base` e `render_preview_image`; `features/generator/imposition.py`.

A validação exige dimensões positivas e finitas, mas não um máximo por lado ou área total. O limite de 64 milhões de pixels aplicado a assets em `core/fornax_container.py` não limita a área do documento. Um `.fornax` com `canvas_size` de 1.000.000 × 1.000.000 foi salvo e aberto com sucesso. Não foi renderizado.

Impacto: um arquivo pequeno pode solicitar uma imagem de aproximadamente 4 TB a quatro bytes por pixel, antes de considerar cópias e workers. Dependendo do caminho e do Qt, pode ocorrer rejeição tardia, travamento, erro ou pressão excessiva de memória. Não afirmamos que todos os caminhos alocam esse total.

Solução: limites explícitos para pixels por lado/área, dimensões físicas e resolução efetiva de saída; validar inteiros onde o Qt os exige; limitar também geometria de objetos e configurações de imposição. Calcular orçamento por trabalho e concorrência antes de renderizar.

Aceite: modelos fora dos limites são recusados com mensagem controlada antes de construir imagens ou abrir o editor.

### S3 — Nome de saída não confinado no modo de imposição

**Prioridade: média. Situação: destino fora da pasta reproduzido sem escrever arquivos.**

Evidências: `features/generator/manager.py`, `_start_imposition_mode`, variável `safe_pattern`; `features/generator/workers.py`, `PageRenderWorker.run`; `features/generator/export_dialog.py`, `_on_accept`/atribuição de `result_pattern`; `core/naming_engine.py`.

No fluxo individual, `build_output_filename` sanitiza o nome. Na imposição, o programa apenas retira `{` e `}` do padrão e concatena `_Folha_...`. O nome resultante é unido ao diretório de saída. O ensaio com `../outside` e worker substituído por um observador confirmou destino fora da pasta do trabalho.

Impacto: padrão digitado ou reaproveitado nas preferências pode causar falha, gravação em local inesperado ou sobrescrita de saída existente fora da pasta da forja. O padrão vem da configuração do usuário; não foi demonstrado que um modelo importado sozinho controla esse parâmetro. Por isso, o risco não é classificado como execução remota ou comprometimento automático.

Solução: reutilizar a mesma sanitização em todos os fluxos e validar o destino resolvido antes de gravar. Tratar nomes reservados do Windows, colisões sem distinção de maiúsculas/minúsculas e nomes excessivamente longos.

Aceite: padrões absolutos, `../`, separadores e nomes reservados não escapam do diretório autorizado nem sobrescrevem arquivos externos.

### S4 — Imagens variáveis podem atravessar a pasta por link simbólico

**Prioridade: média. Situação: reproduzida no Linux.**

Evidência: `core/dynamic_images.py`, `resolve_dynamic_image`.

A função rejeita caminho absoluto e `..`, mas aceita um arquivo dentro da pasta que seja link simbólico para uma imagem fora dela. O ensaio retornou `status='ok'` para esse caso.

Impacto condicionado: alguém precisa conseguir criar ou fornecer esse link na pasta selecionada. A leitura respeita os privilégios do usuário do aplicativo, mas viola a expectativa de limitar a busca à pasta autorizada. Junctions e links Windows não foram ensaiados.

Solução: resolver raiz e candidato e exigir contenção do destino real; definir política explícita para links. Se o cenário incluir alterações concorrentes por terceiros, reduzir também a janela entre validação e abertura.

Aceite: link externo é recusado; imagem normal e subpasta permitida continuam funcionando.

### S5 — Dados persistidos precisam ser documentados; logs sem retenção

**Prioridade: média. Situação: confirmada por código.**

Evidências: `shared/log_panel.py:23` (`append`), `features/workspace/main.py:55` (crash log), `features/generator/manager.py` (`_on_direct_card_finished`), `core/paths.py`, `core/settings.py`.

`app.log` recebe mensagens e nomes dos arquivos gerados. Se o padrão usa `{nome}`, esses nomes também permanecem no log. `crash_log.txt` recebe exceções e caminhos. Não há rotação ou limite de retenção nesses gravadores; limpar o painel visual não apaga o log em disco.

Não foi encontrada persistência automática integral das células da tabela nos caminhos examinados. Isso não significa ausência de dados pessoais persistidos: materiais gerados, conteúdo dos modelos, nomes de arquivos e mensagens podem contê-los.

Solução: política documentada de dados locais, rotação/tamanho máximo e revisão dos campos registrados; preferir contadores e identificadores não sensíveis quando nomes não forem necessários. Documentar como limpar logs, backups e temporários. Isso não exige telemetria ou conexão.

### Mapa de dados observado

| Dado | Local/comportamento | Proteção e observação |
|---|---|---|
| Modelos | `get_app_data_dir()/models` | `.fornax` público, assinaturas protegidas ou proteção integral, conforme escolha |
| Backup | `.fornax.bak` junto ao modelo | Publicador trata aumento de proteção/troca de senha para não manter backup anterior aberto nesse fluxo |
| Recuperação do editor | Contêiner lateral via `FornaxSessionManager.write_recovery` | Usa modo da sessão, inclusive criptografia quando protegido |
| Preferências | `QSettings` do FORNAX | Caminhos recentes, pasta de fotos, seleção, geometria, padrões; sem senha gravada encontrada |
| Logs | Diretório `logs` | Texto aberto, sem retenção automática identificada |
| Prévia de `.fornax` | Memória e snapshots autorizados | `_load_fornax_document` evita cache aberto de modelo protegido |
| Cache legado | `.render_cache` em diretórios antigos | Miniaturas/proxies em disco; não confundir com cache do contêiner protegido |
| Importação/exportação | Diretórios temporários `fornax_import_*`, `fornax_export_*`, etc. | Contêineres temporários; limpeza normal via contexto, interrupção abrupta pode deixar resíduos |
| PDF agrupado público | `.temp_hybrid` na pasta de saída | Imagens intermediárias; revisar limpeza após término abrupto |
| PNG/PDF final | Pasta escolhida pelo usuário, por forja | A proteção do modelo não criptografa o material final |
| Chaves e assets desbloqueados | Memória do processo | Chave retida em sessão; descarte lógico não garante zerar todas as cópias do runtime, swap ou dumps |

No Linux, a base padrão é `$XDG_DATA_HOME/com.leobelisario.FornaxForge` ou `~/.local/share/com.leobelisario.FornaxForge`; no Windows, `%APPDATA%/FornaxForge`; no macOS, `~/Library/Application Support/com.leobelisario.FornaxForge`. Sandboxes podem mudar a localização física.

### Controles positivos e limites de proteção

- `core/fornax_container.py:683`: Argon2id com 64 MiB, três iterações, uma lane, saída de 32 bytes; senha normalizada em NFC de 8–64 caracteres. A derivação é serializada por processo para conter picos simultâneos.
- `_encrypt_payload`: salt aleatório, chave de dados aleatória de 32 bytes e nonces de 12 bytes; AES-GCM autentica payload e contexto do cabeçalho. Não foi encontrada criptografia ZIP tradicional como mecanismo de proteção.
- `_validated_inventory`, `_strict_json` e `_read_inner_zip`: limites de bytes, entradas e complexidade JSON; rejeição de caminhos inseguros, duplicatas e symlinks do ZIP. SVG possui verificações próprias. Isso não cobre automaticamente o HTML descrito em S1.
- Sessão guarda a chave derivada, não a senha em preferências. A tolerância de 300 segundos começa ao sair do modelo; não é bloqueio por inatividade enquanto ele continua ativo. Esse comportamento corresponde às decisões anteriores, não é apontado como defeito.
- Alteração autenticada da parte pública gera sinalização após desbloqueio. Sem a senha, não se pode prometer autenticar a parte pública contra a referência criptografada.
- `_publish_package_locked` verifica escrita temporária e preserva recuperação. `legacy_migration.py` usa inventário, hashes e estados de migração antes da limpeza.
- `RenderManager` usa caminho sem intermediários abertos para geração protegida. A mensagem “PDF protegido” nesse fluxo merece esclarecimento futuro: descreve o tratamento interno, não uma senha aplicada ao PDF final.
- `core/app_instance.py` usa IPC local com acesso do usuário e limites de mensagem/clientes. Importar `QtNetwork` aqui não significa conexão à internet.

Senhas de modelo não substituem segurança do sistema operacional, não protegem arquivos finais já gerados e não impedem capturas por quem está autorizado. Esses limites devem ser documentados, sem retirar as funcionalidades aprovadas nem obrigar proteção onde o usuário optou por modelo público.

### S6 — Evidências de release e manutenção ainda incompletas

**Prioridade: média; concluir antes de anunciar maturidade verificada.**

`requirements.txt` fixa dependências centrais, mas deixa Nuitka e zstandard com mínimos abertos. Não há lock completo com hashes nem SBOM próprio do release. O manifesto Flatpak instala pacotes com `pip` durante o build. Não há `.github/` com verificações automatizadas nesta árvore, nem `SECURITY.md` ou política pública de privacidade.

Não foram localizadas etapas de assinatura de artefatos nos scripts examinados. Isso não prova que nenhum release tenha sido assinado manualmente. As configurações remotas do GitHub não foram auditadas.

Recomendação: builds limpos com versões/hashes registrados, SBOM por plataforma, testes e varreduras de dependências/segredos, canal de relato privado, documentação de suporte e assinatura verificável dos releases. O aplicativo pode continuar totalmente offline; essas verificações pertencem ao desenvolvimento/distribuição.

O Flatpak não concede `--share=network` em `finish-args`; a permissão aparece somente no build. Essa é uma evidência favorável, mas o runtime GNOME 47 e todos os componentes precisam de verificação de suporte/atualizações antes do release. Não se afirma aqui que o runtime foi testado ou está atualizado.

## 4. Referências antigas e desacoplamento do COMSOC

### L1 — Compatibilidade preservada corretamente

`core/paths.py` mantém `LEGACY_APP_ID`, `LEGACY_WINDOWS_APP_DIR` e `.comsoc-migration.json`; `core/settings.py` mantém o namespace antigo e o marcador de migração. Testes cobrem a migração.

**Não remover ou renomear esses identificadores por estética.** Eles localizam dados reais antigos e evitam repetição da migração. Não são evidência de que o editor legado continua sendo usado. Os caminhos ativos examinados usam `features/editor`, `features/workspace` e o identificador FORNAX.

### L2 — Documentação atual ainda descreve menus e distribuição antigos

**Prioridade: média.**

- `README.md:64` ainda orienta “Programa > Temas”, mas a interface atual usa Configurações.
- `README.md:70` usa “Modelo > Importar modelos” para o FORNAX; a interface atual usa Arquivo. A instrução relativa ao COMSOC antigo pode permanecer se identificada como histórica.
- `docs/MODELOS_FRENTE_VERSO.md:42` ainda apresenta ZIP com documento/assets como orientação geral, enquanto o fluxo atual distingue `.fornax` individual e ZIP de lote.
- `assets/icons/ui/README.md` é um pedido antigo de aquisição de ícones, incluindo nomes que não correspondem ao inventário atual. Não é catálogo de autoria/licenças.
- `README.md` diz que a licença própria ainda será definida, mas existe uma EULA restritiva já conectada ao instalador.

Solução: revisar documentação vigente contra o comportamento atual e marcar/arquivar o material que só descreve etapas anteriores. Não apagar a história de autoria.

### L3 — URLs do repositório antigo ainda são as oficiais configuradas

**Prioridade: baixa agora; obrigatória na mudança final.**

`instalador.iss:15–17` e `docs/EULA-pt-BR.txt:37` apontam para `LeonardoJoordan/projeto_comsoc`.

Enquanto não existir repositório novo, esses endereços não são necessariamente incorretos. Preparar uma lista de substituição e atualizá-los somente na migração final. Preservar `AppId` do Inno Setup, identificador FORNAX e caminhos de dados para não quebrar atualização/associações.

### L4 — Resíduos locais e material de desenvolvimento

**Prioridade: baixa, com cuidado de publicação.**

Na pasta de trabalho existem `Linux_Projeto_COMSOC.flatpak`, `Projeto_ComSoc.AppImage`, caches do Flatpak com identificadores antigos, `build-dir/`, `repo/`, ambientes virtuais e `models/`. Os filtros Git examinados excluem os artefatos principais e `git ls-files models` não listou modelos reais rastreados.

Isso diferencia **resíduo no disco** de **conteúdo que será publicado**. Não copiar a pasta de trabalho inteira para o novo repositório. Usar seleção do conteúdo versionado e revisar o histórico separadamente. Os fixtures rastreados identificados são arquivos de referência de teste; não foram usados modelos particulares nos ensaios.

O build copia `assets/` inteiro, incluindo `assets/icons/ui/README.pdf` e documentação de trabalho. O Nuitka inclui o pacote `features` inteiro, que contém módulos de teste do editor. Não foi comprovada sua presença no binário final, mas convém excluir material de teste/planejamento da seleção de release e verificar o relatório de compilação.

`history/` e `docs/historico/` contêm referências legítimas ao COMSOC. Manter como história ou arquivar fora da apresentação principal é uma decisão editorial, não uma correção de segurança.

**Conclusão do desacoplamento:** a separação funcional já avançou; os achados atuais concentram-se em documentação, material de distribuição e compatibilidade deliberada. Não há fundamento nesta revisão para refazer a refatoração inteira.

## 5. Licenças, autoria e redistribuição

### J1 — EULA atual contradiz a distribuição institucional pretendida

**Prioridade: alta; bloqueador documental de publicação com a promessa de redistribuição livre.**

`docs/EULA-pt-BR.txt`, seções 1 e 2, concede licença limitada, intransferível e revogável e proíbe redistribuição. `instalador.iss` a apresenta via `LicenseFile`. Portanto, um órgão não recebe hoje uma autorização inequívoca para distribuir cópias a toda a estrutura.

Solução: o autor deve escolher uma licença reconhecida compatível com suas intenções (MIT é uma opção, não uma escolha já efetuada) ou validar termos próprios adequados. Conciliar LICENSE, EULA, README, Sobre e documento de uso institucional. Declarar claramente gratuidade, permissões de cópia/instalação/distribuição, condições de preservação dos avisos, suporte e ausência de endosso institucional.

A autoria pode ser identificada sem reivindicar autoria das bibliotecas/assets de terceiros. O histórico deve ser preservado. A declaração do autor sobre desenvolvimento independente foi recebida, mas esta revisão não verifica titularidade jurídica ou realiza registro no INPI.

### J2 — Textos integrais e fontes correspondentes não estão garantidos pelos builds

**Prioridade: alta; bloqueador de aprovação documental do pacote.**

- `docs/THIRD_PARTY_LICENSES.md` é um inventário/checklist, não substitui as licenças integrais.
- `instalador.iss`, seção `[Files]`, adiciona EULA, inventário e aviso, mas não referencia uma coleção completa de GPL/LGPL/PSF/Apache/BSD e avisos dos componentes.
- `script_nuitka.py` inclui `assets`, mas não uma pasta de licenças ou coleta dos metadados legais das dependências.
- `script_appimage.sh` reaproveita o standalone sem completar os avisos.
- O Flatpak copia código e assets; não copia `docs/THIRD_PARTY_LICENSES.md` nem o conjunto documental do aplicativo.
- A interface informa que os textos completos “serão incluídos”; isso é uma pendência, não prova de entrega.
- Não foi encontrado arquivo de fontes correspondentes do Qt/PySide por versão, nem oferta operacional detalhada e verificável vinculada ao release. Um link genérico para o projeto upstream não demonstra, por si só, cumprimento da obrigação do distribuidor.

Algum binário pode conter textos trazidos automaticamente por ferramentas, mas isso não foi inventariado nem testado nesta revisão. Não se afirma que todo pacote existente esteja sem qualquer licença; afirma-se que o processo atual não comprova a cobertura exigida.

Solução: montar `licenses/` a partir do inventário real, preservando copyrights e textos; entregar em todos os formatos; arquivar fontes correspondentes e instruções necessárias segundo a opção legal de distribuição escolhida. Validar o pacote instalado, não apenas a árvore do projeto.

### Inventário observado no ambiente Linux

As versões abaixo são do ambiente `.venv`, não uma declaração das versões de um instalador Windows ou de outro release.

| Componente | Versão observada | Licença/obrigação a verificar na distribuição |
|---|---|---|
| Python | 3.13.11 | PSF e avisos históricos/terceiros aplicáveis ao runtime distribuído; conservar textos e copyrights |
| PySide6, Essentials, Addons, Shiboken6 | 6.11.0 | Metadados oferecem LGPL-3.0-only ou alternativas GPL; adotar LGPL para componentes elegíveis, com as condições abaixo |
| Qt usado pelo código | Core, Gui, Widgets, Network, Svg | Verificar licenças por módulo, plugins e bibliotecas nativas do pacote; QtTest aparece nos testes |
| pypdf | 6.14.2 | BSD-3-Clause; conservar copyright, condições, disclaimer e não usar autores para endosso |
| cryptography | 50.0.1 | Apache-2.0 OU BSD-3-Clause para código próprio; registrar opção e cumprir também licenças dos componentes incorporados |
| cffi | 2.1.1 | MIT-0 nos metadados/texto instalado, diferente de “MIT” no inventário atual; conferir componentes nativos separadamente |
| pycparser | 3.0 | BSD-3-Clause; preservar avisos se distribuído |
| OpenSSL incorporado a cryptography | 4.0.2 | Identificado pelo backend e SBOM do wheel; aplicar licença/avisos correspondentes, sem presumir que seja o OpenSSL 3.x do inventário Windows |
| OpenSSL do Python local | 3.0.13 | Componente distinto; sua inclusão e origem no release dependem do pacote/plataforma |
| Crates Rust de cryptography | 39 entradas no SBOM Rust | Incluem MIT, Apache-2.0, BSD-3-Clause, Unicode-3.0 e Apache-2.0 com LLVM-exception, entre expressões alternativas; inventariar o conteúdo efetivamente incorporado |
| Nuitka | 4.0.7 | AGPLv3 com `LICENSE-RUNTIME.txt` para o runtime coberto; a exceção permite saídas com outra licença, sem tornar automaticamente o FORNAX AGPL |
| zstandard | 0.25.0 | Metadados BSD-3-Clause; biblioteca nativa incorporada exige inventário se for distribuída; aqui é ferramenta de build declarada |
| Inter estática | Arquivos `Inter_18pt-*` | SIL OFL 1.1; `assets/fonts/ui/OFL.txt` existe e acompanha cópia integral de assets |
| Ícones SVG/PNG/ICO | Arquivos do projeto | Origem e licença não documentadas de forma suficiente; ver J4 |
| libffi, SQLite, codecs/fontes/terceiros do Qt | Dependem do binário | Não basta o nome do wheel; levantar versões, licenças e avisos com SBOM e inspeção do pacote |
| Runtime Microsoft Visual C++ | Não auditado neste Linux | Conferir arquivos redistribuíveis e termos da ferramenta que os fornece no build Windows |

Pacotes de desenvolvimento também observados: pytest 9.0.3 (MIT), pytest-qt 4.5.0 (MIT), pluggy 1.6.0 (MIT), iniconfig 2.3.0 (MIT), packaging 26.2 (Apache-2.0 ou BSD-2-Clause), Pygments 2.20.0 (BSD-2-Clause), typing_extensions 4.15.0 (PSF-2.0) e pip 25.3 (MIT). Não há razão para distribuí-los automaticamente só por estarem no ambiente. Confirmar sua ausência no pacote final ou adicionar seus avisos se presentes.

### J3 — Inventário atual generaliza componentes que exigem tratamento específico

**Prioridade: alta para fechar o release; não implica que o código autoral precise mudar de licença.**

`docs/THIRD_PARTY_LICENSES.md` está orientado a uma compilação Windows anterior. O ambiente atual demonstra cffi MIT-0 e OpenSSL 4.0.2 dentro de cryptography. Também há runtime Nuitka incorporável e dependências Rust que não aparecem nominalmente na tabela existente.

O manifesto Flatpak instala o metapacote `PySide6`, que depende de Addons. No ambiente equivalente estão presentes bibliotecas como QtGraphs e QtQuick3D, embora os imports produtivos examinados não as usem. Alguns desses módulos não oferecem LGPL na modalidade comunitária. Redistribuir um componente GPL sem utilizá-lo não prova automaticamente que o aplicativo inteiro seja derivado dele, mas cria obrigações sobre esse componente. Não classificar todo Addons como “somente LGPL”.

Solução: minimizar os módulos empacotados e gerar inventário por artefato. Para cada componente, registrar nome, versão, hash, origem, licença escolhida, arquivos de aviso, fonte correspondente e justificativa de inclusão. O conjunto deve corresponder ao binário distribuído, não apenas a `requirements.txt`.

### Obrigações práticas do Qt/PySide sob LGPLv3

1. Informar o uso das bibliotecas e conservar autoria/avisos aplicáveis.
2. Entregar os textos da LGPLv3 e GPLv3 exigidos pela LGPL.
3. Usar um mecanismo de bibliotecas compartilhadas adequado, ou cumprir a alternativa de fornecer os materiais para recombinação/relink conforme a licença. No standalone atual há intenção de bibliotecas separadas; falta validação de substituição no artefato instalado.
4. Não restringir as modificações das partes cobertas nem engenharia reversa necessária à depuração dessas modificações.
5. Quando distribuir binários das bibliotecas, cumprir o fornecimento de fonte correspondente pela modalidade aplicável. Se optar por oferta escrita, cumprir duração e destinatários exigidos pela GPL incorporada à LGPL; não presumir que basta “peça ao autor” ou apontar a homepage.
6. Incluir informações de instalação quando exigidas e tratar patches/modificações nas bibliotecas de acordo com a licença.
7. Auditar componentes GPL exclusivos e licenças dos terceiros do Qt separadamente.

Essas condições não obrigam a enviar o código autoral do FORNAX à Qt nem, automaticamente, a licenciá-lo sob LGPL. O FORNAX pode ter licença própria compatível com a forma de integração. A avaliação final depende também do empacotamento. [Texto LGPLv3, especialmente seção 4](https://doc.qt.io/qt-6/lgpl.html), [licenciamento e terceiros Qt](https://doc.qt.io/qt-6/licensing.html).

### J4 — Proveniência dos ícones não comprovada

**Prioridade: alta para redistribuição pública. Situação: pendência de evidência, não acusação de infração.**

`assets/icons/ui/README.md` pede licença que permita redistribuição, mas não registra autores, URLs de obtenção, licença, atribuições ou comprovantes. Metadados de Inkscape e nomes de arquivos não provam autorização. O mesmo cuidado vale para a identidade visual em PNG/ICO.

Solução: produzir inventário por arquivo ou conjunto, com origem, autor, licença e evidência da obtenção. Se forem desenhos próprios, registrar isso; se vierem de serviço de ícones, guardar a licença aplicável ao download e cumprir atribuição/termos. Substituir somente arquivos cuja autorização não possa ser estabelecida.

Para Inter, a situação é melhor: o texto OFL e o crédito dos autores estão presentes. Manter esses arquivos e observar nomes reservados se houver modificação; a OFL não se transfere aos documentos criados usando a fonte. [Texto oficial OFL](https://openfontlicense.org/open-font-license-official-text/).

### J5 — Limites do parecer de conformidade

Esta revisão identifica obrigações técnicas e lacunas de evidência. Não comprova autoria exclusiva de cada linha/asset, não examina contratos externos e não certifica adequação integral à LGPD ou a regras particulares de cada órgão. Uso offline continua podendo tratar dados pessoais. A instituição define o uso dos dados; o projeto deve explicar o comportamento do software de forma verificável.

Não há necessidade técnica de criar login, telemetria ou atualização automática para resolver as pendências identificadas. A licença oficial deve autorizar com clareza a redistribuição pretendida e preservar os direitos de terceiros.

## 6. Verificações e reprodução

### Ensaios dirigidos realizados

| Ensaio | Resultado |
|---|---|
| `.fornax` com HTML apontando para PNG local sintético | Aceito; `QTextDocument` carregou `QPixmap` válido externo ao pacote |
| Imagem variável via symlink para fora da pasta | Aceita com `status='ok'` |
| Canvas 1.000.000 × 1.000.000 | Aceito pelo salvamento e abertura; não renderizado |
| Padrão `../outside` na imposição | Planejou caminho fora da pasta; worker de escrita foi substituído por observador |
| `.venv/bin/python -m pip check` | Sem requisitos quebrados; não é auditoria de CVEs |

Para reproduzir S1 com segurança: criar PNG fictício em diretório temporário; usar sua URI em `<img>` dentro de `pages[0].boxes[0].html`; salvar/abrir o contêiner; construir texto com `build_document`; consultar recurso de imagem após layout. Nunca usar imagem real de assinatura.

Para S2: alterar apenas `canvas_size` de um fixture válido, salvar e reabrir; não chamar renderização. Para S3: substituir `PageRenderWorker` por observador e inspecionar o destino resolvido. Para S4: criar symlink de teste dentro da pasta autorizada para outro PNG temporário.

### Suíte automatizada

A coleta padrão `pytest -q tests features/editor` encontrou sete erros de importação relativa dos testes do editor. Foi usado `--import-mode=importlib` para coletá-los corretamente. Isso é uma questão de configuração da suíte; não evidência de sete crashes do aplicativo.

Comando da execução abrangente:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest --import-mode=importlib -q tests features/editor --disable-warnings --maxfail=8
```

Resultado: **423 testes aprovados, 1 ignorado, 1 warning e 12 subtestes aprovados**, em 296,98 segundos. O warning foi contabilizado pela execução, cujo detalhamento foi suprimido pela opção `--disable-warnings`; não foi classificado como falha ou descartado como inofensivo nesta revisão.

O teste de IPC nativo exige `FORNAX_RUN_NATIVE_IPC=1` e não deve ser contabilizado como aprovado se ignorado. Testes offscreen não certificam instalação nativa, renderização em impressora real, tráfego de rede ou conformidade legal.

## 7. Sequência recomendada de resolução

| Ordem | Trabalho | Condição de conclusão |
|---|---|---|
| 1 | S1 e S2: fronteiras do conteúdo recebido e limites gráficos | Ensaios negativos passam; editor/prévia/geração preservam formatação normal |
| 2 | S3 e S4: caminhos de saída e imagens variáveis | Nenhuma saída/leitura fora do escopo autorizado nos casos reproduzidos |
| 3 | S5: mapa de dados e retenção | Documentação corresponde ao comportamento; logs têm política definida |
| 4 | J1 e J4: licença própria e origem dos assets | Redistribuição institucional claramente autorizada; direitos dos ícones comprovados |
| 5 | J2/J3/S6: inventário, builds e evidências | Cada pacote tem avisos, fontes aplicáveis, versões/hashes e validação da integração LGPL |
| 6 | L2–L4: documentação e apresentação final | Textos atuais corretos; compatibilidade preservada; só conteúdo deliberado será publicado |
| 7 | Validação dos artefatos e novo repositório | Pacotes específicos identificados e aprovados; novo repositório criado somente no passo final autorizado |

Esta ordem não reabre o escopo funcional nem exige refazer o programa. Corrige problemas demonstrados e fecha obrigações de distribuição.

## 8. Fontes e evidências de licenciamento

Referências oficiais consultadas em 21/09/2026; arquivar a versão aplicável a cada release, pois páginas “latest” podem mudar.

- [Qt: opções de licença, módulos e SBOM](https://doc.qt.io/qt-6/licensing.html).
- [Texto LGPLv3 publicado pelo Qt](https://doc.qt.io/qt-6/lgpl.html).
- [Qt: obrigações GPL/LGPL](https://www.qt.io/development/open-source-lgpl-obligations).
- [Qt for Python](https://doc.qt.io/qtforpython-6).
- [Python: histórico e licenças](https://docs.python.org/3/license.html) — entregar a versão do runtime efetivamente distribuído.
- [pypdf: licença oficial](https://github.com/py-pdf/pypdf/blob/main/LICENSE).
- [Nuitka: exceção do runtime](https://github.com/Nuitka/Nuitka/blob/main/LICENSE-RUNTIME.txt), também lida em `.venv/lib/python3.13/site-packages/nuitka-4.0.7.dist-info/licenses/LICENSE-RUNTIME.txt`.
- [SIL OFL: texto oficial](https://openfontlicense.org/open-font-license-official-text/), comparado ao arquivo local da Inter.
- Evidência local cryptography: `cryptography-50.0.1.dist-info/licenses/`, `sboms/sbom.json` e `sboms/cryptography-rust.cyclonedx.json`, sob `site-packages` de `.venv`.
- Evidência local cffi: `cffi-2.1.1.dist-info/licenses/LICENSE`; inventário por `importlib.metadata`.

Os itens marcados como pendentes devem continuar pendentes até existir evidência. Nem a existência deste relatório nem o sucesso dos testes autoriza declarar o software “certificado”, “sem vulnerabilidades” ou “integralmente conforme a legislação”.
