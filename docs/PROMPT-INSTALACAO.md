# Prompts de instalação com uma IA

Estas são as mesmas instruções publicadas no início do [README](../README.md). Copie somente o bloco do seu sistema para uma IA com acesso local ao terminal e aos arquivos. Ela instala e verifica o kit; você faz o login da assinatura Anthropic. Para conhecer cada recurso, consulte o [catálogo de uso](CATALOGO.md).

### Prompt de instalação — Windows

```text
Instale globalmente o Claude-Antigravity-Kit neste computador Windows. Estou autorizando a instalação do kit e das dependências necessárias, preservando meus dados.

Repositório: https://github.com/matheusdavipc-ai/Claude-Antigravity-Kit.git
Clone-o em uma pasta do meu usuário, ou reutilize um clone existente depois de conferir origem e alterações locais. Não sobrescreva trabalho existente.

Verifique Git for Windows, Python 3.12+ e Claude Code nativo 2.1.292+. Na pasta do clone, execute primeiro:
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
Depois, execute:
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
O instalador instala o Claude nativo se ele estiver ausente. Verifique a versão do Claude existente antes de prosseguir. Não execute tudo como administrador nem desative proteções globalmente.

Use %USERPROFILE%\.claude para a configuração do Claude Code e %USERPROFILE%\.claude\launcher para o registro da instalação e os backups; compartilhe o bundle em %USERPROFILE%\.gemini\config. O comando claude deve abrir o Claude Code nativo de %USERPROFILE%\.local\bin. Ajude no login Anthropic pelo fluxo nativo (/login), sem copiar credenciais. Reabra o terminal e confira o PATH e o comando claude.

Leia README.md, AGENTS.md e docs/CATALOGO.md antes de alterar arquivos. Primeiro faça a auditoria e o dry-run; depois execute a instalação e as verificações. Preserve configurações existentes, use os backups e a reversão do instalador e não copie perfis privados para o clone. Instale dependências ausentes por fontes oficiais, sem usar runtimes embutidos em outros aplicativos.

Instale todas as skills, agentes e workflows do bundle; use /workflow-* para evitar conflitos com comandos nativos. Mantenha a política do CLAUDE.md: Haiku para leitura, Sonnet e Opus para o trabalho, com esforço por nível, e Fable só sob pedido. Memória pessoal permanece desativada.

Se houver uma instalação antiga com o perfil router (comando clauderouter), rode python scripts\remove_router.py --dry-run e me mostre a lista. Só rode --aplicar com a minha autorização, num PowerShell fora do Claude e com todas as sessões fechadas.

Execute a auditoria pública, os testes do repositório e claude --version. Distinga testes simulados de login real. Peça autorização antes de testes que consumam cota.

Entregue os locais finais, comandos de uso, resultados, limitações e reversão. Se a cota, o contexto ou o tempo estiverem acabando, salve CONTINUIDADE.md sem segredos: objetivo, arquivos alterados, backups, etapas e testes concluídos, pendências, operações incertas e próxima ação. Não declare concluído o que não foi verificado.
```

### Prompt de instalação — macOS

```text
Instale globalmente o Claude-Antigravity-Kit neste Mac. Estou autorizando a instalação do kit e das dependências necessárias, preservando meus dados.

Repositório: https://github.com/matheusdavipc-ai/Claude-Antigravity-Kit.git
Clone-o em uma pasta do meu usuário, ou reutilize um clone existente depois de conferir origem e alterações locais. Não sobrescreva trabalho existente.

Verifique Git, Python 3.12+ e Claude Code nativo 2.1.292+. Use Homebrew se já estiver disponível ou os instaladores oficiais. Não instale Homebrew silenciosamente nem use sudo para corrigir permissões. Na pasta do clone, execute primeiro:
bash install.sh --dry-run
Depois, execute:
bash install.sh
O instalador instala o Claude nativo se ele estiver ausente. Verifique a versão do Claude existente antes de prosseguir. Se python3 não apontar para Python 3.12+, selecione o executável correto por CLAUDE_KIT_PYTHON.

Use ~/.claude para a configuração do Claude Code e ~/.claude/launcher para o registro da instalação e os backups; compartilhe o bundle em ~/.gemini/config. O comando claude deve abrir o Claude Code nativo de ~/.local/bin; o instalador coloca essa pasta no início do PATH em ~/.zshrc. Se eu usar outra shell, adapte o PATH dela. Ajude no login Anthropic pelo fluxo nativo (/login), sem copiar credenciais de outro computador. Reabra o terminal e confira o comando claude.

Leia README.md, AGENTS.md e docs/CATALOGO.md antes de alterar arquivos. Primeiro faça a auditoria e o dry-run; depois execute a instalação e as verificações. Preserve configurações existentes, use os backups e a reversão do instalador e não copie perfis privados para o clone. Instale dependências ausentes por fontes oficiais, sem usar runtimes embutidos em outros aplicativos.

Instale todas as skills, agentes e workflows do bundle; use /workflow-* para evitar conflitos com comandos nativos. Mantenha a política do CLAUDE.md: Haiku para leitura, Sonnet e Opus para o trabalho, com esforço por nível, e Fable só sob pedido. Memória pessoal permanece desativada.

Se houver uma instalação antiga com o perfil router (comando clauderouter), rode python3 scripts/remove_router.py --dry-run e me mostre a lista. Só rode --aplicar com a minha autorização, num terminal fora do Claude e com todas as sessões fechadas.

Execute a auditoria pública, os testes do repositório e claude --version. Distinga testes simulados de login real. Peça autorização antes de testes que consumam cota.

Entregue os locais finais, comandos de uso, resultados, limitações e reversão. Se a cota, o contexto ou o tempo estiverem acabando, salve CONTINUIDADE.md sem segredos: objetivo, arquivos alterados, backups, etapas e testes concluídos, pendências, operações incertas e próxima ação. Não declare concluído o que não foi verificado.
```

Prefere instalar pelo terminal? Veja [Windows](../README.md#instalar-no-windows) ou [macOS](../README.md#instalar-no-macos).
