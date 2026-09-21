# Proteção recomendada, opcional, para modelos com assinaturas

Estado: checkpoint A concluído; checkpoint B é o próximo. Implementação do comportamento ainda não iniciada.
Criado em: 20/09/2026, após inspeção do código atual.
Objetivo: substituir a obrigação de cadastrar senha por uma recomendação,
preservando as assinaturas quando o usuário escolher salvar sem proteção.

Este documento é a referência para outra IA executar a alteração em checkpoints.
A execução foi autorizada; avançar um checkpoint por vez e registrar as evidências.

## 1. Decisões e limites

### Comportamento acordado

- Modelos com assinaturas podem ser salvos sem senha após escolha explícita.
- O programa recomenda proteção; não impede o salvamento público por conter assinatura.
- Continuam disponíveis proteção das assinaturas e proteção integral.
- A decisão de salvar sem proteção pertence ao modelo e deve sobreviver a fechamento
  e reabertura, evitando repetir o aviso a cada salvamento.
- Modelos já protegidos não perdem sua proteção nem passam a abrir sem senha.
- “Abrir sem assinaturas” continua produzindo uma cópia sem esses objetos,
  preservando o original e exigindo salvar como novo modelo.
- Cancelar a decisão ou o cadastro de senha não equivale a aceitar salvar sem senha.
- Imagens comuns continuam imagens comuns; não detectar assinaturas pelo conteúdo.
- A política abrange assinaturas visíveis e ocultas, nas duas páginas.

Texto-base da recomendação:

> Este modelo contém assinaturas. Recomendamos protegê-las com uma senha para
> evitar seu uso sem autorização.

Escolhas: **Proteger assinaturas**, **Proteger modelo inteiro**, **Salvar sem senha**
e cancelamento. Seguir os estilos de botões já existentes; não introduzir ícones
ou cores fora do padrão. Explicar que salvar sem senha permite a qualquer pessoa
com acesso ao arquivo extrair e utilizar suas assinaturas.

### Diretrizes propostas para os detalhes ainda não implementados

Adotar estas diretrizes ao executar, sem tratar escolhas técnicas como regras já
presentes no código. Registrar qualquer divergência antes de implementar.

1. Recomendação ao salvar, converter ou incorporar uma assinatura desprotegida;
   não interromper cada seleção, preview ou geração de um modelo público já aceito.
2. Aceite único por modelo, sem timer e sem reapresentação a cada nova assinatura.
   O usuário pode ativar a proteção depois por uma ação explícita e discreta no
   diálogo de proteção; localizar e reutilizar o acesso existente ou adicionar
   acesso mínimo se ele não existir. Não inventar uma nova tela principal.
3. Para uma cópia deliberadamente criada como novo modelo, decidir a proteção da
   cópia no salvamento. Não transformar um aceite antigo em autorização global.
4. Ao receber modelo público com assinaturas, permitir manter sem senha ou proteger
   localmente. A escolha feita pelo remetente não deve suprimir a recomendação
   na primeira incorporação pelo destinatário.
5. Alterar somente a obrigatoriedade local nesta atualização. Modelos já protegidos
   continuam no fluxo protegido de compartilhamento: desbloqueio local, senha de
   transporte e nova proteção local no destinatário. Não adicionar remoção geral
   de senha nem exportação pública de conteúdo protegido por efeito colateral.
6. Modelos públicos com assinaturas podem ser exportados mantendo as assinaturas
   sem senha ou retirando-as. Apresentar escolha explícita de inclusão; não retirar
   assinaturas silenciosamente por serem públicas. Manter a opção de proteger o
   modelo antes de compartilhar. Tornar opcional a senha de transporte de modelos
   já protegidos é uma mudança distinta, fora deste plano.

## 2. Mapa do código e armadilhas confirmadas

As referências abaixo usam nomes de funções; localizar novamente na execução,
pois números de linha e implementação podem mudar.

