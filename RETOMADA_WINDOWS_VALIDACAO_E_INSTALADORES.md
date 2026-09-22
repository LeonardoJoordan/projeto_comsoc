# Retomada no Windows — validar o FORNAX Forge e preparar os instaladores

Documento de passagem de contexto, criado em 22/09/2026. Destinatário: outra instância do Codex trabalhando com Leonardo no Windows.

## Instrução para a próxima instância

Leia este documento e as referências abaixo antes de alterar o projeto. Execute os checkpoints na ordem, registre resultados e corrija os problemas encontrados. O objetivo é validar a versão atual no Windows e produzir um instalador testado, com evidências e documentação de distribuição. Não publicar releases nem criar/migrar o repositório automaticamente.

Não considerar uma etapa aprovada apenas porque outra etapa passou. Não repetir pedidos de decisões já tomadas. Faça escolhas técnicas rotineiras e correções necessárias dentro deste escopo; peça ao usuário apenas informação realmente ausente ou participação em testes manuais que você não consiga realizar. Não usar a biblioteca real como massa de teste, não apagar modelos nem enfraquecer proteção para fazer testes passarem.

Ao interromper o trabalho, atualize a seção **Registro de execução e próxima retomada** com o último checkpoint concluído, arquivos alterados, comandos, resultados e o próximo passo exato. Não depender do histórico desta conversa.

## 1. Contexto e decisões já estabelecidas

- Aplicativo desktop Python/PySide6: **FORNAX Forge**, anteriormente Projeto COMSOC. Runtime atual usa **PySide6_Essentials**, sem metapacote PySide6/Addons. Não é PySide5.
- Desenvolvedor: **Leonardo Joordan Belisário Lima da Silva**. Código/documentação próprios: **GPL-3.0-only**. Licenças e autoria de terceiros permanecem separadas. Não declarar auditoria independente, certificação ou homologação governamental.
- Aplicativo offline, sem conta, telemetria, nuvem ou atualização automática. Releases serão disponibilizados no GitHub. Ferramentas de desenvolvimento podem acessar a rede; não confundir com runtime.
- Cada modelo da biblioteca é `.fornax`; exportação individual usa `.fornax`, exportação de vários modelos usa ZIP contendo `.fornax`. Importação aceita também ZIPs legados. Extensão não é criptografia.
- Modos: público, assinaturas protegidas, modelo integralmente protegido. Senha de 8 a 64 caracteres. **Proteção de assinaturas é recomendada, não obrigatória**: preservar escolha explícita de armazenamento público.
- Selecionar modelo não deve disparar pergunta automática de senha. Assinaturas protegidas abrem uma cópia sem assinaturas; proteção integral não expõe o conteúdo. Botão **Desbloquear modelo / Bloquear modelo** controla acesso.
- A cópia sem assinaturas não substitui o original protegido. Senha de transporte não deve permanecer como senha alternativa da cópia importada. Trocar entre modos protegidos preserva a senha; alterar senha exige a atual e confirmação da nova.
- Timer: cinco minutos após sair do modelo, não cinco minutos de inatividade dentro dele. Conferir comportamento atual documentado e testes.
- Nomes com pontos, acentos e espaços devem permanecer legíveis; identidade do modelo não deve depender de rótulos de interface.
- Novo repositório FORNAX é uma etapa futura. Preservar AppId Inno, namespace de preferências, tipo MIME e aliases COMSOC de migração. Não inventar URLs do novo repositório.

### Referências para leitura

1. `PLANO_ADEQUACAO_SEGURANCA_LICENCAS_FORNAX.md` — plano completo e limites de conclusão.
2. `history/ETAPA_5_DISTRIBUICAO_E_DEPENDENCIAS.md` e `history/ETAPA_6_DOCUMENTACAO_E_VALIDACAO.md` — evidências recentes e pendências.
3. `history/VALIDACAO_WINDOWS_FORNAX.md` — teste Windows anterior, de 20/09; não valida as alterações posteriores.
4. `docs/RELEASE.md`, `docs/CHECKLIST_DISTRIBUICAO_FORNAX.md`, `docs/THIRD_PARTY_LICENSES.md` — build, matriz nativa e obrigações ainda abertas.
5. `docs/GUIA_MODELOS_FORNAX.md`, `docs/MODELOS_FRENTE_VERSO.md`, `docs/PRIVACIDADE_E_ARMAZENAMENTO.md` e `SECURITY.md`.
6. `docs/REFERENCIAS_LEGADAS_E_REPOSITORIO.md`, `docs/ASSET_PROVENANCE.md`, `LICENSE`, `NOTICE`, `AUTHORS.md`, `TRADEMARKS.md`.

