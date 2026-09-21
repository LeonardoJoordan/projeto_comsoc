# Checkpoint E — textos, traduções e documentação

## Resultado

A documentação atual e a interface agora apresentam a mesma política:

- senha é recomendada para modelos com assinatura, mas não obrigatória;
- o usuário pode proteger assinaturas, proteger todo o modelo ou aceitar o
  armazenamento público;
- um `.fornax` público organiza o conteúdo, mas não cifra seus assets;
- assinaturas de um modelo público podem ser extraídas por quem recebe o arquivo;
- o aceite do remetente não é herdado silenciosamente ao incorporar o modelo;
- incluir assinaturas e escolher o modo de proteção são decisões independentes;
- proteção de armazenamento não prova autoria nem equivale a assinatura digital.

O guia também documenta a distinção entre contêiner público v1 sem assinatura
e público v2 com assinatura. O schema gráfico interno permanece v4.

## Documentos atualizados

- `README.md`: recursos e conversão de modelos antigos.
- `docs/GUIA_MODELOS_FORNAX.md`: modos, aceitação pública, compartilhamento,
  migração, limites e versões do contêiner.
- `docs/CHECKLIST_DISTRIBUICAO_FORNAX.md`: matriz manual dos quatro cenários de
  armazenamento e combinações de importação/exportação.

Os documentos em `history/` e `docs/historico/` foram preservados como evidência
das regras e decisões vigentes em suas respectivas etapas.

## Traduções

Os textos novos foram consolidados nos catálogos inglês e espanhol. Mensagens
obsoletas que diziam que todo modelo com assinatura exigia proteção foram
retiradas. Os arquivos `.qm` foram recompilados com `pyside6-lrelease`.

O teste de execução agora confirma diretamente:

- `Salvar sem senha` em inglês e espanhol;
- `Proteger modelo…` em inglês;
- `Importar assinaturas` em espanhol;
- cobertura de todas as chamadas `tr()` e preservação dos placeholders.

## Validação

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/test_i18n.py tests/test_fornax_editor.py \
  tests/test_fornax_export.py tests/test_fornax_import.py \
  tests/test_legacy_migration.py
```

Resultado: **50 testes aprovados**. `git diff --check` também passou. Uma busca
nos arquivos atuais, excluindo histórico, testes e ferramentas de captura, não
encontrou afirmação remanescente de que modelos com assinatura sempre exigem
senha ou proteção.

## Próximo ponto de retomada

Checkpoint F: executar a regressão integrada, comparar renderização e ciclo de
vida, revisar temporários/caches e registrar claramente os testes nativos que
continuam pendentes antes da distribuição.
