# Licenças e avisos de terceiros

Este arquivo descreve os componentes identificados na compilação Windows do FORNAX Forge. O inventário deve ser refeito sempre que as dependências ou o ambiente de compilação mudarem.

## Componentes distribuídos

| Componente | Versão esperada | Licença/modalidade | Observação de distribuição |
|---|---:|---|---|
| Qt for Python (PySide6, Essentials, Addons e Shiboken6) | 6.11.0 | LGPL-3.0-only, GPL ou comercial | Este projeto adota a opção LGPL v3 para o pacote comunitário. As DLLs permanecem separadas e substituíveis. |
| Qt 6 (Core, Gui, Widgets, Network, Svg, Pdf e plugins) | 6.11.0 | LGPL-3.0-only/GPL ou comercial, mais licenças de terceiros do Qt | Preservar os avisos dos módulos e plugins efetivamente empacotados. |
| Python | 3.13 | Python Software Foundation License | O runtime e módulos da biblioteca padrão acompanham o executável. |
| pypdf | 6.14.2 fixado | BSD-3-Clause | A versão do pacote deve coincidir com `requirements.txt`; refaça o build em ambiente limpo. |
| cryptography | 50.0.1 fixado | Apache-2.0 ou BSD-3-Clause | Fornece Argon2id e AES-256-GCM para os modelos protegidos; preservar os avisos distribuídos pelo pacote. |
| cffi / pycparser | conforme resolução da versão fixada | MIT / BSD-3-Clause | Dependências transitivas de `cryptography`; registrar versões e hashes usados no build final. |
| OpenSSL | 3.x | Apache-2.0 | `libcrypto-3.dll` e `libssl-3.dll` foram encontrados no pacote. |
| libffi | 8.x | MIT | `libffi-8.dll` foi encontrado no pacote. |
| SQLite | incorporado ao Python | Public domain/blessing | `sqlite3.dll` e `_sqlite3.pyd` foram encontrados no pacote. |
| Microsoft Visual C++ Runtime | 14.x | Microsoft Visual Studio redistributable terms | Redistribuir apenas arquivos autorizados por uma instalação/licença válida das ferramentas Microsoft. |
| Inter | arquivos incluídos | SIL Open Font License 1.1 | Texto integral em `assets/fonts/ui/OFL.txt`. |

Nuitka e zstandard são ferramentas de construção e não foram identificados como módulos autônomos no diretório final. Suas licenças não se transferem automaticamente ao aplicativo só por terem sido usadas no build; se algum artefato deles passar a ser empacotado, o inventário deve ser atualizado.

## Condições práticas da LGPL v3 para Qt/PySide6

- manter as bibliotecas Qt/PySide6 separadas do executável e não bloquear sua substituição por versões compatíveis modificadas;
- entregar os textos da GNU GPL v3 e GNU LGPL v3, avisos de autoria e licenças de terceiros correspondentes aos binários Qt distribuídos;
- informar que o usuário pode obter, modificar e substituir os componentes cobertos;
- disponibilizar o código-fonte correspondente da versão exata das bibliotecas LGPL distribuídas, por meio válido e pelo período exigido pela licença, ou acompanhar os binários com o material aplicável;
- não aplicar EULA, DRM ou outra restrição que retire os direitos concedidos pela LGPL;
- se o distribuidor usar Qt comercial, substituir esta declaração pelos termos e artefatos comerciais corretos. Pacotes comunitários instalados pelo PyPI não devem ser apresentados como Qt comercial.

Para máxima reprodutibilidade, registre os hashes dos wheels usados no release e arquive o código-fonte correspondente à versão exata juntamente com os artefatos da versão.

## Substituição das bibliotecas Qt

Feche o FORNAX Forge, faça backup da pasta de instalação e substitua somente DLLs/módulos Qt e PySide6 por uma compilação ABI-compatível. A LGPL não obriga o autor do aplicativo a garantir compatibilidade nem a prestar suporte à versão modificada. O instalador não impede essa substituição.

## Fontes e referências oficiais

- Qt for Python: https://doc.qt.io/qtforpython-6/
- Licenças do Qt for Python: https://doc.qt.io/qtforpython-6/licenses.html
- GNU LGPL v3: https://www.gnu.org/licenses/lgpl-3.0.html
- GNU GPL v3: https://www.gnu.org/licenses/gpl-3.0.html
- Código-fonte Qt: https://download.qt.io/official_releases/QtForPython/
- Licença Python: https://docs.python.org/3/license.html
- Licença OpenSSL: https://www.openssl.org/source/license.html
- pypdf: https://github.com/py-pdf/pypdf
- cryptography: https://cryptography.io/en/latest/about/license/
- Inter: https://github.com/rsms/inter

## Verificação antes de publicar

1. Crie um ambiente virtual limpo e instale exatamente `requirements.txt`.
2. Execute `python script_nuitka.py` e confira `build/main.dist`.
3. Compare a lista de DLLs e módulos com esta tabela; resolva qualquer item sem licença identificada.
4. Inclua no instalador os textos integrais da GNU GPL v3, GNU LGPL v3, PSF, Apache 2.0, BSD-3-Clause, MIT, OFL 1.1 e os avisos do Qt aplicáveis ao pacote exato.
5. Arquive requisitos, hashes, fontes correspondentes e o instalador na mesma versão do release.
6. Compile `instalador.iss`, instale em uma máquina limpa e confirme que a pasta `licenses` está presente.

Este inventário auxilia a conformidade técnica, mas não é parecer jurídico. Titularidade do código, contribuições, marcas e contratos comerciais devem ser validados pelo responsável pela distribuição.
