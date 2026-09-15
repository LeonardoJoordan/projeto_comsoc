# Tradução do FORNAX Forge

Idioma original: português do Brasil (`pt_BR`).

Primeiro idioma adicional: inglês dos Estados Unidos (`en_US`).

Segundo idioma adicional: espanhol (`es_ES`).

## Regras

- Usar o sistema de tradução do Qt com catálogos `.ts` e `.qm`.
- Preservar identificadores internos, nomes de modelos, placeholders e conteúdo do usuário.
- Salvar códigos de localidade nas preferências, nunca o texto exibido no menu.
- Aplicar mudanças de idioma na próxima inicialização do programa.
- Manter os catálogos oficiais dentro de `assets/translations/`.
- Deixar a estrutura preparada para novos catálogos oficiais ou comunitários.

## Etapas

- [x] Criar carregamento central e persistência do idioma.
- [x] Criar `Programa > Idioma` com português e inglês.
- [x] Traduzir a estrutura principal do workspace.
- [x] Traduzir navegação do preview e controles da tabela.
- [x] Compilar e validar o primeiro catálogo `en_US`.
- [x] Traduzir todos os textos visíveis do editor.
- [x] Traduzir configurações de exportação, temas e importação/exportação de modelos.
- [x] Traduzir confirmações, erros e mensagens de processamento do workspace.
- [x] Revisar pluralização, textos longos e larguras no inglês.
- [x] Fazer uma varredura final para localizar textos visíveis sem `tr()`.
- [x] Validar os fluxos completos em `pt_BR` e `en_US` antes da distribuição.
- [x] Criar, revisar, compilar e integrar o catálogo `es_ES`.
- [x] Validar os fluxos completos em `es_ES` antes da distribuição.

## Atualização do catálogo

Após marcar novos textos com `tr()`, atualizar o arquivo `.ts` com `pyside6-lupdate`,
revisar as traduções e gerar o `.qm` com `pyside6-lrelease`.
