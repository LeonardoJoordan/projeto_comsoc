# Projeto ComSoc
Construtor Otimizado para Material Social Oficial e Cerimonial.

Sistema desktop modularizado construído em Python e PySide6 para criação de templates visuais, mesclagem de dados ricos e geração de documentos em lote (com suporte a imposição em A4 e impressão direta).

## Estrutura do Projeto
A arquitetura adota o padrão **Vertical Slicing** (Orientada a Features), garantindo baixo acoplamento e alta coesão:
- `core/`: Lógica agnóstica de negócio e utilitários de sistema.
- `features/`: Domínios isolados da aplicação (`workspace`, `editor`, `generator`, `spreadsheet`, `preview`).
- `shared/`: Componentes genéricos de UI.

## Instalação (Desenvolvimento)
1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   # No Windows: venv\Scripts\activate
   # No Linux/Mac: source venv/bin/activate