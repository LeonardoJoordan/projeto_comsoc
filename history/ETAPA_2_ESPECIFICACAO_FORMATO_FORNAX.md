# Etapa 2 — Especificação do formato .fornax v1

Data: 20/09/2026. Estado: especificação dos checkpoints 2.1–2.4 concluída; implementação do aplicativo não iniciada.

Este documento é normativo para a Etapa 3, em conjunto com as decisões de produto do plano principal. O experimento isolado não é uma implementação pronta do formato nem uma auditoria independente. Compatibilidade de instaladores Windows/macOS e desempenho de máquinas modestas serão validados na Etapa 4; não foram demonstrados pelo experimento Linux.

## 2.1 — Estrutura e contratos de acesso

### Identidades e versões

- Contêiner `format="fornax"`, `version=1`; documento interno permanece JSON v4. Não incrementar esquema gráfico por mudar envelope.
- `model_id` e `revision_id`: UUIDv4 em formato ASCII minúsculo com hífens. Salvar mantém identidade e cria revisão; renomear também é revisão. Duplicar, criar cópia sem assinatura e incorporar cópia recebida cria nova identidade. Exportação é cópia com nova identidade para não confundir sessões locais.
- Nunca inferir identidade pelo nome/slug. Biblioteca pode guardar `<model_id>.fornax`, exibindo o nome interno após leitura permitida; integral bloqueado usa nome do arquivo ou rótulo local fornecido pelo usuário, sem publicar nome interno no cabeçalho.
- Versão ou modo desconhecido: rejeitar explicitamente, sem tentar abrir como desprotegido. v1 só admite as entradas e campos descritos; extensões obrigatórias futuras exigem nova versão.

### Entradas do ZIP externo

| Modo | Entradas permitidas |
|---|---|
| `none` | `manifest.json`, `public/document.json`, `public/assets/<uuid>.<ext>` |
| `signatures` | anteriores + `protected.bin` |
| `full` | somente `manifest.json` e `protected.bin` |

Sem miniatura interna nesta primeira versão; miniaturas públicas derivadas são cache externo. Arquivos de assinatura ou metadados de suas camadas não podem aparecer em `public/`. Não embutir backup nem dados da tabela no contêiner. Pastas de imagens variáveis permanecem preferências locais.

Modo `none` é inválido se o documento contiver assinaturas. Remover o bloco de um pacote parcial produz pacote inválido; a cópia pública é criada pelo fluxo explícito sem assinaturas, com nova identidade. Isso não impede terceiros de copiar conteúdo público, que é público por decisão de produto.

Todos os paths internos são POSIX relativos e ASCII, emitidos pelo programa. Nome original do asset é metadado do documento no mesmo âmbito de proteção do objeto. Nunca usar o nome de arquivo fornecido pelo pacote como destino de extração. Referências do documento lógico usam IDs de asset; a fronteira de armazenamento resolve-os, não o renderer por concatenação de paths.

### Manifestos exemplificativos

Sem proteção (exemplo válido de cabeçalho; documento público acompanha):

```json
{"header":{"format":"fornax","version":1,"mode":"none","model_id":"11111111-1111-4111-8111-111111111111","revision_id":"22222222-2222-4222-8222-222222222222"}}
```

Protegido (exemplo de estrutura, `wrapped_key_hex` precisa dos 48 bytes reais):

```json
{
  "header": {
    "format": "fornax", "version": 1, "mode": "signatures",
    "model_id": "11111111-1111-4111-8111-111111111111",
    "revision_id": "22222222-2222-4222-8222-222222222222",
    "crypto_profile": "a2id-64m-t3-p1-aes256gcm-v1",
    "salt": "000102030405060708090a0b0c0d0e0f",
    "wrap_nonce": "000102030405060708090a0b",
    "payload_nonce": "0c0d0e0f1011121314151617"
  },
  "wrapped_key_hex": "<48 bytes em 96 caracteres hexadecimais>"
}
```

Em `full`, apenas o campo `mode` muda; conteúdo inteiro fica cifrado. Bytes acima são exclusivamente ilustrativos/vetores públicos, nunca valores para produção.