## 2. Estado real de validação

**Linux não está totalmente aprovado para distribuição.** A suíte local, o IPC Linux e um standalone compilado foram exercitados. AppImage/Flatpak instalados e sua integração no desktop não foram aprovados nesta rodada. Não escrever que falta somente Windows.

| Evidência | Resultado conhecido | Limite |
|---|---|---|
| Referência inicial da revisão | 423 aprovados, 1 pulado, 1 aviso, 12 subtestes | Base histórica |
| Suíte completa da etapa 6 em Linux | 473 aprovados, 1 pulado, 1 aviso, 12 subtestes; 333,81 s | Anterior aos ajustes de interface mais recentes |
| IPC Linux separado | 3 aprovados, socket local real | Não testa Explorer/instalador Windows |
| Importação/exportação após correção de mensagem | 28 aprovados | Testes direcionados |
| Redesenho dos seletores | 80 aprovados, incluindo persistência e fluxos de transferência | Mudanças de layout posteriores receberam testes direcionados |
| Avisos padronizados e seletores, última rodada | 7 aprovados | Não é suíte completa atual |
| Standalone Linux | Compilado e iniciado offscreen; inicialização observada sem AF_INET/AF_INET6 | Não é teste de todos os fluxos nem pacote instalado |
| Windows em 20/09 | Correções de fsync, testes e build documentados | Instalação/associação ainda pendentes; dependências mudaram depois |

Não somar esses números: vários testes se repetem. Recolher a suíte atual, executar e registrar a contagem real. Um aviso conhecido está em `features/spreadsheet/table_panel.py`, sobre a sobrecarga inteira depreciada de `QTableWidgetItem.setTextAlignment`; examinar sem ocultar avisos globalmente.

## 3. Alterações recentes que exigem atenção especial no Windows

### Importação/exportação

- Corrigido `KeyError: 'arquivo'` ao montar log de sucesso do lote. O arquivo podia ter sido gravado antes do falso alerta. Corrigida também a mensagem do importador de ZIP legado.
- Arquivos: `features/workspace/main_window.py`, `export_models_dialog.py`, `import_models_dialog.py`, `transfer_dialog.py`.
- Seletores têm busca, contador, **Selecionar todos** (inclui modelos ocultos pelo filtro), **Limpar seleção** e resumo. Busca não elimina escolhas.
- Importação: conflitos desmarcados inicialmente; **Criar cópia / Substituir** diretamente nas linhas. A primeira linha contém ações para todos os modelos repetidos; não reapresentar um bloco separado abaixo da tabela nem comboboxes de conflito.
- Botões iguais, distância de 8 px; contêiner transparente. O padding das células antes comprimia os botões: não verificar apenas os valores nominais, observar a geometria renderizada.
- Nomes usam reticências e tooltip completa; coluna não deve esmagar os controles de ação. Proteção/formato também tem tooltip.
- Botão Continuar fica desabilitado sem seleção. Ações de lote não devem iniciar importação nem substituir modelos sem seguir o fluxo de confirmação existente.

### Avisos/erros/confirmações

- Centralizados em `core/dialog_buttons.py` pelo filtro instalado em `features/workspace/main.py`.
- QMessageBox ganhou título interno, margens consistentes e largura base de 480 px quando a tela comporta; altura deve acomodar o conteúdo. Não exigir altura idêntica para textos diferentes.
- Botões sem ícones, dimensões iguais, azul/tema para aceite, neutro para cancelar com hover vermelho; escolhas adicionais neutras. Botão único e conjunto centralizados.
- Erros críticos com texto maior que 1000 caracteres mostram resumo e preservam texto completo em detalhes expansíveis.
- Preservar papéis, valor retornado, botão padrão, Esc, fechamento e sinais. Testar chamadas estáticas `QMessageBox.information/question/critical` e caixas com botões personalizados.
- Não aplicar o layout de aviso indiscriminadamente ao tutorial, impressão, seletor de arquivos ou outras janelas próprias.
- Confirmar detalhes e título após trocar idioma. As novas frases usam `tr`, mas não presumir que EN/ES já estejam traduzidos/compilados.

## 4. Checkpoints de execução

### W1 — Conferir árvore e preparar ambiente limpo

