# Etapa 5 — dependências, licenças e preparação de releases

Registro de 22/09/2026. Ambiente de validação: Linux x86_64, Python 3.13.11.
**Situação: implementação e validação local realizadas; aceite de distribuição
multiplataforma ainda pendente.** Nenhum release foi publicado ou assinado.

## 5.1 — Conteúdo e dependências

- Runtime separado de build e ferramentas de validação em três arquivos de
  requisitos. Locks com versões transitivas e hashes para Linux/Python 3.13.
- Ambiente limpo sem metapacote PySide6 e sem Addons. O programa utiliza
  QtCore/Gui/Widgets/Network/Svg; a suíte passou com Essentials e Shiboken6.
- Preparação de conteúdo permitida por `scripts/release_tools.py`: Python
  produtivo, assets de runtime, fonte/OFL e documentos legais. Exclui testes,
  caches, planos, fontes de tradução e README.pdf. O build recusa venv com Addons.
- Compilação real Nuitka 4.0.7/GCC 13 concluída. Relatórios em
  `build/compilation-report.xml`, `build/nuitka-licenses.rst` e
  `build/release-inventory/`. O inventário não confunde o venv com o conteúdo do
  executável. Seis distribuições Python identificadas pelo compilador.
- Confirmada ausência de módulos de teste do editor, QtGraphs e QtQuick3D.
- Removido da saída o handler `qpdf`: Essentials inclui esse plugin, mas sua
  biblioteca QtPdf não está no pacote. O programa não importa PDF via esse
  handler; exportação usa pypdf e passou nos testes.
- Standalone iniciou em offscreen com dados/configuração vazios, permaneceu
  ativo durante o ensaio de 5 segundos e foi encerrado por `timeout` (124),
  sem traceback. Isso não é teste visual nem aprovação de instalação.
- Manifesto Flatpak atualizado de GNOME 47 para 50 e instalação pip sem rede,
  a partir de wheelhouse com hashes. Wheelhouse deve ser gerado para o SDK;
  não foi construído um Flatpak nesta execução.

## 5.2 — Licenças e fontes

- Licenças de ícones, GPL/LGPL, Python, OpenSSL, ICU, Inter e avisos dos pacotes
  Python preservados e incluídos na seleção de distribuição. Windows e Linux
  recebem a árvore `docs/licenses`, mantendo os caminhos documentados.
- Fontes oficiais QtBase, QtSvg, QtWayland, QtImageFormats e PySide/Shiboken
  6.11.0 baixados e verificados contra SHA-256 oficial: cerca de 71 MiB em
  `build/corresponding-sources/`. Manifesto com URLs/hashes preservado também
  em `docs/licenses/qt-6.11.0/sources.json`.
- 170 arquivos de avisos/atribuição preservados desses fontes. A cópia ampla
  dos avisos não substitui a revisão dos componentes efetivamente incorporados.
- SBOM upstream de cryptography preservado: OpenSSL 4.0.2 incorporado e 39
  entradas Rust. As 32 crates externas foram baixadas, verificadas pelos
  checksums do crates.io e tiveram 62 arquivos de aviso preservados. As sete
  crates internas seguem os avisos de cryptography.
- ICU 73.2 identificado pela API do binário entregue; licença oficial preservada.
  Avisos dos pacotes Ubuntu de bzip2, OpenSSL 3.0.13, xz/liblzma, SQLite e uuid
  copiados, com versões em `docs/licenses/linux-native/packages.json`.
  OpenSSL 3 do sistema e OpenSSL 4 de cryptography são componentes distintos.
- Ensaio limitado de substituição Qt: cópia do standalone com QtCore alterada
  apenas por adição de seção ELF via objcopy. A aplicação continuou iniciando.
  Demonstra ausência de bloqueio à troca binária nesse Linux; não é recompilação
  do Qt nem comprovação para Windows, AppImage ou Flatpak.

## 5.3 — Verificações automatizadas

- Workflow de manutenção com ações fixadas por SHA, acesso somente de leitura,
  testes, Bandit, pip-audit, Gitleaks e arquivamento de evidências. Não publica
  nada e não usa `pull_request_target`. Criado localmente, não executado no GitHub.
- Gitleaks 8.30.1 verificado por SHA-256: 239 commits e worktree examinados.
  Um alerta correspondia ao vetor determinístico público `wrapped_key` da
  especificação. Exceção restrita ao valor e caminho, mantendo regras padrão.
  Depois da triagem, nenhum segredo detectado; não é garantia de ausência.
- pip-audit apontou 8 entradas (6 IDs distintos) em pypdf 6.14.2. Atualização
  para 6.16.1; nova consulta sem vulnerabilidades conhecidas no runtime fixado.
  Isso não audita binários de sistema ou todas as bibliotecas Qt/ Rust.
- Bandit apontou parsing XML de SVG. Trocado por defusedxml 0.7.1, bloqueando
  DTD/entidades/recursos externos também em codificações que contornavam a
  busca textual inicial. Testes UTF-8/UTF-16/UTF-32 adicionados.
- Bandit sem achados médios/altos no runtime e nos scripts. Quatro achados
  baixos no runtime permanecem visíveis: tratamento tolerante de entrada em
  campo matemático, recuperação de migração, biblioteca e importação de modelos.
  Nenhuma regra foi globalmente desativada; revisar esses comportamentos se mudarem.
- Política `SECURITY.md` criada, sem SLA ou canal privado presumidamente ativo.
- Inventários contêm commit, indicação de árvore suja, arquivos/hashes e SBOMs
  CycloneDX; `signed: false` e `license_review_complete: false` são explícitos.

## Validação executada

- Suíte inicial sem Addons: 466 aprovados, 1 ignorado, 1 aviso, 12 subtestes.
- Suíte após atualização pypdf/parser e novos testes: **472 aprovados,
  1 ignorado, 1 aviso de depreciação Qt, 12 subtestes aprovados** (342,76 s).
- Quatro testes de ferramentas de empacotamento passaram após o ajuste final
  do plugin PDF (três já estavam incluídos na suíte acima).
- Runtime instalado com `--require-hashes` em outro venv limpo; imports do
  workspace/editor e inicialização do editor passaram. Lock dev validado com
  `pip install --dry-run --require-hashes`.
- Compilação Python, sintaxe shell, parsing YAML e `git diff --check` passaram.

## Checkpoints ainda necessários para aceitar a etapa inteira

1. Conferir correspondência final entre bibliotecas nativas, avisos e fontes em
   cada pacote. Completar fontes/receitas/modificações pertinentes fora do conjunto
   Qt já arquivado; incluir o código próprio do commit exato de release.
2. Definir entrega dos fontes junto ao release. Um arquivo apenas em `build/`
   local ainda não está disponível ao destinatário. Arquivos em build são
   temporários e devem ser arquivados antes de qualquer limpeza.
3. Gerar os locks/wheels e validar instaladores Windows e Flatpak; AppImage não
   foi gerado porque appimagetool não está disponível neste ambiente. Executar
   testes nativos/instalados, incluindo troca de bibliotecas Qt, no sistema alvo.
4. Executar o workflow no repositório oficial e habilitar/testar o canal privado
   de segurança. Definir assinatura de release/chave ou declarar ausência.
5. Antes de publicar, recalcular checksums dos instaladores finais e repetir a
   auditoria de vulnerabilidades/segredos sobre o commit de release limpo.

**Próxima retomada:** checkpoint 5.2, conferência das fontes/avisos e preparação
por plataforma. A Etapa 6 não deve ser considerada aprovada por este registro.
