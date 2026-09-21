# Checkpoint B — contêiner e sessão com assinaturas opcionais

## Resultado

O núcleo agora aceita assinaturas em modelos públicos somente no contêiner
`.fornax` versão 2. A versão 1 continua sendo gravada para modelos públicos
sem assinatura e para os modos protegidos `signatures` e `full`.

O documento público assinado precisa conter o aceite persistente:

```json
"protection_preferences": {
  "public_signatures_acknowledged": true
}
```

O escritor recusa assinaturas públicas sem esse aceite. Quando a última
assinatura é removida, o escritor elimina o metadado e volta a produzir a versão
1. Salvamentos protegidos também removem o metadado, pois a escolha pública deixa
de se aplicar.

## Compatibilidade e limites

- O parser aceita apenas as versões 1 e 2.
- A versão 2 é exclusiva do modo público e exige ao menos uma assinatura.
- A versão 1 pública continua recusando assinaturas.
- Modos protegidos continuam na versão 1, com KDF, AAD e criptografia
  inalterados.
- A versão real do descritor passou a compor o cabeçalho serializado; isso evita
  interpretar um pacote v2 como v1.
- Sessões públicas abrem, salvam e recuperam snapshots v2 preservando assinaturas
  e assets.
- O aviso e a escolha do usuário ainda pertencem ao checkpoint C; este checkpoint
  fornece a regra segura exigida pela interface.

## Arquivos alterados

- `core/model_document.py`
- `core/fornax_container.py`
- `tests/test_fornax_container.py`
- `tests/test_fornax_crypto.py`
- `tests/test_fornax_session.py`
- `history/PLANO_PROTECAO_OPCIONAL_ASSINATURAS.md`

## Validação

Comando final:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/test_fornax_container.py \
  tests/test_fornax_crypto.py \
  tests/test_fornax_session.py \
  tests/test_fornax_persistence_failures.py
```

Resultado: **104 testes aprovados**.

Foram cobertos round-trip público v2, assinatura visível e oculta, assets,
aceite ausente ou inválido, limpeza do metadado, rejeição da matriz de versão
inválida, preservação da versão 1 protegida, sessão, nova revisão, autosave,
backups e falhas transacionais existentes.

## Próximo ponto de retomada

Checkpoint C: implementar no editor o aviso recomendando proteção, as escolhas
de proteger, continuar sem senha ou cancelar, e a persistência do aceite somente
depois de uma gravação bem-sucedida. Também aplicar as regras de reset em
`Salvar como`, duplicação e importação previstas no contrato.