| Arquivo / ponto | Comportamento atual e ajuste necessário |
|---|---|
| `core/fornax_container.py`: `save_public_fornax` | Recusa qualquer assinatura. Deve aceitar objetos e assets de assinatura no modo `none`. |
| Mesmo arquivo: `open_public_fornax` | Recusa assinaturas no documento público de todos os modos. Liberar somente no modo `none`; manter a proibição no trecho público de `signatures`. |
| Mesmo arquivo: `_split_signatures`, `_merge_protected_signatures`, `save_signature_free_copy` | Preservar isolamento criptográfico, recomposição e remoção explícita de assinaturas; não reaproveitar remoção para um salvamento público comum. |
| Mesmo arquivo: publicação/backup e leitura de versão | Rever compatibilidade e backup, incluindo upgrade de público com assinaturas para protegido. |
| `core/fornax_session.py`: seleção, `save`, recuperação e estado `SIGNATURE_FREE_COPY` | Público autorizado não significa cópia sem assinaturas. Conferir salvamento, autosave e transições sem perder assets. |
| `core/legacy_migration.py`: `migrate_legacy_model` | Exige `signatures` ou `full` quando encontra assinatura. Permitir `none` após a decisão da interface, preservando a transação. |
| `features/editor/editor_window.py`: `_choose_fornax_protection`, `_export_to_fornax` | Força escolha sempre que há assinatura no modo público. Usar o aceite persistente e permitir salvar sem senha. |
| Mesmo arquivo: `_write_fornax_recovery` e carregamento | Não perder assinaturas nem marcar aceite antes de o usuário decidir; recuperação não deve publicar/rebaixar o original. |
| `features/workspace/main_window.py`: `_legacy_migration_credentials` | Trocar imposição por recomendação, incluindo conversão ao selecionar e ZIP legado. |
| Mesmo arquivo: importação/exportação | Hoje identifica candidatos principalmente por `mode != PUBLIC_MODE`; conteúdo e proteção precisam ser decisões separadas. |
| `core/fornax_export.py`: `_export_copy` | O caminho público retorna cedo; verificar se passa a ignorar a escolha de retirar assinaturas. |
| `core/fornax_import.py`: `import_candidate` | `include_signatures=False` remove objetos. A UI inicia essa flag como falsa para entradas públicas; isso apagaria as novas assinaturas públicas. |
| Mesmo arquivo: `import_legacy_document` | Usa `include_signatures=mode != PUBLIC_MODE`; precisa deixar de confundir “sem senha” com “sem assinatura”. |
| `core/model_document.py`, `core/model_info.py`, `core/model_library.py` | Preservação de metadado, IDs, inventário, cópias, revisão de arquivo e leitura de modelos recebidos. |
| `assets/translations/fornax_{en_US,es_ES}.{ts,qm}` | Novos textos e retirada da obrigação da interface em português, inglês e espanhol. |

Não retirar em massa ocorrências de “senha obrigatória”: senha continua obrigatória
para desbloquear ou gravar um modo protegido. Não usar nomes de arquivos nem apenas
o modo para inferir presença de assinatura.

## 3. Modelo de dados e compatibilidade a definir primeiro

Separar três conceitos: presença real de assinaturas, modo de armazenamento e
decisão do usuário sobre a recomendação.

| Situação | Assinaturas no documento | Autorização |
|---|---|---|
| Público sem assinaturas | Nenhuma | Abre normalmente |
| Público com assinaturas | Presentes, assets públicos | Abre normalmente; decisão explícita ao criar/incorporar |
| Assinaturas protegidas | Reconstituídas após desbloqueio | Mantém senha e tolerância atuais |
| Integralmente protegido | Conteúdo inteiro cifrado | Mantém senha e tolerância atuais |
| Cópia aberta sem assinaturas | Nenhuma assinatura do original | Novo modelo; nunca sobrescreve o original protegido |

Metadado definido no checkpoint A: campo de documento, não de página,
`protection_preferences.public_signatures_acknowledged = true`.
Campo ausente equivale a decisão
ainda não registrada. Validar o tipo; não interpretar a string `"false"` como true.
Não usar prefixo `__`, eliminado pela persistência. É preferência de UX, não prova
criptográfica nem autorização para acessar/retirar conteúdo protegido.

Gravar o aceite apenas depois da escolha e de um salvamento bem-sucedido. Erro ou
cancelamento não deve marcar a operação concluída. Recarregar o aceite após abrir
o arquivo. Importação como novo modelo deve coletar decisão local, em vez de herdar
silenciosamente esse aceite. Documentar a política para duplicação e “Salvar como”.

