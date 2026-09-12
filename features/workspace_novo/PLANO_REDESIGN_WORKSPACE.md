# Plano de redesenho do workspace

Objetivo: tornar a tela inicial familiar e adequada a um produto final, preservando o fluxo operacional e mantendo todas as alterações em `workspace_novo` e `spreadsheet_novo`.

## Regras fixas

- Prévia à esquerda e tabela à direita, com divisor ajustável.
- Seleção de modelo sempre visível.
- Novo modelo e Editar modelo sempre acessíveis.
- Colagem da planilha externa e prévia por linha preservadas.
- Editor aberto pelo workspace: somente `editor_novo`.
- Diretórios legados não serão modificados.

## Etapas

- [x] 1. Isolar `workspace_novo`, `spreadsheet_novo` e `editor_novo`.
- [x] 2. Modernizar a apresentação básica da tabela.
- [x] 3. Criar barra de menus: Arquivo, Modelo, Dados, Exibir e Ajuda.
- [x] 4. Criar barra superior de contexto do modelo com seleção, Novo e Editar.
- [x] 5. Reorganizar a área principal em Prévia | Tabela.
- [x] 6. Transformar mensagens de processamento em painel recolhível.
- [x] 7. Reorganizar os controles de geração numa faixa inferior compacta.
- [x] 8. Criar Sobre e ponto de entrada para Licenças de terceiros.
- [x] 9. Validar seleção, tabela, prévia, editor e controles de geração sem regressões.

## Validação executada

- Inicialização isolada pelo `workspace_novo/main.py`.
- Carregamento e troca do modelo ativo com atualização da prévia.
- Inclusão e duplicação de linhas na tabela.
- Abertura e recolhimento das mensagens de processamento.
- Abertura de um novo documento no `editor_novo`.
- Verificação de sintaxe de `workspace_novo` e `spreadsheet_novo`.

O processamento completo de um lote real deve integrar a validação final anterior à distribuição, pois grava arquivos no destino escolhido pelo operador.

## Decisões para uma etapa posterior

- Conteúdo final de autoria, versão, site e créditos institucionais do diálogo Sobre.
- Auditoria de todas as licenças e montagem dos textos distribuídos no instalador.