### Conteúdo do bloco protegido

`protected.bin` decifra para um ZIP interno limitado, processado em memória, sem extração livre.

- `full`: `document.json` (documento completo v4) e `assets/<uuid>.<ext>` (todos os assets incorporados), sem cópia pública.
- `signatures`: `signatures.json` + `assets/<uuid>.<ext>` exclusivamente destinados às assinaturas.
- ZIP interno não pode conter outros ZIPs. Entradas cifradas externas usam ZIP_STORED para evitar recompressão inútil. Documentos/assets usam ZIP_STORED ou DEFLATED dentro dos limites.

Estrutura lógica de `signatures.json`:

```json
{
  "version": 1,
  "public_reference": [{"path":"public/document.json","sha256":"<64 hex>"}],
  "pages": [{
    "page_id":"front",
    "signatures":[{"object_id":"signature:visible","signature_id":"sig-stage1-visible","path":"assets/<uuid>.svg","visible":true}],
    "original_layer_order":["shape:background-front","signature:visible"],
    "public_object_ids":["shape:background-front"]
  }],
  "protected_origin_info": null
}
```

Exemplo abreviado: cada assinatura conserva TODOS os atributos originais (geometria, visibilidade, opacity, nome, locked, group_id etc.). `public_reference` enumera documento e todos os assets públicos válidos, ordenados por path. IDs de assinatura são globais; IDs de objetos são identificados pelo par página/objeto.

### Separação e reconstrução

1. Normalizar v3/v4 usando adaptadores existentes; validar e preservar metadados desconhecidos compatíveis do documento gráfico.
2. Produzir documento público removendo apenas `signatures` e suas referências em `layer_order`. Preservar `group_id` dos demais membros mesmo se o grupo ficar unitário; UI pode ocultar indicador sem destruir o valor. Assinaturas não são imagens mascaradas no esquema atual.
3. Campos de assinatura da tabela são derivados de `signature_id`; não são placeholders de texto. Não remover um placeholder comum só por coincidir com nome de assinatura.
4. Snapshot `origin_info` completo vai para bloco protegido se mencionar assets de assinatura. Parte pública guarda versão filtrada; cópia sem assinaturas usa snapshot filtrado. No desbloqueio normal restaurar snapshot completo. No integral todo snapshot fica protegido.
5. Resolver assets por referências e papel, não por igualdade de bytes. Asset referenciado apenas por assinatura fica protegido. Se mesma referência também for usada por imagem comum, gerar referência pública e protegida separadas; não bloquear nem comparar conteúdo. Isso respeita a decisão explícita do usuário.
6. Se público inalterado, recombinar coleções e ordem original exatamente. Não renumerar object_id/signature_id nem reordenar camadas.
7. Se público válido alterado, alertar antes de combinar e continuar com regras determinísticas: manter ordem atual dos objetos públicos, inserir cada assinatura antes do próximo objeto público sobrevivente na ordem original (ou ao final), preservando ordem relativa das assinaturas. Não sobrescrever mudanças públicas com snapshot antigo.
8. Conflito de object_id: remapear ID da assinatura dentro da cópia em memória e suas relações; nunca substituir objeto público. Conflito de group_id após mudanças que tornem associação ambígua: separar o grupo protegido, mantendo seus membros, e informar no resumo de revisão. Geometria continua preservada.
9. Página original removida/renomeada externamente: não descartar assinaturas. Oferecer destino entre páginas atuais antes de disponibilizar documento completo, com cancelamento; nenhuma gravação automática. Estrutura pública inválida é erro de formato, não mero alerta. Essas são situações excepcionais de recuperação, sem diálogos extras na abertura normal.
10. Cópia sem assinaturas recebe nova identidade somente ao salvar/incorporar e nunca utiliza o destino do original. Novo nome obrigatório. Remover referências/slots protegidos, não simplesmente ocultar sua pintura.

