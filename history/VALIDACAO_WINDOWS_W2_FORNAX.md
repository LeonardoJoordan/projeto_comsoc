# W2 — suíte automatizada Windows

**W2 concluído, com limitações de capacidade registradas.** Execução em 22/09/2026 por Codex, a partir de
`13ccde34b6758a1a430dc597176f7c96641f0e59`, branch `novo_main`.
Ambiente: `.venv-windows` criado em W1, Python 3.13.11 x64,
PySide6 Essentials/Qt 6.11.0, pytest 9.0.3 e pytest-qt 4.5.0,
Windows 11 build 26200, NTFS. Alterações de W1 preservadas.

## Isolamento da execução

- `conftest.py` ativa o isolamento antes da coleta/importação dos testes.
- `tests/isolated_environment.py` direciona dados, caches e temporários para
  uma pasta exclusiva em `build/security/windows-tests-data-*`.
- Preferências FORNAX e COMSOC usam arquivos INI explícitos nessa pasta,
  com fallback desativado. Foi demonstrado que apenas `setDefaultFormat`
  não muda o construtor `QSettings(organização, aplicativo)` no Windows.
- O subprocesso de encerramento abrupto ativa seu próprio perfil isolado.
  Seu inventário anterior ao carregamento protegido identifica por hash os
  ícones de tema e metadados iniciais; após o encerramento, arquivos desse
  perfil não podem conter o marcador privado nem diferir desse inventário.
  Principal e recuperação continuam sujeitos à verificação de contêiner cifrado.
- QApplication usa Fusion e Inter, como a inicialização produtiva. Janelas dos
  casos anteriores são liberadas por `deleteLater`/DeferredDelete. O acúmulo
  anterior tornava a atualização global de temas progressivamente mais lenta.
- Nenhum teste desta etapa usa a biblioteca real ou o registro de preferências
  do usuário. Perfis sintéticos permanecem em build para diagnóstico.

## Correções e regressões

1. **Fonte ausente:** a reconstrução da cena substituía a família declarada
   pela fonte disponível retornada por QFontInfo. Agora o nome original é
   preservado no documento; o Qt continua podendo usar fallback na renderização.
   Testados copiar/colar entre páginas e round-trip com família fictícia ausente.
2. **Callback após destruição:** o ícone de recolher a tabela do workspace
   continuava conectado ao gerenciador de tema depois de destruir o botão.
   A conexão agora termina com o widget; regressão destrói o workspace e emite
   uma mudança de tema, com exceções do event loop monitoradas por pytest-qt.
3. **Alinhamento dos controles:** o rótulo de destino agora ocupa a mesma coluna
   de grid do rótulo de formato, evitando deslocamento entre os campos.
   Geometria verificada automaticamente; não equivale à inspeção visual W3.
4. **Depreciação Qt:** duplicação de células passa AlignmentFlag à sobrecarga
   atual de setTextAlignment; a regressão confirma alinhamento combinado de texto.
   Nenhum filtro global de avisos foi adicionado.
5. **Traduções:** 23 mensagens recentes adicionadas a cada catálogo EN/ES;
   `.qm` recompilados com 917 traduções por idioma. Placeholders verificados.
6. **Capacidade de symlinks:** testes recentes deixam de esconder qualquer
   OSError; somente erro Windows 1314 e ausência explícita de implementação/
   suporte justificam pulo. Casos de empacotamento e limpeza com e sem links
   foram separados para manter a cobertura que independe desse privilégio.
7. **Persistência Windows real:** quatro cenários com arquivo público/protegido,
   somente leitura ou aberto por outro processo. Falha preserva os bytes e o
   conteúdo original, remove staging e permite salvar novamente após liberar
   a restrição. Nomes incluem acentos e espaços. `fsync` em `r+b` preservado.

## Execuções e evidências