**Compatibilidade exige uma decisão verificável:** leitores atuais recusam
assinaturas em modo público. Simplesmente emitir o novo conteúdo na mesma versão
pode fazer o leitor antigo tratá-lo como corrompido e tentar restaurar `.bak`.
Definir um sinal de versão/capacidade reconhecido como não suportado pelos leitores
anteriores, antes de publicar o novo arquivo. Avaliar versão de contêiner nova
somente para a capacidade pública com assinaturas, mantendo leitura dos pacotes
existentes; não aumentar arbitrariamente versão do documento gráfico ou parâmetros
criptográficos. Registrar a escolha e testar com uma referência do leitor anterior.
Não afirmar que um campo desconhecido no JSON resolve isso sem demonstrar.

## 4. Execução por checkpoints

Executar em ordem. Cada checkpoint termina com testes apropriados e registro do
resultado nesta tabela. Não alterar modelos reais para testar migração.

### A — Contrato, compatibilidade e referências (risco médio)

**Objetivo:** eliminar ambiguidades antes de mexer no formato.

- Confirmar o mapa contra o código atual e ler o plano anterior e seus relatórios.
- Fechar metadado/versão e a matriz de importação/exportação descrita acima.
- Registrar contrato de cada API: incluir assinatura é independente do modo.
- Capturar referências sintéticas de frente/verso com assinaturas visíveis/ocultas,
  textos ricos, assets compartilhados e controles individuais na tabela.
- Registrar os testes Windows já feitos com sua versão/artefato, se as evidências
  estiverem disponíveis. Não tratar o relato do usuário como ausência de teste,
  nem inventar cobertura que não foi informada.

**Aceite:** decisão de compatibilidade escrita, referências reproduzíveis e lista
dos testes cuja regra obrigatória será substituída. Nada publicado no formato novo.

### B — Contêiner público, versão, sessão e persistência (risco alto)

**Objetivo:** guardar e recuperar assinaturas públicas sem enfraquecer os modos cifrados.

- Implementar leitura/escrita de assinatura em `none`, versão/capacidade e metadado.
- Manter rejeição de assinatura inserida na parte pública do modo `signatures`.
- Conferir limites, referências de assets, validação de imagens/SVG e IDs.
- Validar sessão pública, autosave, recuperação, nova revisão e backups.
- Na elevação de proteção, não deixar backup público recém-criado com as assinaturas
  que o usuário acabou de proteger; respeitar a regra existente para backups locais.
- Não introduzir senha fictícia, segredo padrão nem modo cifrado vazio para simular
  um público com assinatura. Não mudar Argon2id/AES, tolerância ou comportamento de senha errada.

**Aceite:** round-trip público com assinaturas preserva conteúdo/pixels; protegidos
continuam inacessíveis sem autorização; leitura por versão anterior é recusada
sem restauração destrutiva; falhas de gravação preservam uma revisão recuperável.

### C — Editor e conversão de modelos antigos (risco médio/alto)

**Objetivo:** usuário consegue escolher e o programa respeita a decisão.

- Implementar as escolhas e texto da recomendação, incluindo cancelamento.
- Mostrar uma vez no fluxo adequado e salvar o aceite; não repetir ao reabrir ou
  salvar novamente o mesmo modelo público já aceito.
- Permitir proteção posterior por ação explícita. Respeitar acesso/autorizações
  existentes ao editar modelos protegidos.
- Converter v3/v4 para público com assinaturas quando escolhido, sem mudar ordem
  de camadas, fundo, páginas, IDs ou visibilidade. Preservar a correção recente de
  `layer_order` ausente nos modelos v3 reais.
- Manter diário, publicação, verificação, retomada e limpeza de migração.
- Rever fluxo de duplicação/cópia: aceitação para o novo modelo não permite salvar
  sobre o original protegido aberto sem assinaturas.

**Aceite:** salvar/reabrir funciona nos três modos; público com assinatura não pede
senha nem perde assinatura; cancelamento não altera o original; proteger depois
funciona e mantém a renderização.

### D — Importação e exportação individual/lote (risco alto)

**Objetivo:** inclusão de assinatura nunca é confundida com proteção.

- Revisar UI e APIs juntas. Substituir inferências `mode != PUBLIC_MODE` usadas
  para decidir conteúdo por escolhas explícitas e inspeção do documento disponível.
