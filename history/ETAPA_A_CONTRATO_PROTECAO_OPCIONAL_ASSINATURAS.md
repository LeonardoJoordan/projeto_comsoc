# Checkpoint A — contrato da proteção opcional de assinaturas

Data: 20/09/2026.
Estado: concluído; nenhuma mudança de comportamento implementada.
Plano: `PLANO_PROTECAO_OPCIONAL_ASSINATURAS.md`.

## Resultado

O contrato separa definitivamente três decisões antes confundidas pelo código:

1. **Conteúdo:** o documento possui ou não objetos do tipo assinatura.
2. **Armazenamento:** público, assinaturas protegidas ou integralmente protegido.
3. **Compartilhamento:** a cópia inclui ou retira as assinaturas.

Nenhuma API nova deve deduzir uma dessas decisões a partir das outras. Em especial,
`mode == "none"` não poderá mais significar “documento sem assinaturas”, e
`include_signatures == false` continuará significando remoção explícita do conteúdo.

## Decisão de compatibilidade do contêiner

O contêiner atual usa versão 1. Leitores dessa versão recusam assinaturas no modo
público. O novo caso será identificado como **contêiner versão 2, modo `none`**.

- Versão 1 continua aceita e escrita para público sem assinatura e para os dois
  modos protegidos atuais. Seus bytes, KDF, nonces e AAD não mudam.
- Versão 2 é escrita somente quando um documento público contém ao menos uma
  assinatura. Ela pode ser lida sem senha porque o usuário aceitou esse risco.
- A parte pública de um contêiner `signatures`, versão 1, continua proibida de
  conter assinaturas. Não mover conteúdo cifrado para a parte pública.
- Se todas as assinaturas forem retiradas de um público v2, a próxima revisão pode
  voltar ao v1. A capacidade que exigia v2 deixou de existir.
- O documento gráfico permanece schema v4. Não há motivo para alterar coordenadas,
  páginas, renderer ou a criptografia por causa desta capacidade.
- O parser novo aceita versões 1 e 2 segundo a matriz acima. Combinações não
  especificadas são recusadas como recurso não suportado ou formato inválido.
- O descritor e a serialização autenticada usam a versão real do pacote; não uma
  constante global inserida posteriormente.

Essa decisão é necessária porque o leitor anterior reconhece somente a versão 1.
Ao encontrar v2, ele lança `UnsupportedFornaxFeature`. A biblioteca já trata esse
caso separadamente e não restaura `.bak` como se o arquivo fosse corrompido. Emitir
assinatura pública em v1 faria o leitor antigo acusar corrupção depois de aceitar
o manifesto, com risco de recuperação indevida.

Antes de implementar, preservar em teste uma cópia do parser v1 ou construir
manualmente um manifesto v2: a expectativa é recusa por versão futura, sem tocar
no arquivo nem no backup. O teste não deve chamar apenas o parser já atualizado.

## Metadado da recomendação

Nome fechado:

```json
{
  "protection_preferences": {
    "public_signatures_acknowledged": true
  }
}
```

Regras:

- campo no documento, acima das páginas; não integra `manifest.json`;
- ausente ou `false`: decisão local ainda não registrada;
- somente booleano é aceito; texto, número, lista e objeto no valor são inválidos;
- gravado apenas na revisão publicada com sucesso depois de “Salvar sem senha”;
- não é autorização criptográfica, não suprime verificação de senha e não permite
  substituir um original protegido;
- remover todas as assinaturas remove também o aceite, por não ter mais função;
- adicionar assinatura a um público sem o campo exige a recomendação;
- salvar novamente o mesmo público já aceito não repete a recomendação;
- “Salvar como”, duplicar ou importar cria uma identidade local nova e remove o
  aceite antes de decidir. A decisão não é global nem herdada do remetente;
- exportar pode manter o campo no pacote recebido, mas a importação para a
  biblioteca local deve removê-lo antes de apresentar a decisão ao destinatário;
- proteger o modelo remove o aceite do documento persistido. Se um dia ele voltar
  a público com assinaturas por uma ação explícita futura, deverá decidir novamente.

`origin_info` continua sendo histórico informativo. Não registrar a decisão ali.