Teste de contrato a implementar em 3.2: separação/recombinação da fixture da Etapa 1 produz igualdade do documento normalizado, exceto IDs de asset remapeados e metadados internos; pixels devem ser idênticos. Incluir assinaturas em ambas as páginas nos casos adicionais.

### Interface de armazenamento (contratos, não código de produção)

- `inspect(path) -> descriptor`: leitura limitada de manifesto, modo, identidade, revisão e rótulo acessível. Não carregar JSON integral na listagem.
- `open_public(descriptor) -> detached_document`: só `none`/`signatures`; marcar cópia sem assinaturas no segundo caso.
- `unlock(descriptor, password) -> authorized_session`: autenticar, validar payload, conferir referência pública, processar alerta; só então disponibilizar conteúdo.
- `session.document()` retorna documento autorizado; `session.asset(asset_id)` retorna bytes/imagem em memória, com limite. Renderer não recebe senha nem faz IO de contêiner.
- `save(session, destination, mode)` publica transação; `export_copy`/`import_copy` usam novas chaves/identidades e não modificam fonte.
- Adaptador legado retorna mesmo contrato, mas sinaliza migração pendente. Nunca falsificar diretório descriptografado temporário para satisfazer `__model_dir`.
- `core/model_document.py` continua responsável por semântica v4; armazenamento controla autorização, persistência e assets. Planilha/renderer recebem o documento já preparado.

## 2.2 — Criptografia, dependências e limites

### Perfil v1 fechado

| Parâmetro | Valor |
|---|---|
| Biblioteca avaliada | `cryptography==50.0.1` |
| Perfil | `a2id-64m-t3-p1-aes256gcm-v1` |
| KDF | Argon2id, versão 19, 65536 KiB, 3 passagens, 1 lane, saída 32 bytes |
| Salt | 16 bytes aleatórios do SO |
| Chave de dados (DEK) | 32 bytes aleatórios do SO |
| Chave de proteção (KEK) | saída Argon2id; nunca persistida nem incluída como hash PHC |
| Cifragem | AES-256-GCM, nonce 12 bytes, tag completa 16 bytes |
| Segredos novos | DEK nova por revisão gravada e cópia; novos nonces por cifragem |
| Concorrência KDF | 1 operação por processo, fila cancelável entre operações |

Senha: normalizar NFC, contar pontos de código Unicode após normalização (8–64), codificar UTF-8 estrito. Sem trim/casefold/truncamento. Aceitar espaços/acentos e colagem; confirmação compara após NFC. Rejeitar substitutos Unicode inválidos. Não confundir 64 caracteres com 64 bytes; máximo UTF-8 resultante é 256 bytes.

`header` protegido tem exatamente os campos do exemplo. Serialização para AAD: JSON ASCII, chaves ordenadas, separadores `,` e `:`, `ensure_ascii=True`, `allow_nan=False`, sem whitespace adicional, tipos exatos (bool não é inteiro). IDs/hex/perfil são ASCII restritos. JSON de entrada rejeita chaves repetidas.

```text
H = bytes ASCII da serialização de header
KEK = Argon2id(password_UTF8, salt, perfil fixo)
wrapped_key = AESGCM(KEK).encrypt(wrap_nonce, DEK, b"FORNAX/v1/wrap\0" + H)
protected.bin = AESGCM(DEK).encrypt(payload_nonce, ZIP_interno, b"FORNAX/v1/payload\0" + H)
```

As tags vêm anexadas pela API. O resumo público NÃO entra no AAD; fica autenticado DENTRO do plaintext protegido, permitindo aviso recuperável depois da descriptografia. Header atual autentica modo/identidades/perfil/nonces/salt. `wrapped_key_hex` é a única outra chave do manifesto protegido e tem 96 dígitos hex minúsculos.

No desbloqueio, validar limites e perfil antes da KDF, autenticar wrap, autenticar payload completo e só então interpretar ZIP/JSON. Nada parcialmente decifrado segue para UI/renderer. `InvalidTag` gera erro genérico de senha ou conteúdo protegido danificado. Erros de limite/formato são distintos, sem vazar segredo.

