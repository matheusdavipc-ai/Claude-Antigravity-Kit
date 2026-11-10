# Claude + Antigravity — kit global

Instalação pessoal para Windows e macOS: skills, agentes e workflows compartilhados entre o Claude Code nativo e o Antigravity, mais as regras de orquestração do Claude Code. Não contém contas, chaves, histórico nem configurações de clientes. O clone é a fonte de instalação; depois de instalar, nada depende da pasta do repositório.

**Acesso rápido:** [prompt Windows](#prompt-de-instalação--windows) · [prompt macOS](#prompt-de-instalação--macos) · [catálogo de uso de todos os recursos](docs/CATALOGO.md) · [instalação manual](#instalar-no-windows) · [remover o router de uma instalação antiga](#remover-o-router-de-uma-instalação-antiga).

## Instalar pedindo a uma IA

Escolha **somente o prompt do seu sistema** e copie o bloco inteiro para o Claude Code, Antigravity ou outra IA com acesso ao terminal e aos arquivos do computador. Ela instala e verifica o kit; você faz o login da assinatura Anthropic. Assinaturas e cotas não acompanham o repositório.

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

Prefere instalar pelo terminal? Veja [Windows](#instalar-no-windows) ou [macOS](#instalar-no-macos). Para escolher e usar os recursos depois, abra o [catálogo completo de skills, agentes e workflows](docs/CATALOGO.md).

## O que é instalado

- `claude`: o Claude Code nativo de `~/.local/bin`, com o perfil em `~/.claude` e o login da assinatura Anthropic. O seletor `/model` lista Opus 5.5 (padrão quando nenhum modelo válido está salvo), Sonnet 5.5, Haiku 5.5 e Fable 5.1, com resolução nativa.
- `~/.claude/CLAUDE.md`: um bloco gerenciado com a triagem de modelo e esforço, o roteamento para os 17 agentes e as regras de perguntas. O resto do arquivo é seu e não é alterado.
- Skills, agentes e workflows em `~/.gemini/config/{skills,agents,global_workflows}`, expostos em `~/.claude/skills`, `~/.claude/agents` e `~/.claude/commands`.
- `~/.claude/launcher`: só o registro da instalação (`installation.json`), os backups e o `runtime/rollback.py`. Nenhum processo fica entre você e o Claude Code.

No `~/.claude/settings.json`, o instalador mexe apenas em `model` (só quando ausente ou inválido), `availableModels`, `ANTHROPIC_DEFAULT_OPUS_MODEL` e `ANTHROPIC_DEFAULT_SONNET_MODEL`. Também remove sobreposições antigas que atrapalham a assinatura (`ANTHROPIC_BASE_URL`, chaves de API, Haiku remapeado para Sonnet e qualquer override de Fable). Permissões, plugins, tema e hooks seus ficam como estão.

## Política de modelos

| Nível | Tarefas típicas | Modelo | Esforço |
|---|---|---|---|
| 0 | leitura, busca, resumo | haiku | low |
| 1 | comando conhecido, ajuste trivial | sonnet | low |
| 2 | mudança simples em um arquivo | sonnet | medium |
| 3 | 2 a 4 arquivos seguindo um padrão | sonnet | high |
| 4 | tarefa difícil, decisão de arquitetura, dados sensíveis | opus | high |
| 5 | produção, migração real, auditoria de segurança | opus | xhigh |

Fable entra só quando você pede ou quando Opus em `xhigh` já falhou na mesma tarefa. Haiku nunca edita arquivos nem decide. A tabela completa e as regras de desempate estão no `templates/CLAUDE.md`.

## Instalar no Windows

Pré-requisitos: Python **3.12+**, Git for Windows e acesso à internet. Instale-os pelos sites oficiais ou pelos gerenciadores oficiais do seu sistema. Não use o Python embutido em outro aplicativo.

Na pasta clonada, você também pode abrir `INSTALAR.cmd`. Pelo terminal:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

O script instala o Claude nativo se estiver ausente e aplica o kit. Ele coloca `%USERPROFILE%\.local\bin` no início do PATH do usuário e tira de lá o `launcher\bin` de versões antigas. Reabra o terminal para o PATH novo valer.

Para inspecionar o plano sem instalar:

```powershell
python install.py --dry-run
```

## Instalar no macOS

Pré-requisitos: Python **3.12+** e internet. Com Homebrew já instalado, você pode usar `brew install python@3.12 git`; também pode usar os instaladores oficiais. O kit não pede privilégios de administrador.

```bash
bash install.sh
```

O script instala o Claude nativo se necessário e aplica o kit. O PATH é configurado num bloco do `~/.zshrc` que põe `~/.local/bin` na frente; reabra o terminal. Se usar outra shell, adicione `~/.local/bin` ao início do PATH dela.

## Login

Abra `claude` e use `/login` com a sua assinatura. Não transporte `.credentials.json` nem histórico entre máquinas por este repositório. `claude auth status` mostra o método de login sem exibir tokens.

## Remover o router de uma instalação antiga

Até 06/11/2026 o kit também instalava um segundo perfil (`clauderouter`), um filtro local de modelos gratuitos, o OmniRoute e um supervisor que passava o `claude` por um script Python com 9 hooks. Tudo isso saiu. O instalador atual já tira os hooks do supervisor do `settings.json` e o `launcher\bin` do PATH, com backup e journal. Os arquivos que ficaram no disco saem com:

```text
python scripts/remove_router.py --dry-run    (lista, não muda nada)
python scripts/remove_router.py --aplicar    (move para a quarentena)
```

- Rode `--aplicar` **fora do Claude Code**, com todas as sessões `claude` e `clauderouter` fechadas, depois de reinstalar o kit e reabrir o terminal. O script recusa enquanto encontrar sessões do launcher, hooks do launcher no `settings.json` ou o `launcher\bin` no PATH.
- Nada é apagado. Cada item vai para `~/.claude/launcher/backups/remocao-router-<data>/quarentena/`, com hashes num `journal.json`. Primeiro saem os arquivos do router, por último o `hook.py`, o `launcher.py` e o `launcher\bin`. Junctions saem como link, sem entrar na pasta de destino.
- Para desfazer: `python scripts/remove_router.py --restaurar <journal.json>`. A restauração confere tudo antes e recusa se algum destino já existir ou se a quarentena tiver mudado.
- O script não toca em `~/.omniroute`, nas chaves OpenRouter, no `settings.json` nem no resto do perfil. Para tirar o OmniRoute depois: `omniroute stop`, `npm uninstall -g omniroute`, apagar `~/.omniroute` e revogar as chaves em <https://openrouter.ai/settings/keys>.

## Skills, agentes e workflows

O [catálogo completo](docs/CATALOGO.md) explica **cada recurso**, quando usar e como invocar, com exemplos e links para suas instruções.

| Conteúdo | O que você encontra no catálogo |
|---|---|
| 30 skills de conhecimento e coordenação | Finalidade e exemplo de uso de cada skill; inclui a skill mestre orchestration-kit. |
| 11 skills de workflow | Procedimentos de planejamento, criação, investigação, publicação e outros objetivos. Somadas às 30 acima, são 41 skills. |
| 17 agentes especialistas | Qual especialista escolher no Claude Code e como aplicar a persona no Antigravity. |
| Recursos internos | As 23 operações do Impeccable e os 13 templates do app-builder, com indicação de uso. |

Exemplos no Claude Code:

```text
/workflow-plan Planeje uma área de login; não implemente ainda.
/api-patterns Defina a API de pedidos com paginação e erros consistentes.
/impeccable audit Revise a acessibilidade e a responsividade desta tela.
Use o agente test-engineer para verificar os casos de borda desta regra.
```

No Antigravity, selecione `/nome-da-skill` ou peça que aplique seu conhecimento. Os agentes distribuídos são personas Markdown: peça a leitura do arquivo correspondente em `~/.gemini/config/agents/`. Isso não garante a criação de um subagente nativo.

Prefira `/workflow-create`, `/workflow-plan`, `/workflow-debug` e os demais nomes `workflow-*` nas duas ferramentas. Os comandos Claude legados continuam em `~/.claude/commands`, mas alguns nomes, como `/status`, `/debug` e `/plan`, podem coincidir com comandos nativos. Os workflows convertidos atendem à migração oficial do Antigravity para skills.

O conteúdo foi generalizado a partir do kit fornecido pelo proprietário, removendo referências pessoais, projetos, MCP e settings específicos. Memória Obsidian é opcional e desativada por padrão. Skills e agentes usam a cota do modelo ativo; não incluem novas contas ou créditos.

O instalador mescla arquivos individualmente, preserva arquivos não relacionados, verifica links existentes e mantém backups privados em `~/.claude/launcher/backups`. Reinstalar atualiza os arquivos do kit; suas edições nesses mesmos arquivos são arquivadas antes. Históricos e credenciais nunca entram no bundle.

## Verificação, reversão e publicação

```bash
python scripts/audit_public.py
python -m unittest discover -s tests -v
python install.py --dry-run
```

Os testes usam pastas temporárias e não fazem chamadas a modelos. A CI roda no Windows e no macOS; isso valida as suítes automatizadas, não o login interativo num Mac. Veja os detalhes e limites em [Validação](docs/VALIDACAO.md).

Para reverter a última instalação: `python ~/.claude/launcher/runtime/rollback.py`. A reversão recusa sobrescrever edições posteriores, preserva diretórios, links e credenciais, devolve o PATH anterior e não desinstala Python nem Claude. Registros anteriores ficam em cada backup. Caso haja interrupção, leia `installation.json` e o backup correspondente; não execute uma reinstalação cega.

Antes de publicar, execute a auditoria. Publique **somente este repositório**, nunca `.claude`, `.gemini`, backups, logs ou pastas de clientes. O `.gitignore` e a auditoria são proteções complementares, não substituem revisar o diff. Os instaladores não publicam arquivos automaticamente.

## Fontes

- [Instalação oficial do Claude](https://code.claude.com/docs/en/setup)
- [Seletor e nomes de modelos](https://code.claude.com/docs/en/settings-reference#modelpicker)
- [Modelos e perfis](https://code.claude.com/docs/en/model-config)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Migração de workflows do Antigravity](https://antigravity.google/docs/migration/workflows-to-skills)

Os prompts acima também estão em [Prompts de instalação](docs/PROMPT-INSTALACAO.md). Veja o [catálogo de uso](docs/CATALOGO.md) e os [avisos de terceiros](THIRD_PARTY_NOTICES.md) para conhecer os recursos e sua origem.
