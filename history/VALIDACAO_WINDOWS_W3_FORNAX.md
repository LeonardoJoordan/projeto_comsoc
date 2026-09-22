# W3 — preparação e impedimento de inspeção nativa

Data: 22/09/2026. Etapa iniciada, **não concluída**.

## Preparação verificada

- Iniciador: `tools/windows_visual_validation.py`.
- Biblioteca, temporários e preferências INI em `build/security/windows-w3-profile`.
- IPC com nome exclusivo desse perfil: não encaminha arquivos à instância de uso real.
- Remove `QT_QPA_PLATFORM` e `FORNAX_RUN_NATIVE_IPC` antes da inicialização.
- O reinício por idioma usa `sys.argv[0]`, portanto reexecuta esse iniciador e reaplica o isolamento. Esse caminho foi inspecionado no código; o reinício visual ainda não foi testado.
- Verificação executada com Python da `.venv-windows`: caminhos de biblioteca e QSettings pertencem ao perfil; nome IPC começa com `fornax-w3-`. Resultado: aprovado.

## Impedimento

A skill computer-use foi carregada, mas `sky.list_windows()` retornou:

> Computer Use native pipe is unavailable: failed to connect native pipe: O sistema não pode encontrar o arquivo especificado. (os error 2)

Não houve captura de tela, interação nativa ou aprovação visual. Nenhuma biblioteca real foi usada. Não foi iniciado aplicativo sem possibilidade de acompanhá-lo. As verificações de W2 não substituem W3.

## Retomada

Restabelecer o controle nativo de janelas na sessão e executar:

```powershell
.\.venv-windows\Scripts\python.exe tools/windows_visual_validation.py
```

Preparar a massa sintética e executar todos os itens da seção W3 do plano. Permanecem pendentes: fluxos de importação/exportação, proteção, editor, geração, tutorial, idiomas, temas, escalas e screenshots. Impressão física também não foi testada. Não avançar para W4 como se W3 estivesse aprovado.