Enquanto sessão autorizada existe, reter KEK e salt para salvar sem pedir senha repetidamente. Salvar gera nova DEK e revisão e novos nonces; reembrulha DEK com KEK da sessão. Trocar senha, importar ou exportar gera novo salt/KEK/DEK e recriptografa. Encerrar/expirar descarta referências; não garantir zeroização perfeita em Python. Histórico de arquivos antigos não tem acesso revogado pela troca de senha atual.

### Experimento e vetor público

`tools/probe_fornax_crypto_spec.py` valida primitivas isoladamente, sem tocar em modelos do usuário ou dependências do aplicativo. Ambiente em `/tmp/fornax-stage2-crypto`, instalado com wheels. Python 3.13.11, Linux x86_64, cryptography 50.0.1, OpenSSL 4.0.2.

Sete amostras Argon2id: 135,653 / 118,537 / 115,977 / 116,444 / 117,106 / 113,883 / 113,941 ms; mediana **116,444 ms**. Não aumentar artificialmente a espera nem reduzir parâmetros: meta anterior de 0,5–1 s era estimativa para máquina modesta, não obrigação de atrasar máquina rápida.

Vetor determinístico público, executado com o header do script:

```text
senha = Frase pública de teste 2026
KEK = 0c1b99d37d90fb462ec192743e92877df162181a158361b7000b40e1a72de5b3
wrapped_key = 38a86c33205773b74bd80be90c5afc36e0f89c497453cf530b8cee0c7086383ba1a9a843a89063c417af9be7056891e2
```

Round-trip e equivalência Unicode passaram. Cinco rejeições esperadas passaram: senha errada, wrap adulterado, payload adulterado, header alterado e propósito AAD trocado. Modificação pública não impediu decifrar. Este último ensaio demonstra separação da checagem, não implementa comparador de manifestos/pacotes.

### Dependências e distribuição

Na Etapa 3, fixar `cryptography==50.0.1` em requirements e Flatpak, resolver/pinar transitivas por plataforma e registrar hashes das wheels no processo de distribuição. Experimento Linux usou `cffi==2.1.1` e `pycparser==3.0`; isso não comprova instalação nativa em todos os SOs.

Nuitka precisa incluir pacote/extensões cryptography e sua dependência binária; AppImage deriva desse standalone. Manifesto Flatpak de fonte é `com.leobelisario.FornaxForge.yaml` (o arquivo `.flatpak` é artefato binário, não manifesto). Verificar runtime Python/OpenSSL efetivamente empacotado. Se Argon2id indisponível, bloquear funcionalidade protegida claramente; nunca substituir KDF silenciosamente. Wheels para Python/arquitetura alvo e execução dos vetores em Windows/macOS são gates de distribuição em 3.10/4.4.

### Limites iniciais do leitor v1

Limites operacionais conservadores para primeiro formato, não máximos empiricamente observados de clientes. A fixture pequena da Etapa 1 não justifica afirmar cobertura universal. Excesso recebe erro claro sem truncar nem converter parcialmente.

| Recurso | Limite |
|---|---:|
| `.fornax` físico | 512 MiB |
| Entradas por ZIP (externo ou interno) | 4096 |
| Manifesto | 16 KiB |
| JSON público ou protegido | 8 MiB cada; profundidade 64; 100000 objetos totais |
| Asset individual codificado | 128 MiB |
| ZIP protegido antes de cifrar | 256 MiB; ciphertext até esse valor + 16 bytes |
| Soma de bytes descompactados por modelo, todas camadas | 512 MiB |
| Imagem raster | até 64 milhões de pixels; até 32768 por dimensão |
| ZIP de lote | 2 GiB físico, 1000 modelos, 10000 entradas, 4 GiB descompactados agregados |
| Aninhamento | lote → `.fornax` → payload interno; nenhum outro nível |

Verificar diretório central e bytes realmente lidos, contabilizando modelos ignorados quando examinados, sem ler tudo primeiro. No lote, processar um modelo por vez. Limite agregado não autoriza manter 4 GiB na memória. Cache decodificado com orçamento de 256 MiB e descarte LRU; medir pico nativo no gate 4.4. SVG: sem scripts, entidades externas, referências de rede/arquivo; extensão/MIME não bastam. Avaliar tamanho antes de decodificação e aplicar limites da biblioteca de imagem.

