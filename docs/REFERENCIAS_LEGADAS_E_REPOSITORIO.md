# Referências preservadas e futura mudança de repositório

Revisão de 22/09/2026. O novo repositório ainda não foi criado. Não substituir URLs por endereços hipotéticos.

## Compatibilidade que deve permanecer

| Local | Referência | Motivo |
|---|---|---|
| `core/paths.py` | `com.leobelisario.ProjetoComSoc`, `ProjetoComSoc`, `.comsoc-migration.json` | Encontrar dados antigos e retomar a migração sem duplicá-los |
| `core/settings.py` | `Projeto ComSoc` / `MainApp` | Copiar preferências antigas sem sobrescrever valores atuais |
| `tests/test_data_migration.py` | Nomes e pastas antigos em fixtures sintéticos | Exercitar migração, conflitos, interrupção e preservação da origem |
| `history/`, `docs/historico/` | COMSOC, branches e caminhos das etapas anteriores | Registro histórico, não instrução atual |

Preservar também o AppId do Inno Setup, `com.leobelisario.FornaxForge`, o namespace das preferências atuais e o tipo MIME `application/x-fornax-template`. Trocar a marca ou o endereço do repositório não exige trocar essas identidades.

## Endereços a atualizar quando houver destino real

| Local | Endereço atual | Ação futura |
|---|---|---|
| `.git/config`, remoto `origin` | `https://github.com/LeonardoJoordan/projeto_comsoc.git` | Configurar o remoto da cópia destinada ao novo projeto, preservando o histórico conforme a estratégia escolhida |
| `instalador.iss`, `AppPublisherURL` | `https://github.com/LeonardoJoordan/projeto_comsoc` | Página do novo repositório |
| `instalador.iss`, `AppSupportURL` | Mesmo endereço, `/issues` | Canal real de suporte |
| `instalador.iss`, `AppUpdatesURL` | Mesmo endereço, `/releases` | Releases do novo repositório |

A varredura do código de execução não encontrou outros URLs do repositório antigo. Links de fornecedores e textos de licenças não devem ser alterados. Documentos históricos mantêm os links originais. Na separação, revisar novamente toda a árvore, habilitar/testar o canal privado descrito em `SECURITY.md` e executar o workflow remoto; a existência do YAML local não comprova execução no GitHub.