- Primeira coleta: 482 testes, já incluindo dois testes novos de isolamento.
- Rodada inicial: 468 aprovados, 5 falhas, 9 pulados, 1 aviso, 12 subtestes,
  em 414,13 s; relatório `build/security/windows-w2-initial.xml`.
  A rodada terminou antes da tentativa de interrupção; não é uma suíte aprovada.
- Persistência Windows, isolamento, empacotamento e tabela: 18 aprovados e
  2 pulados em 2,47 s (`windows-w2-focused.xml`).
- Traduções, ciclo de vida, temporários, imagens, nomes e diálogos:
  37 aprovados e 4 pulados em 4,99 s (`windows-w2-regressions.xml`).
- Ciclo de vida ampliado após correções: 38 aprovados e 10 subtestes em 5,94 s
  (`windows-w2-lifecycle.xml`).
- Coleta final: **494 testes**, lista em `build/security/windows-w2-collection.txt`.
- Resultado final: **482 aprovados, 12 pulados e 12 subtestes aprovados em
  104,80 s, sem falhas, erros ou avisos de depreciação**. Código de saída 0.
  `build/security/windows-tests.xml` confirma os três casos de
  `test_app_instance_native` aprovados, incluindo comunicação entre processos.
  O JUnit contabiliza 506 entradas por incluir os 12 subtestes nos 494 casos.
- `git diff --check` e `pip check` aprovados. Avisos Git de conversão LF/CRLF
  são de configuração da cópia de trabalho, não falhas ou avisos do pytest.

Pulos da rodada final, identificados individualmente:

| Arquivo | Caso | Motivo |
|---|---|---|
| test_dynamic_images.py | test_resolver_rejects_symlink_that_leaves_selected_directory | Privilégio de symlink ausente, Windows 1314 |
| test_dynamic_images.py | test_resolver_accepts_subdirectory_and_internal_symlink | Mesmo privilégio |
| test_fornax_adversarial.py | test_export_cannot_replace_original_through_alias[symlink] | Mesmo privilégio; hard link passou |
| test_fornax_persistence_failures.py | test_cleanup_does_not_follow_replaced_parent_symlink | Mesmo privilégio |
| test_legacy_migration.py | test_symlink_in_legacy_model_is_rejected_without_touching_source | Mesmo privilégio |
| test_naming_engine.py | test_confined_output_rejects_escape_and_existing_external_symlink | Mesmo privilégio; caminho sem link tem teste separado |
| test_release_tools.py | test_stage_refuses_resource_symlinks | Mesmo privilégio |
| test_release_tools.py | test_artifact_inventory_refuses_external_symlink | Mesmo privilégio |
| test_temp_storage.py | test_cleanup_does_not_follow_external_symlink | Mesmo privilégio; limpeza sem link passou |
| test_linux_integration.py | test_mime_icon_does_not_lose_to_the_themes_generic_document | Específico GTK/GIO Linux |
| features/editor/test_canvas_edit.py | test_rich_amiri_uses_actual_font_for_vertical_alignment | Amiri indisponível neste ambiente |
| features/editor/test_canvas_edit.py | test_rich_placeholder_replacement_preserves_its_font_and_size | Amiri indisponível neste ambiente |

Comando final, na raiz do projeto:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
$env:FORNAX_RUN_NATIVE_IPC = '1'
.\.venv-windows\Scripts\python.exe -m pytest --import-mode=importlib -q tests features/editor --junitxml=build/security/windows-tests.xml -ra --durations=10 -o faulthandler_timeout=45
```

Os relatórios JUnit são locais e ficam em `build/security/`, ignorado pelo Git.
As baterias se sobrepõem e não devem ser somadas. A coleta final e o resultado
final substituem as contagens históricas para esta revisão do código.

## Limites

Esta é validação automatizada no Windows com Qt offscreen e IPC local real.
W3 (inspeção visual/fluxos nativos) e W4–W7 permanecem separados. Não houve
build, instalação, publicação, mudança de associação, teste FAT/exFAT/rede ou
impressão física nesta etapa. Os binários anteriores precisam ser reconstruídos
nos checkpoints apropriados para incorporar estas correções.