- [x] Ler `AGENTS.md`, se existir, e inspecionar `git status`, branch e commit. Preservar alterações do usuário. Verificar se os arquivos novos deste trabalho chegaram ao Windows; não confiar só no nome da branch.
- [x] Registrar Windows/build, arquitetura, Python, Qt, DPI, compiladores e ferramentas.
- [x] Criar venv novo; não copiar `.venv` nem binários Linux. Usar Python 3.13 x64 como referência atual.
- [x] Instalar `requirements-dev.txt`; consultar os arquivos atuais para versões. Não atualizar dependências indiscriminadamente.
- [x] Confirmar `pip check` e ausência de PySide6 metapacote/Addons. Não usar lock Linux como lock Windows.
- [x] Localizar Inno Setup 6 e compilador suportado pelo Nuitka. Em teste anterior, ISCC existia em `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`, fora do PATH; conferir antes de declarar ausência.

Exemplo PowerShell, na raiz (ajustar launcher Python se necessário):

```powershell
py -3.13 -m venv .venv-windows
$python = Join-Path $PWD '.venv-windows\Scripts\python.exe'
& $python -m pip install -r requirements-dev.txt
& $python -m pip check
& $python -m pip list
New-Item -ItemType Directory -Force build\security | Out-Null
```

**Aceite W1:** árvore identificada, ambiente reproduzível e ferramentas localizadas, sem modificar os dados reais.

### W2 — Suíte automatizada e regressões

