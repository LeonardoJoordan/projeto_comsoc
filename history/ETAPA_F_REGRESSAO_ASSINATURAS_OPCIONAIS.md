# Checkpoint F — regressão das assinaturas com proteção opcional

## Resultado e correções

Revisão automatizada concluída em 21/09/2026. A liberação para distribuição ainda
depende da matriz manual Linux/Windows em `docs/CHECKLIST_DISTRIBUICAO_FORNAX.md`.
Os testes anteriores do Windows não validam automaticamente esta atualização.

Foram corrigidos dois caminhos na ação **Proteger modelo…**:

- Arquivos abertos temporariamente não podem ser modificados por essa ação.
  A interface orienta salvar uma cópia na biblioteca antes de protegê-la.
- A existência de recuperação do editor ou de seu backup impede essa ação até
  salvar ou descartar a recuperação no editor. Não apagamos trabalho pendente,
  nem deixamos deliberadamente uma recuperação pública após proteger o principal.

Os novos testes confirmam preservação dos arquivos nesses três casos, proteção
do principal e do backup na transição público v2 → assinaturas/integral, manutenção
da identidade do modelo e retirada do aceite público na versão protegida. O modo
assinaturas ainda permite abrir a cópia pública sem assinaturas, como previsto.

Também verificamos que abrir, renderizar e salvar o público com assinaturas não
executa derivação de senha. A renderização usa os assets empacotados e mantém os
pixels de referência das duas páginas. Não houve alteração nos algoritmos de
criptografia nesta etapa. A cobertura existente de falhas de persistência,
migração, sessão, importação/exportação e ciclo de vida fez parte da suíte geral.

## Validação executada

Ambiente: Linux, Python 3.13.11, PySide6 6.11.0, Qt offscreen; modelos sintéticos,
sem mutações na biblioteca do usuário.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q --import-mode=importlib features/editor
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/test_fornax_stage4_regression.py tests/test_i18n.py
.venv/bin/pyside6-lrelease assets/translations/fornax_en_US.ts assets/translations/fornax_es_ES.ts
git diff --check
```

- Suíte geral: **352 aprovados, 1 ignorado, 12 subtestes aprovados**, 196,50 s.
  Executada antes da adição dos seis novos casos desta etapa.
- Editor: **63 aprovados**, 27,32 s.
- Regressão final e traduções, incluindo os seis novos casos: **13 aprovados**,
  3,02 s. Esta seleção sobrepõe testes da suíte geral; não somar as contagens.
- Catálogos inglês e espanhol: **855 traduções cada, nenhuma inacabada**.
- Teste ignorado: IPC nativo, que exige `FORNAX_RUN_NATIVE_IPC=1` e sockets locais.
- Um aviso preexistente de depreciação de `setTextAlignment(int)` na tabela.

A coleta inicial do editor sem `--import-mode=importlib` falhou por imports
relativos; o comando correto acima executou os testes. Durante a escrita dos
novos testes, corrigimos a resolução de assets da referência sintética e a
expectativa de abertura pública do modo assinaturas; os resultados finais acima
correspondem aos testes corrigidos, sem falhas conhecidas nas seleções executadas.

## Referência visual e desempenho

Ferramenta `tools/capture_fornax_stage4.py` ampliada com `--public-signatures`.
Relatório bruto: `ETAPA_F_MEDICOES_ASSINATURAS_OPCIONAIS.json`. A captura final
foi executada após as suítes, sem execução concorrente de testes.
Referência anterior: seção `fornax_current` de `ETAPA_4_4_MEDICOES_FORNAX.json`.

Medianas locais em milissegundos, anterior → atual:

| Cenário | Abrir/desbloquear | Salvar autorizado | Render aquecido | Gerar 100 itens / 200 páginas |
|---|---:|---:|---:|---:|
| Público sem assinatura | 1,424 → 1,439 | 17,946 → 16,006 | 2,880 → 2,799 | 883,127 → 858,303 |
| Assinaturas protegidas | 116,199 → 116,102 | 19,860 → 20,506 | 3,144 → 3,147 | 896,796 → 869,443 |
| Integral protegido | 116,250 → 115,533 | 16,435 → 16,982 | 3,127 → 3,112 | 875,269 → 860,592 |
| Público com assinaturas (novo) | 1,772 | 19,208 | 3,138 | 876,252 |

Nos quatro cenários, a comparação de pixels passou nas duas páginas, foram gerados
100 PDFs/200 páginas e exercitado o preview de 500 linhas. Os hashes PNG dos modos
anteriores permanecem iguais à referência arquivada. Público com assinaturas tem
os mesmos hashes dos modos que preservam assinaturas.

As pequenas oscilações não demonstram ganho ou regressão causal. Desbloqueio
protegido inclui o custo da derivação de senha; público não tem esse custo.
São medições sintéticas locais, sem equivalência garantida em outro computador.

## Limites e próxima ação

- Validar manualmente recomendação/cancelamento, proteção posterior, recuperação,
  migração e lotes mistos no Linux e Windows, conforme checklist de distribuição.
- Conferir visualmente os novos textos nos três idiomas e repetir IPC nativo.
- Arquivo público expõe os assets por decisão explícita; não oferece sigilo.
- A revisão não certifica ausência absoluta de vulnerabilidades. Backups externos,
  arquivos já compartilhados e cópias do sistema operacional não são revogados ao
  proteger um modelo. Os testes de ciclo de vida cobrem os caminhos do aplicativo,
  não uma auditoria forense de memória, swap ou armazenamento físico.

Próximo passo: validação manual da versão candidata, registrando plataforma e
resultado. Não há novo checkpoint de implementação pendente neste plano.
