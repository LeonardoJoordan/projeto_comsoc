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
- biblioteca local em `.fornax`, exportação individual ou lote ZIP e importação de ZIPs antigos;
- assinaturas públicas ou protegidas por senha e proteção integral opcional do modelo.

O fluxo de criação, exportação, recuperação e impressão duplex está descrito em [Modelos com frente e verso](docs/MODELOS_FRENTE_VERSO.md).

O motor de renderização é compartilhado pelo editor, pela prévia e pela geração final. Isso mantém posição, tipografia, transparência e dimensões físicas consistentes ao longo do fluxo.

O formato e a proteção estão em validação para distribuição. Consulte o
[guia de modelos `.fornax`](docs/GUIA_MODELOS_FORNAX.md) e o
[revisão final e pendências de distribuição](history/ETAPA_6_DOCUMENTACAO_E_VALIDACAO.md).

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
docs/                    guias atuais, licenças e avisos
history/                 planos e evidências de etapas anteriores
```

O projeto nasceu como COMSOC. Os registros anteriores permanecem em `history/` e `docs/historico/`; não são instruções operacionais da versão atual.

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

Em **Configurações > Tema da interface…**, escolha entre os cinco temas padrão: **Carbono** (preto e cinza profundo), **Marinho** (azul escuro), **Grafite** (cinza médio), **Rosê** (rosa envelhecido e sépia) e **Pérola** (claro). Os perfis personalizados salvos também aparecem nessa lista. O botão **Criar tema**, no rodapé, abre uma segunda janela com os controles avançados de cores e o nome do novo perfil. A interface mostra a prévia imediatamente; Cancelar restaura o tema anterior. Os arquivos oficiais ficam em `assets/themes/` e as personalizações em `themes/` dentro da pasta de dados do aplicativo. As cores dos documentos e arquivos gerados não são alteradas.

O FORNAX Forge usa o identificador técnico `com.leobelisario.FornaxForge`. No primeiro acesso, dados encontrados no diretório da instalação COMSOC são copiados para a nova área. Modelos já existentes no destino são preservados integralmente, sem mesclar assets. A cópia é verificada antes de ser publicada, sua conclusão fica registrada e a origem não é apagada. Uma interrupção pode ser retomada; modelos excluídos após a migração não são recriados. Conflitos podem ser resolvidos posteriormente pela importação de modelos.

As preferências visuais e de exportação também são copiadas do namespace antigo somente quando ainda não possuem valor no FORNAX Forge. Modelos existentes em `template_v3.json` e `template_v4.json` continuam compatíveis. Ao selecionar uma pasta legada na biblioteca, o programa converte o modelo para `.fornax`, normaliza o documento e recomenda proteção quando houver assinaturas. O usuário pode proteger as assinaturas, proteger o modelo inteiro ou aceitar conscientemente o armazenamento público. O JSON versionado passa a integrar o contêiner. Backup e recuperação seguem as regras descritas no [guia de modelos](docs/GUIA_MODELOS_FORNAX.md).

Em uma instalação Flatpak, cada identificador possui uma sandbox própria. Nesse caso, use **Modelo > Exportar modelos** no COMSOC e **Arquivo > Importar modelos…** no FORNAX Forge quando a sandbox nova não conseguir acessar os dados antigos.

## Testes

```bash
python -m pip install -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen python -m pytest --import-mode=importlib -q tests features/editor
```

Os testes offscreen verificam o comportamento funcional, mas não substituem a validação nativa dos controles de janela, impressão e pacotes em Windows, Linux e macOS.

## Distribuição

A preparação, os locks, os inventários e as pendências de fontes/licenças estão em [docs/RELEASE.md](docs/RELEASE.md).

Antes de publicar, conclua o [checklist de distribuição](docs/CHECKLIST_DISTRIBUICAO_FORNAX.md). Testes locais não aprovam automaticamente os pacotes nativos.

- `script_nuitka.py`: executável nativo com Nuitka; instalar `requirements-build.txt` em ambiente limpo;
- `script_appimage.sh`: AppImage Linux criado a partir da saída Nuitka, incluindo o Qt do próprio standalone;
- `com.leobelisario.FornaxForge.yaml`: manifesto Flatpak.

O Nuitka usa até quatro tarefas de compilação por padrão, respeitando o número de CPUs. É possível ajustar com `FORNAX_BUILD_JOBS`. O AppImage exige a compilação standalone concluída e `appimagetool` na raiz. Para registrar `.fornax` e seu ícone na execução Linux pelo código, execute `python3 tools/install_linux_integration.py`; para um AppImage instalado, use `--appimage /caminho/FORNAX_Forge.AppImage`. Veja os detalhes no [checklist](docs/CHECKLIST_DISTRIBUICAO_FORNAX.md).

No Windows, depois de gerar `build/main.dist`, compile `instalador.iss` com Inno Setup 6. O script usa a versão `1.0.0`; atualize `AppVersion` a cada release sem alterar o `AppId`. Faça a compilação em ambiente virtual limpo para que as versões do binário coincidam com `requirements.txt` e complete o checklist de `docs/THIRD_PARTY_LICENSES.md` antes de publicar.

Os ícones oficiais ficam em `assets/icons/`: PNGs dimensionados para a interface e Linux, além do ICO multirresolução para Windows. O PNG de 1024 px é usado como fonte do pacote macOS. Antes da publicação, o inventário e os textos integrais das licenças do pacote devem ser concluídos conforme [docs/THIRD_PARTY_LICENSES.md](docs/THIRD_PARTY_LICENSES.md).

## Tecnologias e licença

O aplicativo usa Python, Qt for Python/PySide6, pypdf e cryptography. O código e a documentação próprios do FORNAX Forge são licenciados sob a **GNU General Public License v3.0 exclusivamente** (`GPL-3.0-only`). Consulte [LICENSE](LICENSE), [NOTICE](NOTICE) e os [avisos de terceiros](docs/THIRD_PARTY_LICENSES.md) antes de distribuir uma cópia.

O nome **FORNAX Forge** e o logotipo identificam o projeto oficial e seguem a política descrita em [TRADEMARKS.md](TRADEMARKS.md). Modelos, textos, imagens, fontes, planilhas e materiais produzidos pelos usuários não passam automaticamente a integrar o programa nem a ser licenciados sob a GPL. Consulte também as [orientações para uso institucional](docs/USO_INSTITUCIONAL.md).

**Recursos gráficos:** os SVGs foram substituídos por recursos declarados como Lucide, Google Material e Bootstrap Icons. As licenças oficiais estão em `docs/licenses/`; o [inventário de procedência](docs/ASSET_PROVENANCE.md) registra as identificações por arquivo e a autoria dos SVGs próprios feitos no Inkscape. A procedência declarada da marca e os limites das evidências também estão registrados nesse inventário.
