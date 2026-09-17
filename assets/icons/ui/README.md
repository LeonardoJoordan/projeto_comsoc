# Ícones funcionais da interface

Coloque os SVGs usando exatamente os nomes abaixo. Um único conjunto visual deve ser usado para que espessura, terminais e proporções sejam coerentes.

## Requisitos dos arquivos

- SVG vetorial, sem imagem raster incorporada.
- `viewBox="0 0 24 24"` sempre que possível.
- Desenho monocromático.
- Preferência por traço de aproximadamente 1,7 a 2 unidades.
- Sem fundo, sombra ou retângulo de enquadramento.
- Cor do desenho configurável pelo programa. Evitar estilos complexos e gradientes.
- Cantos e terminações consistentes em todo o conjunto.
- Licença que permita redistribuição com o aplicativo.

## `navigation/`

| Arquivo | Substitui | Uso |
|---|---|---|
| `chevron-left.svg` | `‹` | Item/folha anterior e expansão lateral |
| `chevron-right.svg` | `›` | Próximo item/folha e expansão lateral |
| `chevron-down.svg` | `⌄` | Cabeçalhos recolhíveis e comboboxes |
| `chevron-up.svg` | símbolo de recolhimento | Cabeçalhos quando necessário |
| `double-chevron-left.svg` | controle textual | Recolher a tabela de dados |
| `double-chevron-right.svg` | controle textual | Expandir a tabela de dados |
| `left-arrow.svg` | `‹` | Item ou folha anterior |
| `right-arrow.svg` | `›` | Próximo item ou folha |
| `layer-child.svg` | indicador desenhado | Vínculo entre máscara e imagem |
| `spin-up.svg` | seta nativa | Incrementar campos numéricos |
| `spin-down.svg` | seta nativa | Decrementar campos numéricos |
| `combo-down.svg` | seta nativa | Abrir caixas de seleção |

## `actions/`

| Arquivo | Substitui | Uso |
|---|---|---|
| `add.svg` | `➕` | Adicionar linha ou modelo |
| `duplicate.svg` | `📑` | Duplicar linha, camada ou modelo |
| `delete.svg` | `🗑️` | Excluir e limpar guias |
| `edit.svg` | `✏️` / `📝` | Renomear ou editar |
| `import.svg` | `📥` | Importar modelos |
| `export.svg` | `📤` | Exportar modelos |
| `undo.svg` | `⬅️` | Desfazer |
| `redo.svg` | `➡️` | Refazer |
| `rotate-left.svg` | `↪️` | Rotação de 90° à esquerda |
| `rotate-right.svg` | `↩️` | Rotação de 90° à direita |
| `rotation-reset.svg` | `⬆️` | Zerar rotação |
| `link.svg` | `🔗` | Manter proporção ou habilitar link |
| `restore.svg` | `🔄` | Restaurar estado original |
| `expand-content.svg` | `↕️` | Exibir conteúdo completo das células |
| `more.svg` | `…` | Selecionar a pasta de saída |
| `more-vertical.svg` | `⋮` | Menu de ações do modelo |

## `align/`

| Arquivo | Substitui | Uso |
|---|---|---|
| `bold.svg` | `B` | Aplicar negrito ao texto selecionado |
| `italic.svg` | `I` | Aplicar itálico ao texto selecionado |
| `underline.svg` | `U` | Aplicar sublinhado ao texto selecionado |

## `objects/`

| Arquivo | Substitui | Uso |
|---|---|---|
| `text.svg` | `📝` | Adicionar ou representar texto |
| `square.svg` | forma desenhada no código | Quadrado/retângulo no menu de formas |
| `circle.svg` | forma desenhada no código | Círculo/elipse no menu de formas |
| `line.svg` | forma desenhada no código | Linha no menu de formas |
| `image.svg` | `📸` / `🖼️` | Adicionar ou representar imagem |
| `signature.svg` | `✍️` | Assinatura e cabeçalho da coluna |
| `quantity.svg` | `🔢` | Cabeçalho da coluna de quantidade |

## `state/`

| Arquivo | Substitui | Uso |
|---|---|---|
| `eye.svg` | `👁️` | Item ou guia visível |
| `eye-off.svg` | variação de visibilidade | Item ou guia oculto |
| `lock.svg` | `🔒` | Item ou guia bloqueado |
| `unlock.svg` | `🔓` | Item ou guia desbloqueado |
| `warning.svg` | `⚠️` | Avisos visuais |
| `info.svg` | `ℹ️` | Informações contextuais |
| `success.svg` | `✅` | Validação bem-sucedida |
| `error.svg` | `❌` | Erro de validação |
| `settings.svg` | `⚙️` | Configuração |
| `opacity.svg` | `Op.` / `α` | Identificação dos campos de opacidade |

## Símbolos usados somente no log

Os símbolos `📋`, `⚡`, `🛑`, `📚`, `🚀`, `📦`, `🖨️`, `📂`, `⏱️`, `🌱` e `✨` aparecem em mensagens textuais. Não precisam de SVG para os botões. Antes da estabilização multiplataforma deve ser decidido se serão removidos, mantidos como decoração variável ou substituídos por uma coluna de status com os ícones `state/`.
