# Etapa 1 — Referência funcional e mapa de dados do `.fornax`

Data da execução: 20/09/2026

Estado: concluída

Escopo: checkpoints 1.1, 1.2 e 1.3 do plano de formato e proteção.

## Resultado

Foi estabelecida uma referência reproduzível antes da mudança de armazenamento. Nenhuma assinatura real foi usada e o comportamento de produção não foi alterado. A etapa acrescentou fixture sintética, contratos automatizados e uma captura local de renderização/desempenho.

Arquivos de evidência:

- `tests/fixtures/fornax_stage1/template_v4.json` e seus três SVGs sintéticos;
- `tests/test_fornax_stage1_contracts.py`;
- `tools/capture_fornax_stage1_baseline.py`;
- `.validation/fornax_stage1/report.json` e imagens geradas localmente; `.validation` permanece ignorado pelo Git.

## 1.1 — Inventário de leitura e escrita

### Raízes persistentes

| Dado | Local atual | Quem cria/lê | Impacto do `.fornax` |
|---|---|---|---|
| Dados da aplicação | `core.paths.get_app_data_dir()` | migração ComSoc → FORNAX | Continua como raiz; a migração histórica é independente da conversão de modelos |
| Biblioteca | `<dados>/models/<slug>/` | workspace, editor, renderer, caches | Passará a listar `.fornax` e pastas legadas simultaneamente |
| Documento atual | `template_v4.json` | `core.model_document` | Será conteúdo lógico do contêiner, acessado pela camada de armazenamento |
| Documento legado | `template_v3.json` | normalização, recuperação e importação | Continua somente como entrada de compatibilidade |
| Recuperação | `template_v4.json.bak` e `template_v3.json` | `load_recovery_documents()` e limpeza de assets | Conteúdo sensível de recuperação precisará permanecer protegido |
| Assets do modelo | `<modelo>/assets/**` | editor, renderer e informações do modelo | Serão resolvidos dentro do contêiner, sem exigir caminho físico aberto |
| Cache gráfico | `<modelo>/.render_cache/` | `core.render_cache`, preview e editor | Miniaturas parciais não podem conter assinaturas; modo integral não pode persistir miniatura do conteúdo |
| Configurações | `QSettings` | idioma, tema, geometria, último modelo, pasta dinâmica e saída | Nunca deve receber senha, chave ou material descriptografado |
| Logs | `<dados>/logs/crash_log.txt` e painel de log | entrada do workspace e fluxos de UI | Não registrar senha, chave, conteúdo descriptografado ou caminho temporário sensível desnecessário |
| Resultados | pasta escolhida / `FORNAX - Forja nº X` | gerador e workers | São saídas autorizadas, podendo conter assinatura visível |
| Imagens variáveis | pasta externa lembrada por modelo em `QSettings` | workspace e renderer | Permanecem vínculo externo; não devem ser incorporadas ao `.fornax` por acidente |

### Fluxos e fronteiras encontradas

#### Inicialização e biblioteca

1. `features/workspace/main.py` cria log de falha e abre o workspace.
2. `features/workspace/main_window.py::_ensure_starter_pack()` pode criar uma pasta de exemplo e salvar v4.
3. `_reload_models_from_disk()` enumera exclusivamente diretórios e carrega cada documento para obter nome/identidade.
4. A seleção persistida usa `workspace/last_model_id` no `QSettings`.
5. Duplicação usa `copytree`; renomeação move/renomeia o diretório e regrava o JSON; exclusão usa `rmtree`.
6. “Abrir pasta de modelos” expõe a raiz atual pelo explorador. No formato novo mostrará os arquivos `.fornax` e eventuais legados ainda não convertidos.

Pontos de adaptação: listagem híbrida, identidade independente do nome/caminho, operações atômicas sobre arquivo único e seleção persistida de temporários/legados.

#### Seleção, preview e tabela

1. `_on_model_changed()` resolve `template_v4.json`/v3, normaliza o documento e cria a vista plana da frente.
2. Caminhos relativos de fundo e assinatura são atualmente convertidos em caminhos físicos; `__model_dir` é propagado ao renderer.
3. O cache é consultado por diretório, hash do JSON e `page_id`; se ausente, `PreviewRenderWorker` renderiza e publica PNG e manifesto em `.render_cache`.
4. A tabela recebe a união de placeholders e assinaturas de todas as páginas. Uma assinatura oculta continua presente como campo funcional.
5. Preview de item usa renderer em memória. Preview de folha usa `mkdtemp("fornax_sheet_preview_")`; a janela guarda esses diretórios e os remove ao invalidar/fechar.

