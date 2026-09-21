# Validação Windows do formato FORNAX

Data: 20/09/2026. Base: commit `4f61385`, com as alterações locais desta revisão.
Estado: correções de persistência e validação automatizada Windows realizadas;
instalação e associação pelo Explorer ainda não aprovadas.

## Ambiente

- Windows 11, build 26200, volume C: NTFS.
- Python 3.13.11, PySide6 6.11.0, cryptography 50.0.1, pypdf 6.14.2.
- pytest 9.1.1, Nuitka 4.0.8, zstandard 0.25.0, compilador clang-cl.
- Inno Setup 6 instalado em `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`.
  A ausência no PATH não significava ausência da ferramenta.
- `python -m pip check`: nenhuma dependência incompatível.

## Problemas corrigidos

1. Gravação de `.fornax` falhava com `OSError: [Errno 9] Bad file descriptor`:
   seis chamadas de `fsync` usavam descritores reabertos somente para leitura.
   Os arquivos temporários agora são reabertos em `r+b`, preservando seu conteúdo
   e permitindo a sincronização no Windows. Abrange contêiner, backup,
   exportação individual/lote, importação e recuperação da biblioteca.
   Erros de sincronização continuam sendo propagados; não foram suprimidos.
2. Tradução ausente de `Modelo já presente na biblioteca: {nome}` em EN/ES:
   mensagens adicionadas e ambos os `.qm` recompilados com `pyside6-lrelease`.
3. Testes de links simbólicos agora pulam especificamente o erro Windows 1314
   (privilégio ausente), sem ocultar outros erros. O teste de limpeza verifica
   essa capacidade antes da migração, evitando aprovação sem exercitar o link.
4. Teste de largura dos botões do editor considera a largura mínima do texto
   calculada pelo Qt e verifica a centralização. O layout de produção permanece
   igual; fontes/estilos nativos podem exigir mais que os 65% preferenciais.

## Evidências

- Suíte geral com `QT_QPA_PLATFORM=offscreen` e `FORNAX_RUN_NATIVE_IPC=1`:
  **322 aprovados, 12 subtestes aprovados e 4 pulados em 193,83 s**.
  Três pulos por privilégio de link simbólico e um teste específico de Linux.
  Permanece um aviso preexistente de API Qt obsoleta em `table_panel.py:243`.
  Inclui persistência, criptografia, migração,
  importação/exportação, geração e IPC real entre processos Windows.
- Editor offscreen, sete módulos `unittest`: 61 aprovações e 2 pulados por fonte
  Amiri indisponível no sandbox; 63 testes executados em 9,829 s.
- Backend Qt `windows`, fora do sandbox: **20 testes aprovados em 5,63 s** em
  `test_app_instance_native`, `test_external_open`, `test_workspace_layout`,
  `test_dialog_buttons` e `test_wheel_focus`.
- Editor com backend Qt `windows`: **63 testes aprovados em 11,734 s**, inclusive
  os dois testes de Amiri, disponível nesse ambiente.
- Links/aliases fora do sandbox: 2 aprovados e 3 pulados em 1,02 s. A conta
  também não permite criar links simbólicos fora do sandbox; hard link testado.
- Persistência + traduções após os ajustes: 52 aprovados e 1 pulado em 7,00 s.
- As baterias se sobrepõem; não somar os números como cenários distintos.

Comandos principais (PowerShell, na raiz):

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
$env:FORNAX_RUN_NATIVE_IPC = '1'
.\.venv\Scripts\python.exe -m pytest -q tests -ra --durations=8 -o faulthandler_timeout=30

$env:QT_QPA_PLATFORM = 'windows'
.\.venv\Scripts\python.exe -m unittest features.editor.test_window_lifecycle features.editor.test_pages features.editor.test_masks features.editor.test_layers features.editor.test_groups features.editor.test_draw_shapes features.editor.test_canvas_edit
```

Para trocar entre sandbox e execução nativa, usar uma pasta `--basetemp` nova
e exclusiva: as permissões do diretório temporário criado pelo sandbox impediram
o acesso na primeira execução nativa. Esses erros eram de preparação do teste.
Os testes do editor usam imports relativos e foram executados como módulos
`unittest`; a tentativa inicial de coleta por caminhos no pytest falhou.

## Build Windows

Nuitka informou criação bem-sucedida de `build/main.dist/FORNAX_Forge.exe`, com
237 arquivos C compilados e 100 arquivos de assets incluídos. Foi necessário
executar fora do sandbox para acessar seu cache local. O invólucro PowerShell
reportou status 1 ao capturar a saída, apesar das mensagens finais de sucesso;
a presença do executável novo e o empacotamento posterior foram verificados.

- Executável: 37.378.560 bytes.
- SHA-256: `9514ED57992DC5EA4D7FBCEBC6D3B0EB8B9AB3C263573D546A0A5085F45AC3E4`.
- Instalador: `build/installer-windows/Instalador-FORNAX-Forge-1.0.0.exe`.
- Inno Setup: compilação bem-sucedida em 24,594 s; instalador de 33.206.994 bytes.
- SHA-256 do instalador: `0EE65D71512D17DF55783E2F22FC1015ED8E7CFEBF890A21BAB53CF87AA9CBDC`.
- Logs locais: `build/windows-validation-build.log` e
  `build/windows-validation-installer.log` (ignorados pelo Git).

## Pendências preservadas

- Instalar em conta limpa e validar o executável instalado, associação, ícone e
  duplo clique pelo Explorer, reinício por idioma, atualização e desinstalação.
  Testes nativos do código-fonte e compilação não aprovam esses itens.
- Links simbólicos: três cenários exigem conta com privilégio apropriado.
- FAT/exFAT, compartilhamento de rede e máquina modesta não avaliados aqui.
- Revisão visual manual, impressão e matriz dos outros sistemas permanecem.
- Checkpoint 3.11, avisos/licenças do pacote e demais pendências de 4.5 continuam
  conforme os relatórios anteriores; esta validação não libera a distribuição.
