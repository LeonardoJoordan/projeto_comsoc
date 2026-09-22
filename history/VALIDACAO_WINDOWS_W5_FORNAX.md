# W5 — build Windows e inspeção estática

Data: 22/09/2026. **Executável novo gerado; aceite funcional de W5 pendente.**

## Dependências reproduzíveis

- Locks runtime/build/dev com hashes arquivados em `history/windows-w5-locks/`.
- Lock dev conferido contra o ambiente W1–W4: 51 versões correspondentes,
  incluindo pip 25.3. Foi regenerado com a restrição do inventário W1 para não
  atualizar implicitamente pip para 26.2.1.
- Pacotes em `build/windows-wheelhouse/`; Nuitka veio como sdist verificado e
  teve wheel local construído, arquivado em `build/windows-built-wheels/`.
  A wheelhouse também contém pip 26.2.1 baixado na primeira resolução, não
  selecionado pelo lock final nem instalado no venv de build.
- Ambiente novo: `build/windows-build-venv`, instalado com `--no-index`,
  `--find-links` e `--require-hashes` a partir de `windows-build.lock`.
- `pip check`: aprovado. Sem metapacote PySide6 ou Addons.
- Hashes de pacotes/wheel construída e freeze em `build/security/windows-w5-*`.

## Compilação e evidências

Executado `script_nuitka.py` pelo Python do novo ambiente, MSVC cl 14.5,
quatro jobs, 241 unidades C compiladas. A primeira tentativa falhou ao gravar
no cache Nuitka fora do sandbox. A repetição autorizada concluiu compilação,
linkedição, ícone, relatórios e inventário.

O executor da chamada PowerShell reportou código 1 mesmo com o log final de
sucesso do Nuitka e do script, sem traceback nessa repetição. Não se registra
um código zero de compilação que não foi observado: a comprovação adicional
é o binário novo, os relatórios finais e a auditoria estática (esta saiu com 0).
Logs: `build/windows-w5-build.log` e `build/windows-w5-build-retry.log`.

- Executável: `build/main.dist/FORNAX_Forge.exe`, PE AMD64, 23.630.848 bytes.
- SHA-256: `12a76f8384cda2d16a9932489c4260052df2350cd4acc0a6b92567ce98c86ed1`.
- Pacote completo: 442 arquivos, 110.041.509 bytes.
- Relatórios: `build/compilation-report.xml`, `build/nuitka-licenses.rst`,
  `build/release-inventory/{inventory.json,SHA256SUMS,files.cdx.json,components.cdx.json}`.
- Worktree contém alterações W1–W5 não commitadas; o inventário registra isso.
  Comparados 441 fontes/recursos atuais com o staging efetivamente compilado:
  nenhuma diferença, excluindo avisos de pacotes regenerados do venv.

Auditoria reproduzível:

```powershell
.\build\windows-build-venv\Scripts\python.exe tools/audit_windows_standalone.py
```

Resultado: zero falhas, todos os hashes e conjunto de arquivos conferidos.
Presentes Python DLL, qwindows, fonte UI, traduções EN/ES e documentos essenciais.
Ausentes módulos de teste no relatório Nuitka e plugin `qpdf.dll` no pacote.
Licenças Qt preservam caminhos upstream contendo `tests`/`tools`; são evidências
legais, não testes executáveis, e foram comparadas com a origem. Não foram
removidas para satisfazer uma busca genérica por nomes de diretório.

Distribuições confirmadas pelo relatório: PySide6_Essentials 6.11.0,
shiboken6 6.11.0, cryptography 50.0.1, cffi 2.1.1, defusedxml 0.7.1 e
pypdf 6.16.1. Isso não substitui revisão completa das dependências nativas e
licenças; o inventário não declara revisão legal completa ou assinatura digital.

Testes auxiliares de distribuição: **4 aprovados, 2 pulados** (links simbólicos
sem privilégio Windows), XML em `build/security/windows-w5-release-tests.xml`.

## Pendências e retomada

Não foi aberto o executável, nem testado em VM/máquina sem Python. Não foi
validada ausência de DLL faltante em execução, nem repetidos os cenários
W3/W4 no standalone, idiomas/reinício/IPC ou impressão. Os recursos presentes
no disco não comprovam funcionamento visual. W3 e parte offline de W4
continuam pendentes.

O executável precisa da pasta `main.dist` completa; não distribuir só o `.exe`.
Nenhum instalador novo foi gerado. Próximo checkpoint sequencial: W6, geração
e instalação de teste, preservando as pendências anteriores. A aprovação final
de W5 exige validação real do standalone fora do ambiente de desenvolvimento.