- Público com assinatura: incluir mantém objetos/assets; excluir retira objetos,
  campos da tabela, referências e assets exclusivos de assinatura.
- Asset compartilhado com imagem comum não pode ser apagado se ainda é referenciado.
  Aplicar a política atual de não tratar imagem comum como assinatura.
- Importar público com assinatura: recomendar proteção local, permitir recusar e
  manter assinatura; não exigir senha do remetente para um arquivo público.
- ZIP legado deve preservar assinaturas ao escolher modo público: corrigir o
  parâmetro `include_signatures` em `import_legacy_document`.
- Protegidos mantêm desbloqueio e fluxo de transporte definido na seção 1.
- Cobrir lote misto, senha comum, falha parcial, conflitos, revisão alterada,
  cópia temporária e abertura de arquivo já pertencente à biblioteca.

**Aceite:** matriz de conteúdo/proteção passa nos três modos; nada some ou passa
para texto aberto por um valor padrão inadequado; origem recebida/exportada intacta.

### E — Textos, ajuda e traduções (risco baixo)

**Objetivo:** interface e documentação explicam a mesma política.

- Revisar avisos que dizem “exigem proteção” e documentação de campos públicos.
- Traduzir mensagens e recompilar EN/ES; validar também erros exibidos diretamente,
  não somente chamadas `tr()` reconhecidas pelo teste atual.
- Atualizar README, guia `.fornax`, especificação de formato, roteiro de testers e
  checklist de distribuição. Registrar a mudança como revisão das regras anteriores.
- Explicar senha opcional, assets públicos extraíveis, senha perdida, proteção
  existente e cópia sem assinaturas. Evitar promessa de segurança absoluta/autoria.
- Não refazer o tutorial de primeiros passos ou o layout por causa desta alteração.

**Aceite:** PT/EN/ES coerentes; documentação atual não apresenta a senha como
obrigatória para qualquer assinatura. Registros históricos permanecem identificados
como política anterior, sem apagar as evidências do que foi testado.

### F — Regressão e entrega (risco alto na verificação)

**Objetivo:** demonstrar preservação funcional e criptográfica.

- Rodar testes de contêiner, criptografia, sessão, editor, migração, importação,
  exportação, persistência sob falhas e ciclo de vida de dados protegidos.
- Rodar renderização/tabela/preview sem alterar sua lógica por conveniência do teste.
- Medir abrir/salvar/renderizar e geração comparando os mesmos dados; separar custo
  de desbloqueio. Não criar chamadas de derivação de senha para modelos públicos.
- Conferir manualmente o fluxo no Linux e repetir os cenários afetados no Windows.
  Não invalidar todos os testes anteriores por uma alteração localizada, mas não
  usar o teste Windows anterior como aprovação automática deste comportamento novo.
- Inspecionar pacotes públicos com assinatura e confirmar exposição intencional;
  nos protegidos, manter os testes de ausência de vazamento. Não aplicar expectativa
  de confidencialidade ao público escolhido conscientemente.

**Aceite:** testes aprovados, referências visuais equivalentes, falhas/limites
registrados e pontos manuais pendentes claramente identificados. Não encerrar o
plano como concluído apenas porque a interface conseguiu salvar uma vez.

## 5. Casos mínimos de regressão

1. Criar sem assinatura; adicionar assinatura; salvar público após aviso; reabrir
   e salvar novamente sem aviso repetitivo. Assinatura e coluna individual presentes.
2. Mesmo caso com assinatura oculta e com assinatura apenas no verso.
3. Cancelar aviso ou senha: original e aceite persistente inalterados.
4. Proteger posteriormente o público: senha passa a ser exigida; backup e autosave
   não introduzem cópia pública indevida após a transição.
5. Protegido existente: senha incorreta/adulteração continuam recusadas.
6. Abrir protegido sem assinaturas, adicionar outra assinatura e salvar sem senha:
   novo modelo, sem recuperar assinatura inacessível nem sobrescrever o original.
7. Converter pasta v3 sem `layer_order` e v4 de duas páginas para público com
   assinatura; igualdade visual e transação de limpeza/retomada preservadas.
8. Importar/exportar público com e sem inclusão de assinatura, inclusive ZIP legado.
9. Lote misto: público simples, público com assinatura, assinaturas protegidas e
   integral protegido, inclusive integral sem assinatura.