## Contrato das APIs

### Contêiner

`save_public_fornax(document, ...)`

- O próprio documento define se há assinatura.
- Sem assinatura: grava v1.
- Com assinatura: exige `public_signatures_acknowledged is True`, grava v2 e inclui
  objetos e assets como conteúdo público. Uma chamada interna sem aceite falha.
- Não recebe `include_signatures`; retirar conteúdo é responsabilidade de uma
  operação explícita anterior.

`open_public_fornax(...)`

- v1/`none`: mantém a regra sem assinaturas.
- v2/`none`: aceita e valida assinaturas/assets como as demais imagens públicas.
- v1/`signatures`: abre somente a parte pública sem assinaturas.
- `full`: continua exigindo senha.

`save_protected_fornax(...)`, desbloqueio e sessão

- Contrato criptográfico e versão 1 permanecem.
- O metadado de aceite público é removido ao proteger.
- A sessão pública pode conter assinaturas; `PUBLIC_ACTIVE` descreve acesso, não
  ausência de assinatura. `SIGNATURE_FREE_COPY` mantém seu sentido atual.

Operação de retirada de assinaturas

- Centralizar um helper que retire objetos, IDs em `layer_order`, campos de tabela
  derivados e assets que ficaram órfãos, preservando qualquer asset ainda usado
  por imagem comum. `save_signature_free_copy` e importação/exportação devem usar
  a mesma semântica. Não inferir pela palavra “signature” no caminho.

### Migração e salvamento do editor

- A escolha da interface produz `(target_mode, acknowledged)` explicitamente.
- Público com assinatura só é enviado à API depois do aceite.
- Cancelamento não altera documento, arquivo, diário nem metadado.
- Conversão legada pública conserva assinatura, visibilidade, IDs, ordem e assets;
  não usa o fluxo “cópia sem assinaturas”.
- O aceite é confirmado somente depois da publicação verificada. Para construir
  os bytes, trabalhar numa cópia do documento; não marcar antecipadamente o estado
  mantido pela janela.

### Importação

Acrescentar uma escolha de destino independente, equivalente a:

```text
include_signatures: bool
target_mode: none | signatures | full
local_password: requerido somente se target_mode for protegido
```

- `include_signatures=false` retira assinaturas para qualquer modo de origem.
- `target_mode=none` mantém as assinaturas incluídas após o aceite local e grava v2.
- `target_mode=signatures` exige ao menos uma assinatura incluída e senha local.
- `target_mode=full` exige senha local, mesmo sem assinatura.
- Origem protegida continua exigindo senha de transporte quando seu conteúdo
  precisa ser lido. Público v2 nunca exige senha do remetente.
- A cópia ganha nova identidade e `origin_info` importado, como hoje.

### Exportação

- `include_signatures` é obrigatório como decisão de conteúdo quando a fonte tem
  assinaturas, independentemente do modo.
- Público v2 + incluir: gera público v2 sem senha de transporte.
- Público v2 + retirar: gera público v1 sem assinatura.
- Protegido + incluir: mantém desbloqueio e senha de transporte atuais.
- Protegido + retirar: gera cópia pública v1 sem assinatura, sem sobrescrever origem.
- Integral exige desbloqueio até para retirar conteúdo, pois nada está disponível
  publicamente. Lotes aplicam a decisão por modelo, com escolha comum apenas como
  conveniência explícita da interface.

## Matriz normativa

| Origem | Incluir assinatura | Destino local/compartilhado | Senha necessária |
|---|---:|---|---|
| Público v1 sem assinatura | Não se aplica | Público v1 | Não |
| Público v2 com assinatura | Sim | Público v2 | Não; aceite local ao incorporar |
| Público v2 com assinatura | Não | Público v1 sem assinatura | Não |
| Assinaturas protegidas | Sim | `signatures` protegido | Origem e nova senha/transportes atuais |
| Assinaturas protegidas | Não | Público v1 sem assinatura | Não para ler sua parte pública |
| Integral protegido | Sim | Integral protegido | Origem e nova senha/transportes atuais |
| Integral protegido | Não | Público v1 sem assinatura | Senha da origem para ler o documento |
| ZIP legado com assinatura | Sim + público | Público v2 | Aceite, sem senha |
| ZIP legado com assinatura | Sim + protegido | `signatures` ou `full` | Nova senha local |
| ZIP legado com assinatura | Não | Público v1 | Não |