Aceitar apenas ZIP_STORED/DEFLATED, sem senha ZIP tradicional, symlinks, caminhos absolutos, `..`, backslashes, entradas duplicadas ou nomes ambíguos por caixa. ZIPs legados passam pelo mesmo limite e whitelist antes de publicação. Não confiar em `extractall()`. Falta de asset que a referência exige deve ser reportada; a fixture de asset invisível ausente exige recuperação explícita, não descarte silencioso na conversão.

## 2.3 — Alerta e estados de acesso

### Referência pública autenticada

Ao salvar completo, computar SHA-256 dos bytes exatos de `public/document.json` e de cada asset público. Lista ordenada `[{path,sha256}]` vai dentro de `signatures.json`, autenticada pela tag do payload. Comparar conjunto de paths e hashes; adições, remoções e mudanças disparam aviso. ZIP timestamps, ordem física/compressão e manifesto não integram essa lista; metadados essenciais do manifesto já integram AAD.

Escolha deliberada: mudança apenas de formatação do JSON também alerta. Evita divergência de canonicalização numérica de documentos entre bibliotecas. O programa sempre escreve JSON UTF-8 determinístico com serializador documentado e sem valores não finitos; não precisa comparar JSONs semanticamente para detectar alteração.

Alerta após senha válida e estrutura pública válida, antes de publicar assinatura: “Foi identificada uma possível alteração no conteúdo deste modelo desde o último salvamento protegido. Confira os textos, imagens e configurações antes de gerar materiais.” Botões “Revisar modelo” e “Cancelar”. Revisar permite acesso autorizado com indicação discreta até salvar. Não é impedimento permanente nem restauração automática.

Aceite vale só para identidade + hash de revisão física atual na sessão. Novo processo ou nova mudança exige alerta. Apenas salvar explicitamente o modelo completo redefine referência. Cópia sem assinaturas não autentica o conteúdo público, preserva original e não redefine referência. Nomear essa ação como revisão não promete autenticação de autoria ou aprovação institucional.

### Máquina de estados

| Evento | Estado/efeito |
|---|---|
| Selecionar `none` | público editável |
| Selecionar parcial bloqueado | pedir senha ou cópia sem assinaturas |
| Selecionar integral bloqueado | painel neutro e senha/cancelar |
| Senha válida, público alterado | aguardando revisão; não liberar assinatura antes de aceite |
| Aceitar revisão / íntegro | ativo autorizado |
| Sair de autorizado | tolerância de 300 s por modelo/revisão |
| Retornar antes de 300 s | ativo autorizado; cancelar relógio |
| Expirar fora do modelo | descartar UI/cache/KEK; pedir só no próximo acesso |
| Mudança externa de revisão | invalidar sessão antiga; recarregar e verificar |
| Fechar processo | encerrar acessos, workers e referências |

Relógio monotônico e tratamento de suspensão: ao retomar do SO invalidar modelos em tolerância se não puder provar prazo restante; modelo ativo segue regra de não expirar. Não confiar exclusivamente no relógio de parede ajustável. Cobrir transições com relógio simulado.

Jobs de geração capturam documento/assets imutáveis autorizados e podem terminar; não carregam KEK desnecessária e não devolvem autorização à UI. Resultados de preview usam token de sessão + revisão + seleção; resultados atrasados são descartados. Mudança de arquivo nunca substitui silenciosamente documento com alterações não salvas no editor: oferecer manter trabalho em nova cópia ou recarregar após decisão.

### Compartilhamento e transições

| Origem | Operação sem senha | Operação após desbloqueio |
|---|---|---|
| `none` | abrir/exportar/importar | escolher integral se desejar |
| `signatures` | cópia sem assinatura | completo, nova senha local/exportação; pode elevar para integral |
| `full` | apenas cancelar/ignorar modelo | completo ou cópia sem assinaturas; preservar integral por padrão |

