# Checkpoint D — compartilhamento com assinaturas opcionais

## Resultado

Importação e exportação agora tratam separadamente:

1. se as assinaturas devem fazer parte da cópia;
2. se o destino será público, terá somente assinaturas protegidas ou será
   integralmente protegido.

Um `.fornax` público v2 pode ser exportado com suas assinaturas sem senha de
transporte ou sem assinaturas como um público v1. A escolha deixou de ser ignorada
pelo retorno antecipado do fluxo público.

Na importação, o aceite contido no arquivo recebido nunca é herdado. Se as
assinaturas forem mantidas em um modelo público, o destinatário precisa tomar uma
decisão local. Ele pode mantê-las sem senha, proteger somente as assinaturas ou
proteger todo o modelo. Para lotes protegidos, permanece a opção de usar uma senha
comum ou definir senhas individuais.

## API

`import_candidate` passou a receber decisões independentes:

- `include_signatures`;
- `target_mode`;
- `public_signatures_acknowledged`;
- senha de transporte, quando a origem precisa ser desbloqueada;
- senha local, somente quando o destino escolhido é protegido.

O comportamento anterior continua disponível quando `target_mode` não é
informado, preservando chamadas existentes.

`import_legacy_document` também recebeu `include_signatures` e o aceite público.
Assim, um ZIP legado com assinatura pode gerar um público v2, um protegido ou uma
cópia pública v1 sem assinatura.

## Retirada segura

A remoção foi centralizada em `core.model_document.without_signatures`.
Ela elimina:

- objetos de assinatura;
- IDs correspondentes em `layer_order`;
- o aceite público que perdeu sua finalidade;
- nomes de assets exclusivos de assinatura no snapshot informativo.

Se uma imagem comum e uma assinatura usam o mesmo asset, o asset continua no
pacote e no inventário. O escritor inclui somente arquivos ainda referenciados,
evitando bytes órfãos.

## Interface

- Modelos públicos v2 agora participam da pergunta sobre incluir assinaturas.
- A importação recomenda proteção local para assinaturas públicas recebidas.
- A escolha de proteção pode ser aplicada ao conjunto selecionado.
- Quando o destino é protegido, o usuário pode usar a mesma senha no lote ou
  definir uma senha por modelo.
- Senha de transporte continua restrita à leitura de pacotes protegidos; um
  público v2 não pede senha do remetente.

## Arquivos alterados neste checkpoint

- `core/model_document.py`
- `core/fornax_container.py`
- `core/fornax_export.py`
- `core/fornax_import.py`
- `features/workspace/main_window.py`
- `assets/translations/fornax_en_US.{ts,qm}`
- `assets/translations/fornax_es_ES.{ts,qm}`
- `tests/test_fornax_export.py`
- `tests/test_fornax_import.py`
- `history/PLANO_PROTECAO_OPCIONAL_ASSINATURAS.md`

## Validação

O grupo principal de compartilhamento terminou com **90 testes aprovados**:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/test_fornax_export.py tests/test_fornax_import.py \
  tests/test_fornax_persistence_failures.py tests/test_fornax_crypto.py
```

O grupo complementar de editor, migração, sessão, abertura externa,
biblioteca e traduções terminou com **52 testes aprovados**. Total direcionado:
**142 testes aprovados**. `compileall` e `git diff --check` também passaram.

Foram cobertos pacotes públicos v1/v2, protegidos parciais e integrais, retirada e
inclusão, destino protegido sem assinatura, senha errada, lotes, conflitos,
substituição transacional, ZIP legado e asset compartilhado.

## Próximo ponto de retomada

Checkpoint E: revisar todos os textos e documentos que ainda descrevem senha como
obrigatória para assinaturas, consolidar PT/EN/ES e atualizar os guias atuais sem
apagar os registros históricos das regras anteriores.