Pontos de adaptação: autorização antes de construir tabela/preview, cache por identidade e revisão do pacote, descarte de jobs atrasados e proibição de miniatura sensível persistente.

#### Editor e salvamento

1. `EditorWindow.load_from_json()` aceita arquivo ou pasta, carrega documento e mantém `_current_model_dir`.
2. A cena trabalha com uma página plana; `DocumentSessionMixin` combina a página novamente no documento v4.
3. `_import_asset()` copia arquivos para `assets/` usando `copy2`. O salvamento reescreve referências, garante proxy de fundo, grava v4 atomicamente e publica thumbnail.
4. `save_model_document()` grava temporário no mesmo diretório, faz `fsync`, conserva o v4 anterior como `.bak` e substitui o destino.
5. Ao fechar, `_cleanup_unused_assets_on_close()` cruza documento atual e recuperações, apaga arquivos órfãos e remove subpastas vazias.
6. Histórico de desfazer/refazer é memória de sessão. A recuperação persistente identificada é o backup v4 e o v3 anterior; não foi encontrado autosave independente do modelo.

Pontos de adaptação: resolver assets sem arquivos abertos, empacotar documento/assets de modo transacional, proteger backup/recuperação e impedir que a limpeza remova dados ainda referenciados.

#### Renderer e geração

1. `renderers_for_document()` cria um renderer por página adaptada.
2. `NativeRenderer` resolve assets por `__model_dir`; ainda possui fallbacks para `<models>/<slug>`.
3. O renderer mantém caches de imagens e base estática em memória. Fundo pode usar proxy persistente em `.render_cache`.
4. `RenderManager` usa `<saída>/.temp_hybrid` na geração de PDF agrupado. Workers gravam PNG/PDF temporários e movem/publicam resultados; a montagem remove o diretório ao final.
5. PDFs agrupados e de imposição recebem links posteriormente por `features/generator/pdf_links.py`, que grava arquivo temporário e substitui o PDF.
6. Frente e verso usam renderers separados; a imposição define a correspondência física, sem alterar o documento fonte.

Pontos de adaptação: entregar bytes/imagens autorizados ao renderer mantendo seu contrato, garantir limpeza dos recursos em memória e separar temporários internos de resultados solicitados.

#### Importação, exportação e migração

1. Importação atual abre ZIP, examina JSONs e depois executa `extractall()` em diretório temporário.
2. O conteúdo extraído é normalizado, salvo como v4 e instalado por `install_model_directory()`, que usa staging e backup de diretório.
3. Exportação atual percorre toda a pasta com `os.walk`, excluindo apenas `.render_cache`, e cria ZIP.
4. `core.paths` também possui migração única dos dados do aplicativo antigo, com cópia verificada por SHA-256 e marcador retomável.

Risco registrado: `extractall()` não oferece os limites e a validação granular exigidos para arquivos externos na etapa 2/3. A substituição pertence ao checkpoint 3.1; esta etapa apenas registra o comportamento.

#### Distribuição

- Entradas: `main.py` e `features/workspace/main.py`.
- Empacotamento: `script_nuitka.py`, `script_appimage.sh` e `com.leobelisario.FornaxForge.yaml`; `FORNAX_Forge.flatpak` é o pacote binário resultante.
- A nova dependência `cryptography` ainda não consta em `requirements.txt` nem nos empacotadores; sua versão e suporte a Argon2id/AES-GCM serão fechados no checkpoint 2.2.
- Associação de `.fornax` e eventos de abertura externa ainda não existem.

### Lacunas deliberadamente não resolvidas nesta etapa

- Não existe abstração de armazenamento/resolvedor capaz de servir assets internos do `.fornax`.
- Várias rotas inferem identidade pelo slug/diretório e precisam ser desacopladas.
- Importação não possui limites contra expansão excessiva, caminhos perigosos ou custo agregado.
- Cache atual pode conter a aparência completa do modelo e não conhece autorização ou modo de proteção.
- O renderer ainda exige caminhos físicos em alguns fallbacks.
- Não há estado central de bloqueado/desbloqueado, prazo de cinco minutos ou invalidação por revisão.
- Não há associação de extensão nem fluxo de abertura temporária.

Essas lacunas são entradas para as etapas 2 e 3, não falhas introduzidas pela etapa 1.

## 1.2 — Modelos sintéticos e contratos

A fixture v4 contém:

- frente e verso com dimensão comum;
- texto rico com pesos, itálico, cores e placeholders;
- link funcional;
- assinatura visível e assinatura oculta, ambas com `signature_id` distinto;
- imagem dentro de máscara elíptica;
- grupo básico;
- forma de imagem variável;
- guia em cada página;
- asset propositalmente ausente e invisível;
- ordem completa de camadas.

