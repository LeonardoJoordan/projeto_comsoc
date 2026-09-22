# W4 — proteção, persistência e operação offline

Data: 22/09/2026. Execução autorizada após impedimento de W3.

## Resultado

**128 testes aprovados, 2 pulados, zero falhas, em 35,01 s.**
Executado no Windows com `.venv-windows`, Qt offscreen e armazenamento
descartável isolado pelo `conftest.py`. Não constitui inspeção visual.

```powershell
.\.venv-windows\Scripts\python.exe tools/validate_windows_w4.py
```

Evidências locais: `build/security/windows-w4-tests.xml` e
`build/security/windows-w4-network.json`.

Cobertura executada:

- Arquivos somente leitura e abertos por processo independente, nomes com
  espaços/acentos, preservação do original e nova tentativa após liberar o arquivo.
- Falhas de gravação/publicação, destino concorrente, backups, migração retomável,
  recuperação criptografada e troca de senha sem manter backup com senha anterior.
- Processo filho encerrado por `os._exit(17)` após editar documento protegido:
  recuperação reaberta, perfil comparado aos hashes anteriores ao documento e
  ausência de imagens ou conteúdo sensível em claro nos artefatos examinados.
- Importação/exportação protegida, senha incorreta, troca da senha de transporte
  por senha local, sessões, expiração, cancelamento e descarte de dados de prévia.
- Sanitização e rotação de logs; limpeza limitada à área temporária do aplicativo.
- Geração autorizada PNG e, nesta etapa, cobertura ampliada para PDF individual
  e agrupado: PDF abre sem criptografia e possui uma página; PNG corresponde à
  imagem esperada. Recursos protegidos são liberados e a biblioteca permanece
  sem artefatos em claro. Não houve inspeção visual do conteúdo PDF.

## Offline e limites

O iniciador bloqueia e registra eventos Python `socket.connect`,
`socket.getaddrinfo` e `socket.sendto`. A execução terminou com **zero eventos
detectados**. Isso não intercepta bibliotecas nativas nem processos filhos e
**não equivale a desligar a conexão ou monitorar todo o tráfego no SO**.
Não foram alteradas configurações de rede/segurança do usuário.

O volume C: foi confirmado como NTFS por `System.IO.DriveInfo.DriveFormat`.
`Get-Volume` não pôde consultar o volume por falta de acesso; o método somente
leitura alternativo confirmou o formato. FAT/exFAT e compartilhamentos de rede
não foram testados e não recebem promessa de suporte.

Dois testes de limpeza com links simbólicos foram pulados pela falta de
privilégio Windows (1314); os cenários sem links foram executados.
Não há promessa de apagamento físico de RAM, swap ou disco.

## Estado e próxima retomada

W4 tem **validação automatizada aprovada, aceite completo pendente** do ensaio
real sem conexão e das inspeções de ciclo de uso nativo ligadas a W3.
Nenhuma falha de produto foi encontrada nesta rodada; foram ampliados testes
e criado um iniciador reproduzível. W3 continua pendente, não implicitamente
aprovada pelo avanço autorizado. Próximo checkpoint sequencial: W5 (build),
mantendo essas pendências para a aprovação final. Nenhum novo binário ou
instalador foi produzido nesta etapa.
