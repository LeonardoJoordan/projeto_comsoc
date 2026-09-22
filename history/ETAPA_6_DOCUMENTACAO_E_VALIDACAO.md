# Etapa 6 — documentação e revisão integrada

22/09/2026 — Linux x86_64, Python 3.13.11, Qt/PySide6 Essentials 6.11.0.
**Documentação e revisão local realizadas; aprovação dos instaladores finais permanece pendente.** Este registro não certifica segurança nem conformidade jurídica integral. Não houve publicação, assinatura de release ou criação de repositório.

## 6.1 — Documentação e compatibilidade

- README atualizado para os menus **Arquivo** e **Configurações**, comando de testes atual e distinção entre documentação operacional e histórica.
- Guia de frente/verso atualizado: biblioteca `.fornax`, documento interno v4, backup do contêiner e exportação individual/lote. Retiradas instruções antigas de operar diretamente com `template_v4.json`.
- Guia de modelos atualizado com abertura sem pergunta automática de senha, botão **Desbloquear/Bloquear modelo** e menu de proteção no escudo do editor.
- Antiga lista de pedidos de SVGs substituída por orientação ligada ao inventário real. O PDF antigo é identificado como histórico e continua excluído do pacote.
- [Inventário de referências preservadas](../docs/REFERENCIAS_LEGADAS_E_REPOSITORIO.md): caminhos COMSOC, preferências, diário de migração, identidades de instalação e três URLs do Inno Setup. O remoto antigo permanece até a criação do novo repositório.
- Testes sintéticos de migração continuam exercitando conflitos, cópia verificada, retomada, preservação de preferências e modelos já existentes. Não houve alteração das bibliotecas reais do usuário.

## 6.2 — Ajustes e verificações de distribuição

- Inno Setup utiliza LICENSE, aviso e documentos presentes no standalone compilado. Não sobrepõe a compilação com outra revisão documental da árvore de desenvolvimento.
- AppImage copia seus avisos do mesmo standalone, incluindo SECURITY.md.
- Inventário macOS passa a ser calculado depois da alteração de Info.plist e da renomeação do bundle, para não publicar hashes anteriores à associação `.fornax`. Compilação e instalação macOS continuam não executadas aqui.
- Seleção de release inclui os guias atuais e checklist. Preparação sintética produziu 453 arquivos; confirmou documentos legais e guias presentes e exclusão de histórico/testes/caches. Essa seleção de fontes não é a contagem de arquivos do binário final.
- Sintaxe shell, compilação Python dos scripts e quatro testes de empacotamento aprovados após os ajustes.
- Revisão estática das associações: comando Windows preserva aspas no executável/argumento; desktop Linux encaminha `%F`; MIME e extensão permanecem consistentes. Isso não substitui duplo clique no sistema instalado.

## Evidências de execução

| Referência | Testes aprovados | Pulados | Avisos | Subtestes aprovados |
|---|---:|---:|---:|---:|
| Relatório inicial | 423 | 1 | 1 | 12 |
| Etapa 5, suíte completa | 472 | 1 | 1 | 12 |
| Etapa 6, suíte completa | **473** | **1** | **1** | **12** |

Suíte atual: **333,81 segundos**, sem falhas. O teste adicional é o de remoção restrita do plugin PDF, que na etapa 5 havia sido executado separadamente. Não é um benchmark de desempenho do aplicativo. O pulo padrão corresponde ao IPC nativo, executado separadamente abaixo.

- IPC nativo: **3 testes aprovados**, incluindo envio entre processos com espaços/acentos, preservação do servidor ativo e liberação do socket. A tentativa restrita falhou ao criar socket; a repetição fora da sandbox passou. Não foi tratada como defeito do aplicativo.
- Revisão do aviso existente: `table_panel.py:243` passa um inteiro à sobrecarga depreciada de `QTableWidgetItem.setTextAlignment`. Os testes não indicaram falha funcional; a atualização para enum fica identificada como manutenção de API, sem ocultar o aviso.
- A suíte inclui testes de descarte de cena/histórico/clipboard, cache de imagens protegidas em memória, cancelamento/falha de prévia, liberação após geração e encerramento abrupto em subprocesso, verificando ausência de conteúdo protegido em claro nos artefatos sintéticos.
- Inicialização do standalone Linux da etapa 5 observada com `strace -f -e trace=network`, dados/configuração/cache temporários isolados e Qt offscreen durante seis segundos: sem chamadas AF_INET/AF_INET6; comunicação AF_UNIX local de instância única observada. Encerramento deliberado por timeout (124), sem traceback. Não representa observação dinâmica de todos os fluxos, impressão ou instalações.
- Revisão estática de runtime não encontrou cliente HTTP, atualização automática ou telemetria. QtNetwork atende ao IPC local. Links externos e abertura explícita de pastas são distintos de transmissão automática de dados.

Evidências locais: `build/security/stage6-tests.xml`; logs de testes e observação de rede em `/tmp/fornax-stage6-*`. Os temporários não são arquivo permanente de release; preservar as evidências necessárias antes da limpeza. A compilação observada antecede os ajustes documentais/empacotamento desta etapa e deve ser refeita para publicação.

## O que ainda impede declarar os pacotes prontos para publicação

1. Testar os instaladores finais no sistema alvo: instalação, associação/ícone, duplo clique, atualização/desinstalação, impressão e caminhos/permissões. Windows/Inno, AppImage, Flatpak e macOS não foram instalados nesta etapa. O Flatpak ainda requer wheelhouse compatível com seu SDK; AppImage requer appimagetool.
2. Fechar a correspondência entre bibliotecas nativas, fontes, avisos e receitas do artefato efetivamente publicado, conforme a etapa 5. Fontes baixados apenas localmente não estão entregues ao destinatário.
3. Definir versão, reconstruir a partir do commit de release, recalcular hashes dos pacotes finais e repetir as análises no estado publicado. Nenhum artefato está assinado por este trabalho.
4. Executar a CI no repositório e habilitar/testar o canal privado de segurança. A mudança para o novo repositório continua sendo trabalho posterior autorizado separadamente.

O [checklist de distribuição](../docs/CHECKLIST_DISTRIBUICAO_FORNAX.md) mantém a matriz nativa sem aprovação presumida. Os testes locais não deixam uma regressão funcional conhecida sem registro, mas tampouco garantem ausência de falhas futuras.