Omitir assinatura de um modelo integral não remove automaticamente proteção integral. Se usuário escolher redução: com assinatura, parcial; sem assinatura, none permitido. Falha ao desbloquear integral oferece retry ou ignorar modelo, nunca “abrir sem” como bypass.

Pacote exportado usa mesma senha escolhida para todos os protegidos, salts/chaves diferentes. Falhas de tentativa comum reaparecem individualmente. Importação exige novas senhas locais; se alguma escolha faltar, modelo não é publicado. Lote não é transação única: publicar unidades válidas, relatar sucessos/ignorados/falhas; cancelamento preserva sucessos claramente informados. Recebido e originais não mudam.

## 2.4 — Publicação, migração e persistência

### Salvamento de um .fornax existente

1. Capturar revisão autorizada; montar novo conteúdo e cifrá-lo em memória.
2. Escrever `<destino>.pending-<uuid>` no mesmo volume, permissões restritas; somente pacote final cifrado ou público conforme modo.
3. Flush/fsync, reabrir e verificar estrutura, assets/hashes e descriptografia com chave de sessão. Comparar documento lógico, não apenas presença de arquivo.
4. Antes de substituir, conferir hash físico do destino contra revisão esperada. Conflito mantém original e oferece salvar cópia/recarregar, sem sobregravar mudanças de terceiros. Lock cooperativo durante publicar; reconhecer que processos externos não cooperativos ainda exigem rechecagem.
5. Preservar última versão válida em backup `.fornax.bak` protegido segundo seu modo. Nunca criar backup aberto ao ativar proteção sobre conteúdo que antes estava público: converter backup para modo destino ou substituir por cópia protegida verificada.
6. Substituição atômica e fsync do diretório quando suportado. Se falhar, destino anterior válido permanece; pending não é listado como modelo.
7. Limpar pending após sucesso ou falha; interrupção deixa pacote cifrado que pode ser retomado/verificado, sem extração de assinatura em claro.

Reduzir proteção deliberadamente pode produzir documento público; não confundir isso com falha. Trocar senha não promete revogar backups/copias históricas: backup local automático deve ser recriptografado para nova senha antes de finalizar a operação, ou substituído por uma cópia verificada do novo pacote quando recriptografar a versão anterior não for possível. Falha nessa atualização mantém operação como pendente, informando o usuário.

### Conversão de pasta ao selecionar

Diário retomável em `<dados>/migrations/<operation_id>.json`, só IDs/paths relativos/hashes/estados; nunca senha, conteúdo, chaves ou nomes internos do modo integral. Estados: PREPARED → VERIFIED → PUBLISHED → CLEANED.

| Ponto de interrupção | Retomada |
|---|---|
| Antes de gravar pending | pasta original intacta; pedir cadastro novamente quando necessário |
| Durante pending / antes de VERIFIED | descartar pending incompleto restrito; manter pasta |
| VERIFIED, ainda não PUBLISHED | revalidar hash do pending e identidade/hash do original; publicar se consistente, senão manter original |
| PUBLISHED, pasta ainda existe | listar somente destino validado; original pertence à operação de migração pendente |
| Durante limpeza | remover só alvos registrados e ainda inalterados; retomar sem reconverter |
| CLEANED | remover diário/temporários; manter `.fornax` único |

Cadastros com assinatura oferecem parcial/integral. Normalização não cria verso. Comparar todos os atributos gráficos e assets referenciados, incluindo assinaturas ocultas. Não prometer conversão íntegra se asset estiver ausente: informar lista e manter original até usuário resolver ou optar por salvar nova cópia sem o elemento ausente. Abertura sem assinatura pode ignorar asset de assinatura ausente porque remove esse elemento, sem modificar original.

Antes da limpeza, registrar hashes dos arquivos da pasta; alteração concorrente suspende limpeza. Confirmar destino verificado ainda existe e corresponde ao hash publicado em toda retomada. Não deletar pasta inteira cegamente se contiver arquivos desconhecidos/adicionados depois: registrar e reportar pendência. Não seguir symlinks. Backups v3/v4 contendo assinaturas não permanecem abertos como “segurança”; oferecer recuperação protegida ou removê-los somente após validação da migração. Dados originais externos e imagens variáveis não são removidos.