Os cinco contratos novos verificam:

1. preservação de páginas, relações, grupos e união de campos;
2. inventário de assets incluindo assinatura oculta e referência ausente;
3. round-trip atual de gravação e leitura;
4. renderização determinística das duas páginas sem falhar pelo asset ausente;
5. isolamento de mutações entre vistas planas e documento.

Validação focada executada:

```text
72 passed, 1 warning in 7.80s
```

O aviso é preexistente: `QTableWidgetItem.setTextAlignment(int)` está marcado como obsoleto pelo PySide6. Não interfere nos contratos de armazenamento.

Regressão ampliada ao encerrar a etapa:

```text
pytest tests: 131 passed, 10 subtests passed, 1 warning
unittest features.editor.*: 63 tests, OK
```

O `pytest` deve ser direcionado a `tests/`: a raiz contém `build-dir/`, com uma imagem Flatpak e cópias do sistema que não pertencem à suíte. A coleta irrestrita percorre esses artefatos e falha por testes duplicados/permissões, antes de testar o código fonte.

## 1.3 — Referência visual, desempenho e volume

Comando reproduzível:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python tools/capture_fornax_stage1_baseline.py
```

Ambiente da captura registrada: Linux 7.0.0-31 x86_64, Python 3.13.11, PySide6 6.11.0, Qt offscreen.

### Referência visual e funcional

| Saída | Resultado |
|---|---|
| Frente PNG | 400×240 px; SHA-256 `0cb6bb8a7e6dddacfc78946a28ddffb507ab335e16ce2724d3458c5f1d313197` |
| Verso PNG | 400×240 px; SHA-256 `c94de46797aa1a9de62a4f50a72f559c4d8ccab9e8ad43e8d0194db7c1aa9160` |
| Lote PDF por item | 100 arquivos de duas páginas; 200 páginas e 2.465.270 bytes no total |

O hash de PNG é referência exata neste ambiente. Mudança de Qt, fonte ou plataforma pode produzir rasterização diferente; nesses casos comparar dimensão, regiões/pixels funcionais e inspeção visual antes de aceitar o novo hash. PDF pode carregar metadados variáveis e não deve ser validado apenas pelo hash.

### Medições da captura

| Operação | Mediana | P95 | Amostras |
|---|---:|---:|---:|
| Leitura fria do documento | 0,454 ms | 0,454 ms | 1 |
| Leitura aquecida | 0,339 ms | 0,403 ms | 50 |
| Adaptar frente e verso | 0,482 ms | 0,490 ms | 100 |
| Abrir fixture no editor | 34,130 ms | 34,130 ms | 1 |
| Renderizar duas páginas, frio | 5,206 ms | 5,206 ms | 1 |
| Renderizar duas páginas, aquecido | 2,665 ms | 2,949 ms | 30 |
| Gerar 100 itens / 200 páginas em PDF | 862,192 ms | 862,192 ms | 1 |
| Examinar ZIP legado com 100 modelos | 8,079 ms | 9,050 ms | 10 |
| Instalar 20 modelos legados | 170,662 ms | 170,662 ms | 1 |

Pico observado do processo: 128.584 KiB. `ru_maxrss` registra pico e não mede com precisão toda memória nativa do Qt.

### Interpretação e limites para a etapa 2

- O JSON sintético tem 7.283 bytes, duas páginas e três assets reais pequenos. Ele serve para regressão funcional, não para definir sozinho limites máximos.
- A geração mede o pipeline real de renderer/worker em modo offscreen; não mede latência de diálogo ou sensação visual.
- O teste ZIP mede descoberta e leitura de 100 documentos; a publicação de 20 modelos mede staging/cópia/gravação atual. Não valida segurança do ZIP.
- Medições frias e operações de lote único têm uma amostra porque produzem artefatos/estado; devem ser repetidas no mesmo ambiente ao final da etapa 4.
- Os modelos reais existentes no diretório `models/` foram apenas inventariados por tamanho durante o levantamento e não foram copiados para fixtures, pois podem conter conteúdo do usuário.
- Os limites definitivos de tamanho, pixels, quantidade de entradas e lote deverão considerar exemplos institucionais maiores no checkpoint 2.2, aplicando margens documentadas.

## Encerramento e retomada

Checkpoints 1.1, 1.2 e 1.3 concluídos. O comportamento de produção permanece igual. O próximo ponto é **2.1 — Esquema dos três modos e contratos de acesso**.

Antes de iniciar 2.1, usar este documento como mapa e executar os contratos novos. Ao final da implementação, repetir a captura no mesmo ambiente e comparar referências, custo recorrente e resultados gráficos.