Um modelo público v2 pode ser protegido depois. Essa transição publica uma revisão
protegida v1 com o mesmo `model_id`, nova `revision_id` e regras de backup já
existentes para não deixar uma nova cópia pública ao lado da proteção elevada.

## Referência anterior à implementação

Fixture: `tests/fixtures/fornax_stage1/template_v4.json`.

- duas páginas, 400 × 240 px, 100 × 60 mm;
- texto rico nas duas páginas;
- uma assinatura visível e uma oculta na frente;
- máscara, grupo, forma dinâmica, imagem fixa, link e placeholder;
- controle individual por `signature_id` já coberto na tabela;
- asset invisível ausente propositalmente, útil para validar tolerância do renderer,
  mas deve ser removido da cópia sintética antes de empacotar um `.fornax` válido.

Hashes PNG de referência, já preservados em
`history/ETAPA_4_4_MEDICOES_FORNAX.json`:

| Página | SHA-256 | Dimensões |
|---|---|---|
| Frente | `0cb6bb8a7e6dddacfc78946a28ddffb507ab335e16ce2724d3458c5f1d313197` | 400 × 240 |
| Verso | `c94de46797aa1a9de62a4f50a72f559c4d8ccab9e8ad43e8d0194db7c1aa9160` | 400 × 240 |

Script reproduzível: `tools/capture_fornax_stage1_baseline.py`, sempre com um
diretório de saída novo para não sobrescrever a coleta original. A referência
funcional também está em `tests/test_fornax_stage1_contracts.py`; controles de
assinatura da tabela em `tests/test_workspace_fields.py`.

Validação desta etapa: 25 testes aprovados em 0,49 s nos contratos de referência,
tabela e contêiner. Um aviso preexistente de API Qt obsoleta apareceu na tabela.
O teste atual `test_writer_rejects_signature_and_missing_asset` documenta a regra
que será parcialmente substituída: a falta de asset continuará falhando; a
assinatura pública passará a ser o novo caminho v2.

## Evidência Windows disponível

`history/VALIDACAO_WINDOWS_FORNAX.md` registra Windows 11 build 26200, NTFS,
Python 3.13.11, PySide6 6.11.0, cryptography 50.0.1 e build Nuitka/Inno.
A suíte anterior teve 322 testes e 12 subtestes aprovados; o backend Qt Windows
teve 20 testes; editor nativo teve 63. O executável e instalador foram gerados com
hashes registrados naquele relatório. Instalação pelo Explorer ainda constava
pendente nele.

Esses resultados são referência da política obrigatória anterior. Os cenários
afetados por assinatura pública v2 deverão ser repetidos no Windows; não considerar
esta alteração aprovada pela bateria anterior.

## Testes que mudarão ou serão acrescentados

- Substituir apenas a expectativa de recusa de assinatura em público por round-trip
  v2; manter o caso independente de asset ausente.
- Parser v1 de referência recusando v2 como versão futura, sem recuperação do backup.
- Matriz de versão/modo/assinatura e versão real coberta pelo AAD/descritor.
- Validação estrita de `protection_preferences` e persistência após sucesso.
- Round-trip, falhas e transições público v2 ↔ protegido v1.
- Importação/exportação da matriz acima, inclusive asset compartilhado.
- Editor: aceitar uma vez, cancelar, reabrir sem repetir e “Salvar como”.
- Migração v3 sem `layer_order`, duas páginas e assinatura oculta.
- Sessão, autosave, backup, recuperação e ciclo de vida de dados.
- Render, preview, tabela e PDF/PNG com hashes equivalentes.
- EN/ES e testes manuais Linux/Windows posteriores.

## Próximo ponto de retomada

Checkpoint B: implementar versão/capacidade, metadado validado, leitura/escrita
pública de assinaturas, sessão e persistência. Começar por testes do parser v1 e
da matriz de versão; depois alterar o núcleo. Não iniciar pela interface.
