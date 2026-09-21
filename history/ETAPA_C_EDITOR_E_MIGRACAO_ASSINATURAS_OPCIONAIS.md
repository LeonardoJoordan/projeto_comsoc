# Checkpoint C — editor e migração com assinaturas opcionais

## Resultado

O editor deixou de exigir senha para todo modelo que contenha assinatura. Quando
uma decisão ainda não existe, apresenta quatro caminhos claros:

- proteger somente as assinaturas;
- proteger o modelo inteiro;
- salvar com as assinaturas sem senha;
- cancelar sem alterar o modelo.

Ao escolher o caminho público, o aceite é inserido somente na cópia encaminhada
ao escritor. O documento mantido pela janela só passa a conter essa decisão depois
que o pacote foi publicado, verificado e reaberto. Cancelar ou falhar não modifica
o arquivo, a sessão ou o estado persistente do editor.

Um modelo público v2 já aceito pode ser salvo novamente sem repetir o aviso.
`Salvar como` remove o aceite herdado, cria uma identidade nova e exige nova
decisão. A duplicação segue a mesma regra.

## Proteção posterior

O menu de ações do modelo agora possui **Proteger modelo…**. A ação fica habilitada
para um `.fornax` público e permite proteger assinaturas ou todo o documento. Para
um documento sem assinatura, oferece proteção integral. A publicação conserva o
`model_id`, cria nova revisão e usa a regra transacional existente que evita deixar
as assinaturas abertas no backup criado durante a elevação de proteção.

## Modelos antigos

A conversão de pastas v3/v4 com assinatura agora aceita explicitamente o destino
público. Sem aceite, a API de migração recusa a operação. Com aceite, grava um
contêiner público v2, preservando assinatura oculta, IDs, `layer_order`, páginas e
assets. Os modos protegidos continuam com o comportamento anterior.

O diário, a publicação atômica, a retomada e a limpeza da origem não foram
alterados.

## Arquivos alterados neste checkpoint

- `core/legacy_migration.py`
- `features/editor/editor_window.py`
- `features/workspace/frontend.py`
- `features/workspace/main_window.py`
- `assets/translations/fornax_en_US.{ts,qm}`
- `assets/translations/fornax_es_ES.{ts,qm}`
- `tests/test_fornax_editor.py`
- `tests/test_legacy_migration.py`
- `history/PLANO_PROTECAO_OPCIONAL_ASSINATURAS.md`

## Validação

Primeiro grupo:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/test_fornax_editor.py tests/test_legacy_migration.py \
  tests/test_fornax_persistence_failures.py tests/test_fornax_container.py \
  tests/test_fornax_crypto.py tests/test_fornax_session.py
```

Resultado: **125 testes aprovados**.

Segundo grupo:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/test_model_library.py tests/test_workspace_fields.py \
  tests/test_fornax_data_lifecycle.py tests/test_external_open.py \
  tests/test_ui_assets.py
```

Resultado: **36 testes aprovados**, com um aviso preexistente de API Qt obsoleta
na duplicação de linhas da tabela. `compileall` de `core`, `features` e dos testes
alterados também foi concluído sem erros.

O teste dos catálogos encontrou os textos introduzidos neste checkpoint. As nove
mensagens foram traduzidas para inglês e espanhol e os arquivos `.qm` foram
recompilados. Resultado adicional: **3 testes de internacionalização aprovados**.

## Próximo ponto de retomada

Checkpoint D: separar completamente inclusão de assinatura e modo de proteção
nos fluxos de importação e exportação individual ou em lote, incluindo ZIP legado,
assets compartilhados, conflitos e senhas de transporte.
