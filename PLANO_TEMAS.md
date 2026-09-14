# Temas do FORNAX Forge

Objetivo: preservar o layout aprovado, centralizar as cores de interface e permitir temas personalizados sem alterar a arte, prévia ou exportação.

- [x] Definir temas JSON com funções de cor, validação e fallback.
- [x] Implementar gerenciador compartilhado, persistência e leitura compatível de dark_mode.
- [x] Migrar estilos de workspace, editor, planilha e diálogos.
- [x] Integrar ícones, réguas, seleção e guias sem afetar cores do documento.
- [x] Modal com prévia, cancelamento, restaurar padrão e salvar tema personalizado.
- [x] Validar troca repetida, persistência, cores inválidas e estabilidade da renderização.

Temas oficiais ficam em assets/themes. Personalizações ficam na pasta de dados do usuário; nunca em modelos. A troca de tema não reconstrói janelas, não executa renderização de documentos e não lê JSON durante pintura de células/objetos.

## Resultado

Implementados Carbono, Marinho, Grafite, Rosê e Pérola em um seletor simples. O combobox contém somente temas oficiais e perfis já criados. O botão `Criar tema`, alinhado à esquerda do rodapé, abre um segundo modal com as nove cores editáveis e o nome do novo perfil; Aplicar e Cancelar permanecem agrupados à direita. Alterações de destaque ajustam hover e texto do botão. Temas personalizados são gravados atomicamente em themes/custom-<id>.json e passam a aparecer no seletor principal. Cancelar o editor avançado restaura sua base; cancelar o seletor principal restaura o tema que estava ativo antes de abri-lo. Confirmar o seletor persiste theme/id. Arquivos ausentes ou inválidos na inicialização retornam a um tema oficial. Cores de amostras da arte não são convertidas.

Marinho e Pérola preservam os identificadores `dark` e `light` para manter preferências existentes. Os três novos perfis usam `carbon`, `graphite` e `rose`. Checkboxes e radio buttons possuem indicadores explícitos com estados marcado, desmarcado, hover e desabilitado; a checkbox também cobre estado parcial. O contraste mínimo testado é 4,5:1 para texto principal e texto do botão de destaque, e 3:1 para contornos ativos das checkboxes em relação ao campo e fundo principal. As cores de ações destrutivas separam texto de fundo para manter a seleção do menu legível.

Estilos usam tokens explícitos (@field@, @text@ etc.), sem substituição de hexadecimais em execução. Ícones SVG das ferramentas e setas são atualizados por tema; os ícones da marca são preservados. QSS por widget é reaplicado somente na mudança de tema. Recursos assets já estão incluídos no empacotamento.

Validação: testes de cancelamento, tema personalizado, fallback, amostras de cores e igualdade de renderização; smoke de workspace/editor com troca claro–escuro–claro, inspeção offscreen do editor claro. O ajuste visual fino em sistemas nativos e contraste de combinações arbitrárias do usuário continuam sendo itens de revisão visual, não garantia dos testes automatizados. Importação/exportação de temas pela interface permanece uma extensão futura.