10. Leitor anterior diante do novo público com assinatura e de um `.bak` antigo:
    não restaura backup por confundir nova capacidade com corrupção.
11. Assinatura e imagem comum referenciando o mesmo asset; exclusão de assinatura
    não remove a imagem comum, e inclusão mantém os IDs/ordem das camadas.
12. Janela fechada, falha de gravação, reabertura, cópia temporária e importação com
    nomes conflitantes: ausência de perda de dados e de rebaixamento automático.

Arquivos de teste relevantes: `tests/test_fornax_container.py`,
`tests/test_fornax_crypto.py`, `tests/test_fornax_session.py`,
`tests/test_fornax_editor.py`, `tests/test_legacy_migration.py`,
`tests/test_fornax_import.py`, `tests/test_fornax_export.py`,
`tests/test_fornax_persistence_failures.py`, `tests/test_fornax_data_lifecycle.py`,
`tests/test_rendering_pipeline.py`, `tests/test_external_open.py`,
`tests/test_workspace_fields.py` e `tests/test_i18n.py`.

## 6. Controle de execução e passagem para outra IA

| Checkpoint | Estado | Evidência / ponto de retomada |
|---|---|---|
| A — Contrato e referências | Concluído | Contrato, versão 2 restrita ao público com assinatura, metadado, matriz e referências em `ETAPA_A_CONTRATO_PROTECAO_OPCIONAL_ASSINATURAS.md`; 25 testes de referência aprovados |
| B — Contêiner e sessão | Concluído | Versão 2 pública com assinaturas, aceite estrito, sessão/autosave e regressão dos modos protegidos registrados em `ETAPA_B_CONTAINER_E_SESSAO_ASSINATURAS_OPCIONAIS.md`; 104 testes direcionados aprovados |
| C — Editor e migração | Concluído | Recomendação opcional, cancelamento transacional, novo aceite por identidade, proteção posterior e migração v3/v4 registrados em `ETAPA_C_EDITOR_E_MIGRACAO_ASSINATURAS_OPCIONAIS.md`; 164 testes direcionados aprovados |
| D — Compartilhamento | Concluído | Inclusão de assinatura e proteção separadas na importação/exportação, lotes modernos e ZIP legado registrados em `ETAPA_D_COMPARTILHAMENTO_ASSINATURAS_OPCIONAIS.md`; 142 testes direcionados aprovados |
| E — Textos e traduções | Concluído | Política atual consolidada no README, guia, checklist e catálogos PT/EN/ES; evidências em `ETAPA_E_TEXTOS_TRADUCOES_E_DOCUMENTACAO.md`; 50 testes direcionados aprovados |
| F — Regressão e entrega | Concluído no escopo automatizado; validação nativa pendente | Evidências, correções e medições em `ETAPA_F_REGRESSAO_ASSINATURAS_OPCIONAIS.md`; testes manuais Linux/Windows continuam necessários antes da distribuição |

Ao terminar cada checkpoint, atualizar esta tabela e registrar: arquivos alterados,
decisões tomadas, comandos/testes e resultados reais, limitações, pendências e
próxima ação exata. Testes não executados não podem ser marcados aprovados.

Instrução de retomada para a IA executora:

> Leia este documento inteiro e as instruções do repositório. Confira o estado do
> código e execute o primeiro checkpoint pendente autorizado pelo usuário. Preserve
> alterações existentes. Não implemente apenas o botão: siga os contratos de
> persistência, compartilhamento e compatibilidade. Não faça testes mutantes na
> biblioteca real. Registre evidências antes de marcar o checkpoint concluído.

Referências anteriores: `history/PLANO_FORMATO_FORNAX_E_PROTECAO_ASSINATURAS.md`,
`history/ETAPA_2_ESPECIFICACAO_FORMATO_FORNAX.md`,
`history/ETAPA_4_REVISAO_FORNAX.md`, `history/ETAPA_4_5_FECHAMENTO_FORNAX.md`,
`docs/GUIA_MODELOS_FORNAX.md` e `docs/CHECKLIST_DISTRIBUICAO_FORNAX.md`.
Este novo plano substitui a obrigatoriedade de proteção apenas no escopo descrito;
não cancela as demais garantias ou pendências documentadas anteriormente.
