# FORNAX Forge

**Geração de material personalizado em lote**
*Personalized Batch Material Generation*

O FORNAX Forge é um aplicativo desktop para criar modelos gráficos, alimentar seus campos com dados tabulares e gerar materiais personalizados em escala. O fluxo reúne editor visual, prévia fiel, tabela integrada e exportação em PNG ou PDF sem exigir que cada peça seja editada manualmente.

## O que o aplicativo oferece

- editor visual com textos ricos, imagens, assinaturas, formas, camadas, guias e histórico;
- placeholders como `{Nome}`, `{Cargo}` e outros campos definidos no próprio modelo;
- tabela para colar dados vindos de Excel, LibreOffice Calc ou Google Sheets;
- prévia do resultado antes da geração do lote;
- PNG por item, PDF por item ou PDF agrupado;
- modelos com frente e verso, com PNGs identificados por página e PDFs multipágina;
- imposição em folhas, marcas de corte, sangria e links em PDF;
- biblioteca local de modelos com importação e exportação em ZIP.

O motor de renderização é compartilhado pelo editor, pela prévia e pela geração final. Isso mantém posição, tipografia, transparência e dimensões físicas consistentes ao longo do fluxo.

## Estrutura atual

```text
main.py                  entrada oficial
core/                    modelo de documento, texto, histórico e caminhos
features/workspace/      janela principal e biblioteca de modelos
features/editor/         editor visual
features/spreadsheet/    tabela de dados
features/preview/        prévia do registro selecionado
features/generator/      renderização, PDF e imposição
shared/                  componentes compartilhados
tests/                   testes do motor e da migração
docs/                    licenças e documentação histórica
```

As interfaces antigas foram retiradas da branch `novo_main`. A última versão funcional do COMSOC permanece preservada na branch `main` do repositório.

## Executar a partir do código

Requer Python 3.11 ou mais recente.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

No Windows, ative o ambiente com `.venv\Scripts\activate`. O editor também pode ser aberto isoladamente para diagnóstico:

```bash
python features/editor/main.py
```

## Dados e compatibilidade com o COMSOC

Em **Exibir > Tema da interface**, escolha entre os cinco temas padrão: **Carbono** (preto e cinza profundo), **Marinho** (azul escuro), **Grafite** (cinza médio), **Rosê** (rosa envelhecido e sépia) e **Pérola** (claro). Os perfis personalizados salvos também aparecem nessa lista. O botão **Criar tema**, no rodapé, abre uma segunda janela com os controles avançados de cores e o nome do novo perfil. A interface mostra a prévia imediatamente; Cancelar restaura o tema anterior. Os arquivos oficiais ficam em `assets/themes/` e as personalizações em `themes/` dentro da pasta de dados do aplicativo. As cores dos documentos e arquivos gerados não são alteradas.

O FORNAX Forge usa o identificador técnico `com.leobelisario.FornaxForge`. No primeiro acesso, dados encontrados no diretório da instalação COMSOC são copiados para a nova área. Modelos já existentes no destino são preservados integralmente, sem mesclar assets. A cópia é verificada antes de ser publicada, sua conclusão fica registrada e a origem não é apagada. Uma interrupção pode ser retomada; modelos excluídos após a migração não são recriados. Conflitos podem ser resolvidos posteriormente pela importação de modelos.

As preferências visuais e de exportação também são copiadas do namespace antigo somente quando ainda não possuem valor no FORNAX Forge. Modelos existentes em `template_v3.json` continuam compatíveis. Novos salvamentos usam o documento versionado `template_v4.json`; quando um v4 anterior existe, ele é mantido como cópia de recuperação.

Em uma instalação Flatpak, cada identificador possui uma sandbox própria. Nesse caso, use **Modelo > Exportar modelos** no COMSOC e **Modelo > Importar modelos** no FORNAX Forge quando a sandbox nova não conseguir acessar os dados antigos.

## Testes

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest \
  features.editor.test_window_lifecycle \
  features.editor.test_draw_shapes \
  features.editor.test_layers \
  features.editor.test_canvas_edit \
  tests.test_pdf_links \
  tests.test_rendering_pipeline \
  tests.test_data_migration
```

Os testes offscreen verificam o comportamento funcional, mas não substituem a validação nativa dos controles de janela, impressão e pacotes em Windows, Linux e macOS.

## Distribuição

- `script_nuitka.py`: executável nativo com Nuitka;
- `script_appimage.sh`: AppImage Linux criado a partir da saída Nuitka, incluindo o Qt do próprio standalone;
- `com.leobelisario.FornaxForge.yaml`: manifesto Flatpak.

O Nuitka usa até quatro tarefas de compilação por padrão, respeitando o número de CPUs. É possível ajustar com `FORNAX_BUILD_JOBS`. O AppImage exige a compilação standalone concluída e `appimagetool` na raiz.

Os ícones oficiais ficam em `assets/icons/`: PNGs dimensionados para a interface e Linux, além do ICO multirresolução para Windows. O PNG de 1024 px é usado como fonte do pacote macOS. Antes da publicação, o inventário e os textos integrais das licenças do pacote devem ser concluídos conforme [docs/THIRD_PARTY_LICENSES.md](docs/THIRD_PARTY_LICENSES.md).

## Tecnologias e licença

O aplicativo usa Python, Qt for Python/PySide6 e pypdf. Consulte os avisos de terceiros antes de distribuir um pacote. A licença própria do FORNAX Forge ainda deve ser definida e adicionada ao repositório antes da publicação ampla.
