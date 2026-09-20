# Checkpoint 4.5 — consolidação para distribuição

Data: 20/09/2026.
Estado: **documentação de fechamento preparada; liberação pendente**.
Não é certificação, auditoria externa nem aprovação dos pacotes finais.

## Resultado consolidado

| Área | Evidência | Estado |
|---|---|---|
| Inventário, contratos e referência | ETAPA_1_REFERENCIA_E_MAPA_FORNAX.md | Concluído |
| Formato, criptografia e migração especificados | ETAPA_2_ESPECIFICACAO_FORMATO_FORNAX.md | Concluído |
| Implementação 3.1–3.10 | ETAPA_3_IMPLEMENTACAO_FORNAX.md e testes específicos | Implementada; distribuição nativa depende de 4.4 |
| Textos/ajuda/traduções 3.11 | Catálogos existentes; novo guia em português | Incompleto |
| Revisão interna 4.1–4.3 | ETAPA_4_REVISAO_FORNAX.md | Concluída no escopo registrado |
| Regressão 4.4 | Mesmo relatório + ETAPA_4_4_MEDICOES_FORNAX.json | Local concluída; gates nativos/hardware pendentes |
| Fechamento 4.5 | Este relatório e checklist em docs/ | Preparado, sem aprovação de distribuição |

A coleta final registrada no 4.4 teve 314 testes gerais e 12 subtestes aprovados,
um teste IPC pulado na suíte comum e aprovado na bateria nativa separada de seis
testes. A bateria do editor teve 63 aprovações. Não são novos testes executados
no 4.5 nem devem ser somados sem considerar sobreposição.

Os PNGs protegidos mantiveram os hashes da referência. A mediana de desbloqueio
ficou em aproximadamente 116 ms no ambiente medido; isso não representa hardware
modesto. Tabela de tempos e limitações estão na evidência 4.4.

## Entregas deste checkpoint

- `docs/GUIA_MODELOS_FORNAX.md`: formatos, três modos, senha perdida, tolerância,
  cópia sem assinaturas, compartilhamento, migração e recuperação.
- `docs/CHECKLIST_DISTRIBUICAO_FORNAX.md`: matriz nativa por pacote, testes de
  instalação/associação, filesystems, desempenho e campos de evidência.
- README atualizado para o armazenamento `.fornax`, compatibilidade ZIP e caminhos
  atuais da documentação. Não anuncia a versão como pronta.
- Inventário abaixo separa ambiente de desenvolvimento de pacote distribuído.

## Dependências observadas nesta revisão

Lidas do ambiente `.venv`, sem instalar ou atualizar pacotes:

| Componente | Versão local |
|---|---|
| Python | 3.13.11 |
| PySide6 / Essentials / Addons / shiboken6 | 6.11.0 |
| cryptography | 50.0.1 |
| cffi | 2.1.1 |
| pycparser | 3.0 |
| pypdf | 6.14.2 |
| Nuitka | 4.0.7 |
| zstandard | 0.25.0 |
| Backend OpenSSL reportado por cryptography | 4.0.2, 25 Aug 2026 |

SO: Linux 7.0.0-31 x86_64/glibc 2.39. Este inventário não descreve um instalador
Windows/macOS nem os pacotes Flatpak/AppImage finais. `requirements.txt` fixa Qt,
pypdf e cryptography, mas deixa ferramentas de build com limites mínimos e não
fixa todas as transitivas. Registrar versões/hashes resolvidos por release.

O inventário de licenças em `docs/THIRD_PARTY_LICENSES.md` descreve uma inspeção
Windows anterior. Sua referência a OpenSSL 3.x não deve ser aplicada ao backend
Linux atual, nem o backend atual deve substituir o inventário de um pacote que
não foi inspecionado. Conferir avisos e bibliotecas efetivamente empacotados.

## Pendências que impedem fechar a liberação

### 1. Checkpoint 3.11 ainda incompleto