Executar em perfil/VM descartável ou com armazenamento de teste isolado. Alterar APPDATA não isola sozinho o registro QSettings do Windows; testes de preferências devem usar fixtures temporários. Inspecionar isso antes da execução em conta com dados importantes.

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
$env:FORNAX_RUN_NATIVE_IPC = '1'
& $python -m pytest --import-mode=importlib --collect-only -q tests features/editor
& $python -m pytest --import-mode=importlib -q tests features/editor --junitxml=build/security/windows-tests.xml
```

- [x] Registrar falhas, pulos e avisos individualmente. Link simbólico sem privilégio Windows pode justificar pulo; não ocultar falhas genéricas de filesystem.
- [x] Cobrir `test_fornax_export`, `test_fornax_import`, `test_fornax_persistence_failures`, `test_transfer_dialogs`, `test_dialog_buttons`, `test_data_migration`, `test_legacy_migration`, `test_fornax_data_lifecycle`, `test_temp_storage`, `test_app_instance_native`, `test_release_tools`.
- [x] Conferir gravação/fsync em `r+b`, substituição atômica, arquivo aberto por outro processo, backup e recuperação.
- [x] Corrigir a causa das falhas e adicionar regressão quando justificar. Executar testes afetados e, ao terminar mudanças funcionais, a suíte completa novamente.

**Aceite W2:** nenhuma falha sem resolução; pulos justificados por capacidade real e rastreados; resultados atuais arquivados. Não aprovar IPC se foi pulado.

### W3 — Validação visual e funcional pelo código no Windows

Remover as variáveis de execução headless antes de abrir a interface:

```powershell
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
Remove-Item Env:FORNAX_RUN_NATIVE_IPC -ErrorAction SilentlyContinue
& $python main.py
```

Usar biblioteca sintética com: modelo público de uma página, frente/verso, assinatura pública aceita, assinatura protegida, proteção integral, pasta legada válida e duplicatas com nomes longos/acentuados. Usar imagens e assinaturas fictícias.

- [ ] Testar 100%, 125% e 150% de escala quando disponíveis, janela menor e maximizada; temas escuro e claro. Registrar quais combinações realmente foram usadas.
- [ ] Importar `.fornax` único, lote ZIP atual e ZIP legado. Nomes repetidos: ignorar, criar cópia, substituir, cancelar nome/senha. Verificar origem preservada e destino correto.
- [ ] Exportar um, vários e seleção filtrada; abrir o ZIP final e importar de volta. Confirmar log e sucesso, ausência do erro `'arquivo'`, fontes/imagens/páginas/nomes e assinaturas esperadas.
- [ ] Testar proteção e senhas: público, parcial, integral, com/sem assinaturas, senha errada, cancelamento, senha comum falhando para parte do lote. Conferir senha local nova no destino e rejeição da antiga senha de transporte quando diferente.
- [ ] Conferir os seletores recentes: fundos dos botões, 8 px entre ações, texto completo nos botões, reticências/tooltip dos nomes, primeira linha de lote alinhada, busca e contador. Selecionar todos inclui itens fora do filtro.
- [ ] Avisos: “Importação concluída / Importados: 3”, confirmação de limpar página, erros curtos e longos com detalhes, três ou quatro escolhas, Enter/Esc e fechamento pelo X. Conferir que nenhuma resposta foi alterada pela padronização.
- [ ] Testar PT/EN/ES e recompilar `.qm` conforme ferramentas do projeto se houver traduções ausentes; manter placeholders corretos.
- [ ] Biblioteca: último modelo, ordem/nome, bloquear/desbloquear, retorno antes/depois dos cinco minutos. Modelo `2.2.1 - Nome` não pode virar `221` no rótulo.
- [ ] Editor: texto/Inter, placeholders, trechos opcionais, assinatura por coluna, imagem variável, máscaras, grupos, seleção/redimensionamento, frente/verso, salvar/reabrir, desfazer/refazer e fechamento.
- [ ] Prévia e geração: PNG, PDF por item, PDF agrupado, imposição; conferir conteúdo e páginas. Imprimir prova duplex se houver impressora; caso contrário registrar impressão física como não testada.
- [ ] Tutorial primeiros passos: alvos, modal arrastável, alinhamento e geração final, sem bloquear o controle solicitado.

**Aceite W3:** fluxos e layout utilizáveis no Windows nativo; screenshots sintéticos e problemas/correções registrados. Não declarar inspeção visual se só houver offscreen.

### W4 — Proteção, persistência e operação offline

- [ ] Arquivo somente leitura, nome com espaços/acentos, destino existente e cancelamento: sem substituir original indevidamente.
- [ ] Simular encerramento inesperado em biblioteca descartável: recuperar principal/backup/autosave sem expor assets protegidos em claro. Não interromper a máquina com dados reais.
- [ ] Após desbloqueio, cancelamento, exportação e reinício, examinar temporários, caches, recuperações e logs. Material PNG/PDF deliberadamente gerado é legível e não herda a senha do modelo.
- [ ] Checar ausência de senhas/conteúdo de documentos nos logs; limpeza limitada ao diretório temporário do aplicativo.
- [ ] Executar sem conexão. Quando possível, observar conexões com ferramenta do SO: diferenciar IPC local, ações explícitas do usuário e tráfego de ferramentas de desenvolvimento.
- [ ] NTFS é referência. FAT/exFAT e rede precisam de ensaio próprio: publicação com hard links pode não ser suportada; não prometer suporte sem evidência nem inventar fallback que enfraqueça a transação.

**Aceite W4:** proteções e recuperação mantidas; limitações reais registradas, sem promessa de apagar fisicamente RAM/swap/disco.

### W5 — Build Windows e inspeção do standalone

- [x] Gerar locks com hashes no Windows para runtime/build/dev usados; arquivar wheels e versões. Reinstalar o lock em venv limpo de build e executar `pip check`.
- [x] Compilar com `script_nuitka.py`. Ele recusa PySide6/Addons; usa árvore permitida, exclui testes/caches/histórico e gera inventários em `build/`.
- [ ] Abrir `build/main.dist/FORNAX_Forge.exe` diretamente em ambiente sem Python instalado, preferencialmente VM. Não usar apenas o programa pelo código como validação do binário.
- [ ] Repetir os cenários críticos W3/W4 no standalone: importação/exportação, senha, editor, geração, reinício por idioma e IPC.
- [ ] Conferir ícone, Inter incorporada, SVGs, traduções, Qt plugins e ausência de DLL faltante. O plugin qpdf não é necessário à geração via pypdf e é removido de forma restrita pelo build.
- [ ] Inspecionar relatórios Nuitka, dependências efetivamente incluídas, SHA256SUMS e SBOM. Pacote instalado no venv não significa biblioteca distribuída.

```powershell
& $python -m piptools compile --generate-hashes --output-file build/windows-runtime.lock requirements.txt
& $python -m piptools compile --generate-hashes --allow-unsafe --output-file build/windows-build.lock requirements-build.txt
# Usar um venv limpo instalado pelo lock para a compilação final.
& $python script_nuitka.py
```

**Aceite W5:** executável real funciona fora do ambiente de desenvolvimento; composição e build registrados. Não baixar ferramentas executáveis de origem não verificada para contornar falha.

### W6 — Instalador Inno Setup e integração real

A geração de instalador de teste faz parte deste checkpoint; instalador final só é aprovado após instalar e testar. Confirmar a versão com o responsável se não houver decisão registrada: `instalador.iss` historicamente declara `1.0.0`. Não mudar AppId para “atualizar o nome”.

```powershell
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' instalador.iss
```

- [ ] Instalar em VM/conta limpa; verificar atalhos, ícone, nome e local do aplicativo.
- [ ] No Explorer, `.fornax` com espaços e acentos mostra ícone correto e abre o programa com argumento íntegro. `.fornax.bak` não deve ser associado como modelo principal.
- [ ] Duplo clique com programa fechado/aberto: uma única instância, sem erro de QLocalSocket já destruído. Com editor alterado aberto, preservar trabalho pendente.
- [ ] Arquivo já dentro da biblioteca: selecionar sem perguntar para adicionar. Externo: oferecer incorporação; recusar permite uso temporário sem reaparecer na próxima execução, aceitar copia sem alterar origem.
- [ ] Reinício por idioma não reimporta argumentos antigos nem perde instância.
- [ ] Atualizar instalação existente preservando modelos/configurações. Instalar com aplicativo/editor aberto respeita cancelamento e proteção de trabalho.
- [ ] Desinstalação normal preserva dados. Testar remoção completa somente em perfil descartável e após opção explícita. Não apagar dados reais ou de outro usuário.
- [ ] Verificar associação/desinstalação e permissões em conta comum. Não mascarar comportamento real de instalações por usuário/máquina.
- [ ] Arquivos LICENSE/NOTICE/AUTHORS/TRADEMARKS/SECURITY, guias e `docs/licenses` presentes e acessíveis no pacote instalado; atalho de licenças abre o documento certo.

**Aceite W6:** matriz Windows do checklist preenchida com evidências da instalação real, não apenas compilação do ISS.

### W7 — Fechamento documental, legal e artefatos finais

- [ ] Conferir avisos/fontes/receitas correspondentes às DLLs e componentes realmente distribuídos no Windows. Os avisos Linux em `docs/licenses/linux-native` não substituem obrigações dos binários Windows.
- [ ] Não considerar fontes Qt apenas baixados no computador como entregues: preparar sua disponibilização junto ao release, além do código próprio exato. Consultar `docs/RELEASE.md` e registrar lacunas.
- [ ] Preservar possibilidade de substituição/recombinação prevista pelas licenças aplicáveis; testar em cópia descartável e documentar limites. Não alterar licença do aplicativo para contornar requisitos de terceiros.
- [ ] Rodar Bandit, pip-audit com lock Windows e varredura de segredos conforme workflow/ferramentas disponíveis. Registrar versões, data e escopo; pip-audit não cobre sozinho DLLs Qt/sistema.
- [ ] Executar suíte final após correções; `git diff --check`; conferir traduções, versão e documentos finais.
- [ ] Reconstruir se o código/documentos incluídos mudaram. Calcular hashes após todos os ajustes; não reutilizar inventário anterior ao build final.
- [ ] Informar ausência de assinatura digital se não houver certificado/chave. SHA-256 não é assinatura. Não adquirir certificado ou publicar automaticamente.
- [ ] Atualizar checklist e produzir `history/VALIDACAO_WINDOWS_FINAL_FORNAX.md`, sem sobrescrever a evidência histórica de 20/09.

```powershell
Get-FileHash build\installer-windows\*.exe -Algorithm SHA256
```

**Aceite W7:** artefato final identificado, testado e documentado; pendências legais/técnicas explicitadas. Se uma pendência de liberação existir, não declarar “pronto para publicar”.

## 5. Pendências Linux que continuam existindo

- Recompilar com os ajustes recentes; o standalone da etapa 5 não contém necessariamente a interface atual.
- Construir/instalar AppImage e verificar integração efetiva de MIME/ícone/duplo clique no host. O `.desktop` incluído sozinho não garante registro automático. Ferramenta: `tools/install_linux_integration.py`; ver checklist.
- Flatpak: preparar wheelhouse/lock para ABI e arquitetura do SDK GNOME 50, construir e testar portais, seleção de pastas/arquivos externos, fotos variáveis, saída e IPC na sandbox. Não reaproveitar indiscriminadamente wheels do host.
- Validar fontes/avisos e hashes de cada pacote final. Não marcar matriz Linux como concluída a partir dos testes Windows.
- macOS também não foi aprovado; só oferecer instalador macOS após validação própria. Não precisa bloquear um release explicitamente limitado a Windows/Linux por uma plataforma que não será distribuída.

## 6. Registro de execução e próxima retomada

**Ajuste posterior ao build W5/W6:** seletores de importar/exportar agora usam linhas de 28 px (24 px de conteúdo + 2 px acima/abaixo); botões internos de importação com 24 px. Três testes de transferência aprovados, incluindo geometria Qt offscreen. O executável e o instalador anteriores não contêm esse ajuste: reconstruir ambos antes da próxima validação/distribuição.

**Estado em 22/09/2026:** W1 e W2 concluídos no Windows; W2 com pulos de capacidade documentados. W3 com inspeção nativa impedida; W4 com validação automatizada aprovada e aceite completo pendente. W5 com novo executável e auditoria estática aprovados, validação funcional pendente. W6 com instalador de teste gerado, instalação real pendente. W7 não executada para esta revisão. Os testes/builds de 20/09 não validam este commit.

| Checkpoint | Estado | Evidências / correções / pendências |
|---|---|---|
| W1 Ambiente | Concluído | Venv novo `.venv-windows`, requisitos atuais instalados, pip check aprovado, sem PySide6/Addons; inventário abaixo e `history/WINDOWS_W1_REQUIREMENTS_RESOLVIDOS.txt`. |
| W2 Suíte | Concluído com limitações registradas | 482 aprovados, 12 subtestes, 12 pulados, sem falhas/avisos; IPC real aprovado. Ver `history/VALIDACAO_WINDOWS_W2_FORNAX.md`. |
| W3 Interface e fluxos | Iniciada; inspeção nativa impedida | Iniciador isolado verificado; controle Windows indisponível. Ver `history/VALIDACAO_WINDOWS_W3_FORNAX.md`. |
| W4 Proteção e persistência | Automatizada aprovada; aceite completo pendente | 128 aprovados, 2 pulados; offline limitado ao bloqueio Python. Ver `history/VALIDACAO_WINDOWS_W4_FORNAX.md`. |
| W5 Standalone | Build e auditoria estática realizados; aceite funcional pendente | 442 arquivos verificados; falta máquina sem Python e fluxos nativos. Ver `history/VALIDACAO_WINDOWS_W5_FORNAX.md`. |
| W6 Instalador instalado | Instalador de teste gerado; instalação real pendente | ISCC saiu com 0; 9 testes de código/IPC aprovados. Ver `history/VALIDACAO_WINDOWS_W6_FORNAX.md`. |
| W7 Fechamento | Pendente | |

### W1 — execução em 22/09/2026 por Codex

- Árvore inicialmente limpa, branch `novo_main`, commit `13ccde34b6758a1a430dc597176f7c96641f0e59`. Nenhum `AGENTS.md` encontrado no projeto. Confirmados no Git os novos requisitos, `scripts/release_tools.py`, `tests/test_transfer_dialogs.py`, `tests/test_temp_storage.py` e este plano; referências listadas acima consultadas.
- Windows 11 build 26200, AMD64/64 bits, C: NTFS. Tela reportada pelo Qt nativo: LG ULTRAWIDE, 2560×1080, DPI lógico 96, fator 1,0 (100%). Isso é inventário de tela, não inspeção visual W3.
- Novo `.venv-windows`, criado com `C:\Users\leona\AppData\Local\Programs\Python\Python313\python.exe`, Python 3.13.11 x64. `include-system-site-packages = false`; ambiente anterior preservado.
- Runtime: Qt/PySide6_Essentials/shiboken6 6.11.0, pypdf 6.16.1, cryptography 50.0.1 e defusedxml 0.7.1. Ausência de distribuições `PySide6` e `PySide6_Addons` confirmada por `importlib.metadata`.
- Ferramentas: Nuitka 4.0.7, zstandard 0.25.0, pytest 9.0.3, pytest-qt 4.5.0, pip-tools 7.6.1, pip-audit 2.10.1 e Bandit 1.9.4. Pip 25.3 mantido.
- Clang/clang-cl 22.1.3 em `C:\Program Files\LLVM\bin`, alvo x86_64-pc-windows-msvc. Visual Studio Community 2026 18.1.11312.151 localizado por vswhere, com toolsets MSVC 14.44.35207 e 14.50.35717. Inno Setup localizado no caminho previsto; notas locais indicam série 6.7. A seleção e execução efetiva do compilador são verificadas em W5.
- `pip check`: `No broken requirements found.` A instalação precisou de acesso à rede fora do sandbox após WinError 10013 na primeira tentativa; concluída com código 0. Nenhum requisito direto foi alterado.
- Inventário de todas as versões, incluindo transitivas: `history/WINDOWS_W1_REQUIREMENTS_RESOLVIDOS.txt` (versionado) e `build/security/windows-w1-freeze.txt` (cópia local). É um snapshot Windows de `pip freeze --all`; locks com hashes, wheels arquivados e reinstalação de build continuam em W5.
- Arquivos alterados: `.gitignore` (ignora somente o novo `.venv-windows/`), este plano e o snapshot versionado. Nenhuma alteração funcional, teste da suíte, compilação ou instalação do aplicativo foi feita em W1.
- Artefato final desta revisão: ainda não gerado. A biblioteca real e as preferências do aplicativo não foram usadas para esta preparação.
- Último checkpoint concluído: **W1**. Próximo: **W2**, começando pela inspeção de isolamento de QSettings, pasta de dados, temporários e subprocessos dos testes; só depois coletar e executar a suíte atual no novo venv. No Windows, mudar apenas APPDATA não isola o registro.

Comandos executados (raiz do projeto):

```powershell
& 'C:\Users\leona\AppData\Local\Programs\Python\Python313\python.exe' -m venv .venv-windows
.\.venv-windows\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-windows\Scripts\python.exe -m pip check
.\.venv-windows\Scripts\python.exe -m pip freeze --all
clang-cl --version
& 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe' -latest -products '*' -format json
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' /?
git diff --check
```

Verificação complementar: imports de QtCore/QtGui e consulta `QGuiApplication.screens()` com `QT_QPA_PLATFORM=windows`, sem iniciar `main.py` nem criar janela do FORNAX. W2 terá contagens novas; não reutilizar as contagens históricas deste documento.

### W2 — execução em 22/09/2026 por Codex

- Mesma branch/commit-base de W1, preservando suas alterações locais. Ambiente `.venv-windows`, Qt offscreen, Fusion/Inter e `FORNAX_RUN_NATIVE_IPC=1`.
- Criado isolamento anterior à coleta em `conftest.py` e `tests/isolated_environment.py`: dados/temporários descartáveis e QSettings em INI explícito; subprocesso de falha isolado. Liberação das janelas entre testes evita acúmulo e expõe callbacks tardios.
- Corrigidos: preservação da família de fonte ausente no editor; desconexão do callback de tema do botão da tabela; alinhamento do destino na grade de saída; sobrecarga Qt depreciada ao duplicar células; 23 traduções em cada catálogo EN/ES, com `.qm` recompilados.
- Regressões: fontes ausentes, janela destruída, alinhamento combinado de texto, arquivo público/protegido somente leitura e aberto por processo independente, isolamento de preferências e armazenamento. Testes de links agora distinguem capacidade ausente de falha genérica.
- Resultado final: **494 casos coletados; 482 aprovados + 12 subtestes aprovados; 12 pulados; zero falhas/erros/avisos em 104,80 s**. Pulos: nove symlinks sem privilégio Windows 1314, dois Amiri indisponível e um exclusivo Linux. Os três testes de IPC passaram; não foi pulado.
- Comando: `.\.venv-windows\Scripts\python.exe -m pytest --import-mode=importlib -q tests features/editor --junitxml=build/security/windows-tests.xml -ra --durations=10 -o faulthandler_timeout=45`, com as variáveis acima. `git diff --check` e `pip check` passaram.
- Evidências e lista individual de pulos: `history/VALIDACAO_WINDOWS_W2_FORNAX.md`; JUnit final `build/security/windows-tests.xml`; coleta `build/security/windows-w2-collection.txt`; baterias intermediárias também em `build/security/`.
- Arquivos funcionais alterados: `features/editor/editor_window.py`, `features/workspace/frontend.py`, `features/spreadsheet/table_panel.py` e catálogos TS/QM EN/ES. Testes/apoio: conftest, isolamento, helper de symlinks, ciclo de vida, páginas, tabela, workspace, persistência Windows, imagens dinâmicas, nomenclatura, empacotamento e temporários. Mudanças detalhadas no relatório W2 e no diff.
- **Último checkpoint concluído: W2. Próxima ação: W3**, preparar biblioteca sintética e isolamento também das preferências para a aplicação nativa, então validar visualmente fluxos/layout conforme a seção W3. Não iniciar `main.py` com a biblioteca real como massa de teste. QSettings INI do pytest não se aplica automaticamente ao programa iniciado fora do pytest.
- Nenhum instalador novo foi gerado em W2. W3–W7 seguem pendentes, inclusive reconstrução do binário com as correções desta etapa.

### Retomada W3 — 22/09/2026

- W3 iniciada, mas não aprovada: o controle nativo retornou `Computer Use native pipe is unavailable` ao listar janelas.
- Preparado `tools/windows_visual_validation.py`, com biblioteca/INI/temporários e IPC isolados em `build/security/windows-w3-profile`; verificação de isolamento executada com sucesso.
- **Último checkpoint concluído continua W2. Próxima ação: restabelecer o controle nativo e continuar W3** pelo iniciador isolado, criar massa sintética e executar o checklist visual/funcional. Nenhum item visual foi marcado como aprovado.
- Evidências e comando de execução: `history/VALIDACAO_WINDOWS_W3_FORNAX.md`. W4–W7 não iniciadas.

### Retomada W4 — 22/09/2026

- Usuário autorizou avançar apesar do impedimento de W3; W3 permanece pendente.
- Executado `tools/validate_windows_w4.py`: **128 aprovados, 2 pulados, zero falhas, 35,01 s**, armazenamento isolado e Qt offscreen. Testes de geração protegida ampliados para PDF individual/agrupado sem senha na saída.
- Zero tentativas de rede nos eventos Python monitorados. Ainda falta ensaio realmente sem conexão e inspeção nativa; não houve bloqueio/monitoramento de tráfego de bibliotecas nativas ou filhos.
- NTFS confirmado; FAT/exFAT/rede não testados. Dois pulos por privilégio de links simbólicos. Relatório: `history/VALIDACAO_WINDOWS_W4_FORNAX.md`.
- **Próximo checkpoint sequencial: W5**, sem considerar W3/W4 integralmente aprovadas. Último checkpoint integralmente concluído continua W2. Nenhum novo binário ou instalador foi gerado em W4.

### Retomada W5 — 22/09/2026

- Locks com hashes runtime/build/dev em `history/windows-w5-locks/`; ambiente limpo de build instalado offline pelos hashes e `pip check` aprovado.
- Novo `build/main.dist/FORNAX_Forge.exe` AMD64 gerado pelo Nuitka/MSVC; auditoria estática de 442 arquivos aprovada. Fontes/recursos comparados com staging sem diferenças, fora avisos regenerados dos pacotes.
- SHA-256 do executável: `12a76f8384cda2d16a9932489c4260052df2350cd4acc0a6b92567ce98c86ed1`.
- **W5 não integralmente aprovada**: falta execução em máquina sem Python, inspeção visual e cenários críticos do standalone. W3 e offline real W4 continuam pendentes.
- Próximo checkpoint sequencial: **W6**, sem dispensar pendências de W3–W5. Nenhum novo instalador gerado. Relatório e ressalva sobre código de saída PowerShell: `history/VALIDACAO_WINDOWS_W5_FORNAX.md`.

### Retomada W6 — 22/09/2026

- Gerado `build/installer-windows/Instalador-FORNAX-Forge-1.0.0.exe` pelo Inno Setup, saída 0, 30.864.019 bytes. Versão de teste e AppId preservados.
- SHA-256: `e2fda680c85b795b107ea30441e5a058f6e0aad31c2dbe1373aa7a2880e8c776`. Sem assinatura digital.
- Auditoria dos 442 arquivos W5 repetida e aprovada; 9 testes de abertura externa/IPC pelo código aprovados. Não equivalem a instalação/Explorer.
- **W6 não aprovada integralmente**: instalador não executado; é necessário disponibilizar VM descartável para testar instalação administrativa, associações, atualização e desinstalação sem afetar o ambiente real.
- Próximo checkpoint documental sequencial: W7, mantendo W3–W6 pendentes de aceite completo. Não declarar pronto para publicar. Relatório: `history/VALIDACAO_WINDOWS_W6_FORNAX.md`.

### W6 — atualização real autorizada no host

- Usuário autorizou usar este Windows. Atualização da instalação de 19/09 aplicada com saída 0; 442 arquivos conferidos sem divergência, atalhos e associação verificados.
- Detectado qpdf antigo remanescente. ISS corrigido para remover só esse plugin, com backup recuperável; 10 testes aprovados. Novo instalador SHA-256 `b4de1a1e3e677a2969477670d282082d425b25a64d88c29579df42cdf07d8b89`.
- **Próxima ação imediata: confirmar UAC e finalizar segunda instalação**, ainda pendente (sessão 23174, processo consent presente). Verificar saída e ausência de qpdf antes de considerar correção instalada. Não houve desinstalação nem limpeza de dados. W6 ainda não integralmente aprovada.
- Atualização posterior: sessão 23174 terminou com código 2, sem aplicar a correção. Nova tentativa na sessão 82872, ainda aguardando UAC (processo `consent` observado). Log esperado: `build/security/windows-w6-install-upgrade-fix-retry.log`. Os 442 arquivos instalados permanecem corretos; qpdf ainda presente na última conferência.

Texto que o usuário pode enviar à outra instância:

> Leia `RETOMADA_WINDOWS_VALIDACAO_E_INSTALADORES.md`, confira o estado atual do repositório e execute os checkpoints a partir do primeiro pendente. Corrija os problemas encontrados, preserve minha biblioteca real e registre os resultados e o próximo passo no documento. Não publique nem migre o repositório ainda.
