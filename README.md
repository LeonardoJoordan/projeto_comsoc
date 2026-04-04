# C.O.M.S.O.C.
**Construtor Otimizado de Material Social Oficial e Cerimonial**

O **C.O.M.S.O.C.** é um sistema autônomo desenvolvido para modernizar a produtividade e a padronização visual das seções de Comunicação Social das Organizações Militares. O projeto substitui processos manuais e repetitivos por uma automação de alto desempenho, garantindo a excelência da imagem institucional da Força.

## 🎖️ Impacto no Desempenho Operacional
* **Multiplicação da Força de Trabalho**: Reduz o tempo de confecção de aproximadamente 2 minutos por documento para a geração de 100 documentos personalizados em menos de 2 minutos.
* **Zero Erro Humano**: A importação direta de dados e a visualização em tempo real eliminam erros de digitação em postos, nomes e autoridades, garantindo 100% de conformidade visual.
* **Independência Tecnológica**: Desenvolvido para rodar de forma fluida em hardware legado e sistemas Linux, eliminando a dependência de softwares proprietários e licenças onerosas.
* **Segurança da Informação**: Funciona 100% offline e de forma nativa, extinguindo a necessidade de militares utilizarem computadores pessoais para missões de design.

## 🚀 Funcionalidades Principais
* **Editor Visual WYSIWYG**: Interface para criação de templates com placeholders dinâmicos (ex: `{nome}`, `{posto}`).
* **Processamento de Dados Ricos**: Tabela inteligente que preserva formatações de Negrito, Itálico e Sublinhado ao colar dados do Excel ou Navegador.
* **Motor de Renderização Nativo**: Fidelidade total entre o editor (96 DPI) e o arquivo final, utilizando `QPainter` para máxima precisão gráfica.
* **Sistema de Imposição (N-up)**: Agrupamento automático de múltiplos itens em folhas A4 com marcas de corte para economia de insumos.
* **Geração Multithread**: Processamento em segundo plano que permite a geração de grandes lotes sem travar a estação de trabalho.

## 📂 Estrutura do Sistema (Vertical Slicing)
A arquitetura adota o padrão **Vertical Slicing** para garantir baixo acoplamento:
* **`core/`**: Motores de nomenclatura e lógica de slugs.
* **`features/editor/`**: Ambiente de design visual e persistência de modelos em JSON.
* **`features/generator/`**: Lógica de renderização multithread e imposição.
* **`features/spreadsheet/`**: Interface de tabela com suporte a Rich Text e sanitização de dados.
* **`features/preview/`**: Painel de visualização dinâmica proporcional.
* **`shared/`**: Componentes globais de UI e logs de sistema.

## 🛠️ Instalação e Requisitos
1.  **Ambiente**: Python 3.10+ e PySide6.
2.  **Configuração Linux (Fix Teclado BR)**:
    O sistema já vem configurado para garantir a compatibilidade do teclado PT-BR no Qt/Linux:
    ```python
    os.environ.setdefault("QT_IM_MODULE", "ibus")
    ```
3.  **Execução**:
    ```bash
    python main.py
    ```

## 📝 Fluxo de Trabalho
1.  **Modelagem**: Crie ou selecione um modelo no editor visual.
2.  **Alimentação**: Cole a lista de nomes/dados na tabela (o sistema limpa o HTML automaticamente).
3.  **Configuração**: Defina o padrão de nomes e se haverá agrupamento em folha A4.
4.  **Produção**: Gere o lote. O sistema organiza tudo em pastas datadas automaticamente.

---
*C.O.M.S.O.C. - Autonomia total para a produção de diplomas, prismas, identificações e homenagens com padrão institucional.*