Publicação verificada antecede qualquer remoção material. Se limpeza falhar, não dizer que migração terminou ou que cópias antigas já estão protegidas. Listagem usa diário para evitar duplicidade, com pendência acessível. Cancelar antes de publicar não protege legado e não pode ser apresentado como proteção concluída.

### Destino dos dados derivados

| Dado | Política |
|---|---|
| Assinatura/asset integral decifrado | memória autorizada; nunca path temporário aberto |
| Preview parcial desbloqueado | memória; no disco somente thumbnail sem assinaturas |
| Preview integral | memória após senha; bloqueado mostra placeholder genérico |
| Folhas de impressão em preview | memória com cache limitado; eliminar atual temporário PNG aberto |
| Histórico/clipboard interno | memória; referências autorizadas; não enviar assets protegidos ao clipboard público do SO |
| Recuperação persistida | pacote cifrado conforme modo; nunca JSON de sessão em claro |
| Geração final | arquivos explicitamente solicitados podem ser públicos |
| Intermediários da geração agrupada | spool protegido ou memória limitada; `.temp_hybrid` aberto não atende à regra aprovada |
| Logs/QSettings | sem senha/chave/conteúdo; somente metadados operacionais necessários |

Para lote grande, não acumular todos os pixels em memória: spool interno cifrado com chave aleatória efêmera de job, nonce por entrada e revisão/índice autenticados. Chave só em memória; limpar no fim/cancelamento e resíduos inacessíveis no próximo início. Isso não muda o pipeline gráfico; muda IO entre worker e montador. Arquivos finais `.partial.pdf`/PNG destinados à publicação são resultados em construção, sujeitos a limpeza e não reutilizados como cache de modelo.

### Revisão dos checkpoints e evidências

- 2.1: três layouts, dois exemplos de manifesto, payload parcial, regras de relações, cópia e contratos de armazenamento definidos. Exemplos são especificação; round-trip de contêiner fica em 3.1/3.2.
- 2.2: primitivas/perfil/Unicode/AAD/limites especificados; experimento executado com vetor público e cinco falhas esperadas. Dependências do aplicativo não alteradas. Plataformas empacotadas e equipamento modesto são gates explícitos, não resultados desta etapa.
- 2.3: alteração pública separada da autenticação obrigatória, alerta e estado de sessão definidos; cenários de expiração, jobs e compartilhamento registrados.
- 2.4: walkthrough de crash antes/depois de publicação, recuperação, conflito e limpeza definido; caches, previews, histórico, geração e logs têm política de destino.
- Correção do inventário: o nome de classe do gerador é `RenderManager`; diretório intermediário de PDF agrupado é `<saída>/.temp_hybrid`. A seleção chama gravação também por alterações de predefinição e por criação de `origin_info`, rotas que devem passar pela autorização central.
- Limite das evidências da etapa anterior: hashes visuais sintéticos não substituem captura de canvas/folha e testes nativos; a fixture não cobre limites institucionais máximos. Essas verificações precisam ser ampliadas antes da liberação em 4.4.

Próximo checkpoint: **3.1 — Contêiner e validação de entradas**. Implementar somente após ler estes contratos; não integrar criptografia à UI antes de testar núcleo e acesso autorizado.

## Fontes técnicas consultadas em 20/09/2026

- https://cryptography.io/en/stable/hazmat/primitives/key-derivation-functions/ — parâmetros Argon2id, suporte de backend e Unicode tratado na aplicação.
- https://cryptography.io/en/stable/hazmat/primitives/aead/ — AESGCM, AAD, tags e rejeição de adulteração.
- https://pypi.org/pypi/cryptography/json — distribuição da biblioteca; versão efetivamente instalada e testada: 50.0.1.

Sem alegação de certificação, autenticidade de autoria ou auditoria independente. Revisão especializada permanece prevista em 4.1.
