# W6 — instalador Windows de teste

Data: 22/09/2026. **Primeira atualização real concluída; aplicação da correção abaixo aguardando UAC. Aceite W6 pendente.**

## Atualização no computador real autorizada pelo usuário

- Encontrada instalação administrativa 1.0.0 de 19/09 em `C:/Program Files/FORNAX Forge`, sem processo do aplicativo aberto.
- Instalador originalmente descrito abaixo aplicado com saída 0, sem reinício e sem abrir o programa. Log: `build/security/windows-w6-install.log`.
- Conferidos os 442 arquivos instalados contra os hashes de W5: nenhuma divergência. Atalhos de programa/licenças/desinstalação presentes; associação `.fornax` e comando com aspas conferidos no registro.
- Encontrados resíduos da instalação antiga, inclusive `qpdf.dll`. Corrigido ISS com `[InstallDelete]` para **apenas** `{app}/PySide6/qt-plugins/imageformats/qpdf.dll`; nenhuma remoção recursiva. Cópia recuperável guardada em `build/security/windows-w6-previous-files/qpdf.dll`.
- Adicionado teste de regressão do alvo restrito: 10 testes de integração/IPC aprovados em 0,92 s.
- **Instalador atual corrigido:** 30.864.030 bytes; SHA-256 `b4de1a1e3e677a2969477670d282082d425b25a64d88c29579df42cdf07d8b89`. Substitui o artefato inicial descrito abaixo. ISCC saiu com 0.
- Segunda instalação iniciada, mas ainda aguardando confirmação administrativa: processo `consent` presente e log `windows-w6-install-upgrade-fix.log` ainda inexistente. Não declarar a remoção de qpdf concluída antes de verificar saída e arquivos. Sessão de execução 23174 nesta conversa.
- Outros resíduos antigos (QtTest, Qt6Pdf, arquivos auxiliares) não foram removidos indiscriminadamente. Nenhuma desinstalação/limpeza de dados ou teste funcional da interface foi feito. Preservação integral dos dados não foi comprovada por comparação anterior/posterior.
- Próxima ação: usuário confirmar UAC, aguardar instalador, conferir saída 0, hashes dos 442 arquivos e ausência de qpdf. Depois continuar cenários W6; usar este host não equivale a máquina sem Python.

## Artefato inicial — histórico, substituído pela correção acima

### Tentativa após confirmação do usuário

A sessão 23174 terminou com `INSTALL_EXIT_CODE=2`, sem log de instalação.
Conferência posterior: 442 arquivos corretos, mas qpdf ainda presente; portanto
a correção ainda não foi aplicada. Repetida a execução do mesmo instalador
verificado, sessão 82872, log esperado
`build/security/windows-w6-install-upgrade-fix-retry.log`.
Na última observação havia processo Windows `consent` e nenhum log: aguarda
confirmação do UAC do próprio Windows, distinta da autorização da ferramenta.
Próxima ação: aguardar saída dessa sessão e verificar o plugin e os hashes.

- `build/installer-windows/Instalador-FORNAX-Forge-1.0.0.exe`
- Tamanho: 30.864.019 bytes.
- SHA-256: `e2fda680c85b795b107ea30441e5a058f6e0aad31c2dbe1373aa7a2880e8c776`.
- Assinatura Authenticode: `NotSigned`. Hash não é assinatura digital.
- Versão de teste 1.0.0 mantida do ISS; não foi escolhida uma nova versão final.
- AppId mantido: `{F0599521-F254-4070-91F0-A13FF6F788DA}`.

Compilado com Inno Setup **6.7.1**, ISCC já instalado em `C:/Program Files (x86)/Inno Setup 6/ISCC.exe`.
Código de saída explicitamente capturado: **0**. Log informa compilação em
20,141 segundos: `build/windows-w6-inno.log`.

```powershell
& 'C:/Program Files (x86)/Inno Setup 6/ISCC.exe' instalador.iss
```

Antes da geração, repetida auditoria W5: 442 arquivos e hashes aprovados.
O instalador usa o standalone atual, cujo executável tem SHA-256
`12a76f8384cda2d16a9932489c4260052df2350cd4acc0a6b92567ce98c86ed1`.
Hashes do ISS, instalador e executável em `build/security/windows-w6-sha256.csv`.

## Verificações executadas

- Leitura do ISS: instalação administrativa, diretório Program Files,
  comando de abertura com executável e argumento entre aspas, associação
  `.fornax`, sem associação explícita `.fornax.bak`, atalho de licenças.
- A configuração prevê preservação de dados na desinstalação normal/silenciosa;
  limpeza completa depende de opção explícita, inicialmente desmarcada.
  Isso é inspeção do código, não validação da desinstalação em execução.
- Testes `test_external_open.py` e `test_app_instance_native.py`:
  **9 aprovados em 0,88 s**, com `FORNAX_RUN_NATIVE_IPC=1`, Qt offscreen e
  armazenamento sintético isolado. XML: `build/security/windows-w6-integration-tests.xml`.
  Exercitam código-fonte/IPC local real; não validam duplo clique no Explorer
  nem o executável instalado.
- Nenhuma alteração no ISS ou no produto foi necessária para compilar.

## Limites e próxima retomada

Não foi executado o instalador, elevado o aplicativo, alterado registro,
associação, atalho ou instalação existente. Não foram usados dados reais.
Não foi identificada VM/conta descartável para o teste. A consulta a comandos
`Get-VM`, `vmrun` e `VBoxManage` não encontrou ferramentas no PATH; isso não
prova inexistência de virtualização instalada por outro caminho.

Permanecem todos os ensaios de instalação real da seção W6: atalhos/ícones,
Explorer, argumentos acentuados, instância única, editor com alterações,
atualização, cancelamento, conta comum, preservação na desinstalação e limpeza
explícita apenas em perfil descartável. W3, offline real W4 e runtime W5
também permanecem pendentes.

**Para concluir W6, indicar ou disponibilizar uma VM Windows descartável.**
Uma conta separada no mesmo computador não isola totalmente este instalador,
pois ele exige administrador e registra componentes por máquina.
W7 é o próximo checkpoint documental sequencial, mas não pode declarar
liberação final enquanto essas validações estiverem pendentes.
