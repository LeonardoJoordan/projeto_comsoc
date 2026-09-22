# Procedência dos recursos do FORNAX Forge

Data do inventário: 21/09/2026.

Este documento controla a origem e a autorização de redistribuição dos recursos incorporados ao aplicativo. Um arquivo só pode ser considerado liberado para publicação quando possuir autor ou fornecedor, origem verificável e licença ou declaração de criação própria.

## Situação conhecida

| Grupo | Arquivos | Situação | Evidência |
|---|---|---|---|
| Fonte Inter | `assets/fonts/ui/*.ttf` | Verificada | SIL Open Font License 1.1 em `assets/fonts/ui/OFL.txt`; origem indicada em `assets/fonts/ui/README.txt` |
| Traduções | `assets/translations/*.ts` e `*.qm` | Produzidas no projeto | Catálogos mantidos junto ao código; os `.qm` são compilados dos `.ts` |
| Temas | `assets/themes/*.json` | Produzidos no projeto | Configurações próprias do FORNAX; cobertas pela GPL-3.0-only |
| Integração Linux | `assets/linux/com.leobelisario.FornaxForge.xml` | Produzida no projeto | Metadado técnico próprio do formato `.fornax` |
| Marca e ícone do aplicativo | `assets/icons/fornax-forge.ico` e `assets/icons/fornax-forge_*.png` | **Evidência a completar** | Imagem gerada com auxílio de IA e posteriormente editada no Photoshop por Leonardo Joordan Belisário Lima da Silva; preservar o arquivo-fonte, data, ferramenta e termos aplicáveis antes da publicação |
| Ícones funcionais SVG | `assets/icons/ui/**/*.svg` | **Substituição obrigatória** | Arquivos obtidos ou adaptados a partir do Flaticon Premium; serão substituídos por desenhos originais antes da publicação do repositório e de novos pacotes públicos |
| Guia antigo de ícones | `assets/icons/ui/README.md` e `README.pdf` | Não é recurso da interface | Material de desenvolvimento; deve ser excluído dos pacotes finais na Etapa 5 |

Metadados `sodipodi:docname` encontrados em alguns SVGs apenas registram nomes de edição. Eles não demonstram autoria nem autorização de redistribuição.

## Inventário gráfico pendente

### Marca do aplicativo

- `fornax-forge.ico`
- `fornax-forge_32.png`, `fornax-forge_48.png`, `fornax-forge_64.png`
- `fornax-forge_128.png`, `fornax-forge_256.png`, `fornax-forge_512.png`, `fornax-forge_1024.png`

### `ui/actions`

- `delete.svg`, `duplicate.svg`, `edit.svg`, `expand-content.svg`, `group.svg`
- `link.svg`, `lock ratio.svg`, `more-vertical.svg`, `more.svg`
- `redo.svg`, `rotate-left.svg`, `rotate-right.svg`, `undo.svg`, `unlock ratio.svg`

### `ui/align`

- `bold.svg`, `italic.svg`, `underline.svg`, `paragraph.svg`, `line-space.svg`
- `left-align.svg`, `center-align.svg`, `right-align.svg`, `justify.svg`
- `top-alignment.svg`, `mid-alignment.svg`, `bot-alignment.svg`
- `straight_edge.svg`, `curved_edge.svg`
- `sup_dir.svg`, `sup_esq.svg`, `inf_dir.svg`, `inf_esq.svg`

### `ui/navigation`

- `chevron-back.svg`, `chevron-down.svg`, `chevron-right.svg`, `chevron-up.svg`
- `double-chevron-left.svg`, `double-chevron-right.svg`, `left-arrow.svg`, `right-arrow.svg`
- `layer-child.svg`

### `ui/objects`

- `circle.svg`, `image.svg`, `line.svg`, `quantity.svg`, `shapes.svg`
- `signature.svg`, `square.svg`, `text.svg`

### `ui/state`

- `eye.svg`, `guide.svg`, `h.guide.svg`, `l.guide.svg`, `v.guide.svg`
- `lock.svg`, `unlock.svg`, `opacity.svg`, `settings.svg`

## Como encerrar uma pendência

Para recurso criado por Leonardo Joordan Belisário Lima da Silva, registrar uma declaração simples com data aproximada e confirmar que não contém partes copiadas de outro conjunto sem autorização.

Para recurso obtido ou adaptado de terceiros, registrar:

1. autor ou fornecedor;
2. URL da página original ou comprovante preservado;
3. nome e versão da licença vigente quando o recurso foi obtido;
4. alterações realizadas;
5. texto de licença e atribuição exigida no pacote.

Uma assinatura Premium do Flaticon dispensa atribuição nos usos cobertos pelos termos do serviço, mas não transforma os SVGs em recursos sublicenciáveis sob a GPL nem autoriza sua disponibilização como arquivos reutilizáveis de um repositório aberto. Alterações visuais nos arquivos não eliminam automaticamente essa dependência de origem. Por isso, todos os SVGs funcionais atuais estão bloqueados para publicação até serem substituídos.

Se a origem não puder ser comprovada, substituir somente o arquivo pendente por um recurso próprio ou de licença conhecida antes da publicação. Sem uma dessas evidências, o recurso permanece fora do conjunto considerado pronto para distribuição.