Os testes atuais verificam as strings chamadas por `tr()`, mas não provam que todo
texto exibido foi envolvido por essa função. Exemplos identificados:
`password_bytes()` em `core/fornax_container.py` lança mensagens em português;
`_request_new_fornax_password()` no editor exibe `str(error)` diretamente.
Importação, sessão e outras falhas também possuem detalhes técnicos não localizados.

Solução: revisar a fronteira entre erro técnico e mensagem ao usuário, traduzir
os fluxos restantes e testar senha inválida/arquivo inválido em EN/ES. Evitar
traduzir identificadores persistidos ou usar mensagem traduzida como código de erro.
O guia criado aqui está em português; disponibilizar ajuda acessível na interface
e equivalentes em inglês/espanhol antes de marcar 3.11 concluído. Não mudar o
roteiro aprovado do tutorial de primeiros passos sem necessidade.

### 2. Pacotes nativos e hardware modesto

Nenhum resultado offscreen aprova instalação, portal, eventos macOS ou associação
real no sistema. Executar a matriz do checklist e registrar os artefatos exatos.
Clang, exigido pelo script Nuitka, não está presente no ambiente Linux revisado.
A declaração MIME do AppImage não instala sozinha a associação no host.

### 3. Conteúdo de distribuição e avisos

Nuitka inclui `assets`, mas não há uma etapa geral explícita de coleta dos avisos
completos de todas as dependências. Inno copia três documentos de `docs/` para
`licenses`; isso, por si só, não comprova entrega dos textos integrais exigidos
pelo checklist existente. Flatpak copia código/assets e não esses documentos.
Os guias novos também ainda não fazem parte de uma ajuda empacotada.

Solução: inventariar cada artefato, completar os avisos correspondentes e sua
inclusão no build. Preservar o inventário anterior como histórico, sem declarar
que a lista de DLLs dele corresponde aos novos pacotes. Não alterar licenças ou
termos do produto por inferência desta revisão técnica.

### 4. Publicação em volumes e apresentação de medidas

Publicação de arquivos novos usa hard link; volumes sem suporte falham preservando
a origem, sem fallback. Testar FAT/exFAT e rede; resolver suporte ou documentar
limitação explicitamente para a distribuição escolhida.

A correção de carregamento preserva os pixels salvos. A apresentação das réguas
em modelos com proporção pixels/mm diferente de 300 dpi ainda requer conferência
visual específica. Não prometer equivalência completa desse cenário com base
apenas no hash das imagens renderizadas.

### 5. Garantias e riscos conhecidos

Criptografia não autentica autoria de PNG/PDF gerado, não impede captura do que
foi autorizado a exibir e não converte imagens comuns em assinaturas protegidas.
Não há recuperação de senha. Nome do arquivo/metadados técnicos permanecem
visíveis; cópias antigas externas não são revogadas. Limpeza lógica não garante
apagamento físico de RAM/disco/swap. Revisão especializada independente não feita.
Esses limites constam do guia; não criar alegações de certificação.

## Ordem de retomada

1. Concluir 3.11: erros exibidos, ajuda acessível e EN/ES, com testes de interface.
2. Preparar conteúdo/licenças de cada pacote e executar gates nativos/hardware
   do 4.4. Resolver falhas encontradas e registrar evidências, sem marcar por previsão.
3. Revisar este relatório com os resultados e só então concluir 4.5.

Não repetir as migrações na biblioteca real nem sobrescrever as medições iniciais.
Nenhum modelo real, senha, associação do sistema ou pacote instalado foi alterado
por este checkpoint documental.

## Verificação desta entrega

- Links locais dos novos guias, relatório e README conferidos.
- `git diff --check` sem erros.
- `tests/test_i18n.py`: 3 testes aprovados em 0,37 s. Esse resultado confirma
  cobertura das chamadas `tr()` existentes, não dos erros diretos identificados.
- Nenhuma alteração no código de execução; não houve nova bateria funcional
  completa nem nova coleta de desempenho neste checkpoint documental.
