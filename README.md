# C.O.M.S.O.C.
**Construtor Otimizado de Material Social Oficial e Cerimonial**

O **C.O.M.S.O.C.** é um sistema autônomo desenvolvido para modernizar a produtividade e a padronização visual das seções de Comunicação Social das Organizações Militares. O projeto substitui processos manuais e repetitivos por uma automação de alto desempenho, garantindo a excelência da imagem institucional da Força.

## 🎖️ Impacto no Desempenho Operacional
* **Multiplicação da Força de Trabalho**: Reduz o tempo de confecção de aproximadamente 2 minutos por documento para a geração de 100 documentos personalizados em menos de 2 minutos.
* **Zero Erro Humano**: A importação direta de dados e a visualização em tempo real eliminam erros de digitação em postos, nomes e autoridades, garantindo 100% de conformidade visual.
* **Independência Tecnológica**: Desenvolvido para rodar de forma fluida em hardware legado e em Linux, Windows e macOS, eliminando a dependência de softwares proprietários e licenças onerosas.
* **Segurança da Informação**: Funciona 100% offline e de forma nativa, extinguindo a necessidade de militares utilizarem computadores pessoais para missões de design.

## 🚀 Funcionalidades Principais

### Editor Visual
* **WYSIWYG com 4 tipos de elementos**: Caixas de texto com placeholders dinâmicos (ex: `{nome}`, `{posto}`), elementos de assinatura, imagens e imagem de fundo.
* **Sistema de Camadas**: Gerenciamento de camadas com reordenação por drag-and-drop, alternância de visibilidade e renomeação via duplo clique.
* **Linhas Guia**: Guias verticais e horizontais com snap automático aos limites e ao centro do documento.
* **Tipografia Completa**: Controle de fonte, tamanho, cor, alinhamento horizontal e vertical, recuo e altura de linha por elemento.
* **Dimensões Precisas**: Todos os elementos posicionados e dimensionados em milímetros (mm), com rotação livre e travamento de proporção opcional.

### Tabela de Dados
* **Processamento de Dados Ricos**: Preserva formatações de **Negrito**, *Itálico* e Sublinhado ao colar dados do Excel ou navegador.
* **Coluna de Quantidade (🔢 Qtd)**: Gera múltiplas cópias de um mesmo item sem duplicar a linha na planilha.
* **Coluna de Assinatura (✍️ Ass.)**: Ativa ou desativa o elemento de assinatura por linha individualmente.
* **Atalhos de Formatação**: `Ctrl+B`, `Ctrl+I` e `Ctrl+U` aplicam formatação diretamente nas células selecionadas.

### Geração de Lotes
* **Motor de Renderização Nativo a 300 DPI**: `QPainter` garante fidelidade total entre o editor e o arquivo final em resolução de impressão.
* **Formatos de Saída**: PNG individual por item, PDF individual por item ou PDF único consolidado (todos os itens em um só arquivo).
* **Sistema de Imposição (N-up)**: Agrupamento automático de múltiplos itens em folhas A4, com orientação automática (retrato/paisagem) e marcas de corte configuráveis.
* **Geração Multithread**: Usa `N - 2` núcleos da CPU em paralelo, mantendo a estação de trabalho responsiva durante lotes grandes.
* **Impressão Direta**: Envio para impressora sem sair do sistema.

### Gerenciamento de Modelos
* **Operações Básicas**: Criar, duplicar, renomear e remover modelos diretamente na sidebar.
* **Importação em Lote (ZIP)**: Importa múltiplos modelos de um único arquivo `.zip` com resolução inteligente de conflitos (substituir ou renomear).
* **Exportação em Lote (ZIP)**: Empacota modelos selecionados, incluindo todos os assets, em um único `.zip` portátil.

## 📂 Estrutura do Sistema (Vertical Slicing)
A arquitetura adota o padrão **Vertical Slicing** para garantir baixo acoplamento:
* **`core/`**: Motor de nomenclatura, lógica de slugs, gerenciamento de caminhos e estado de texto.
* **`features/editor/`**: Ambiente de design visual, itens do canvas e persistência de modelos em JSON.
* **`features/generator/`**: Renderização multithread, imposição N-up e exportação PDF/PNG.
* **`features/spreadsheet/`**: Tabela com suporte a Rich Text, clipboard e delegates de renderização HTML.
* **`features/preview/`**: Painel de pré-visualização dinâmica proporcional.
* **`features/workspace/`**: Janela principal, painel de controles e diálogos de importação/exportação.
* **`shared/`**: Painel de log com persistência em arquivo.

## 🛠️ Instalação e Requisitos

**Dependências de execução:**
```
PySide6 >= 6.5.0
```

**Dependências de build (geração do executável):**
```
Nuitka >= 2.0.0
zstandard >= 0.19.0
```

**Configuração Linux (Fix Teclado BR):**
O sistema já configura automaticamente as variáveis de ambiente necessárias para a compatibilidade do teclado PT-BR no Qt/Linux:
```python
os.environ.setdefault("QT_IM_MODULE", "ibus")
os.environ.setdefault("GTK_IM_MODULE", "ibus")
os.environ.setdefault("XMODIFIERS", "@im=ibus")
```

**Execução:**
```bash
python main.py
```

## 📁 Armazenamento de Dados
Os modelos e logs são armazenados no diretório de dados do usuário, conforme o sistema operacional:

| Sistema | Caminho |
|---|---|
| Linux (nativo) | `~/.local/share/com.leobelisario.ProjetoComSoc/` |
| Linux (Flatpak) | `~/.var/app/com.leobelisario.ProjetoComSoc/data/` |
| Windows | `%APPDATA%\ProjetoComSoc\` |
| macOS | `~/Library/Application Support/com.leobelisario.ProjetoComSoc/` |

## 📝 Fluxo de Trabalho
1. **Modelagem**: Crie ou selecione um modelo no editor visual. Adicione elementos de texto, imagem e assinatura.
2. **Alimentação**: Cole a lista de dados na tabela. O sistema preserva a formatação Rich Text do Excel.
3. **Configuração**: Defina o padrão de nomenclatura dos arquivos e o modo de saída (PNG, PDF avulso, PDF único ou imposição N-up).
4. **Produção**: Clique em "Gerar Material". O sistema processa em paralelo e organiza os arquivos na pasta de destino.

---
*C.O.M.S.O.C. - Autonomia total para a produção de diplomas, prismas, identificações e homenagens com padrão institucional.*