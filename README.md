# Claude + Antigravity — kit global

Instalação pessoal para Windows e macOS, com skills, agentes, workflows, Claude Code nativo, dois perfis e OmniRoute. Não contém contas, chaves, histórico nem configurações de clientes. O clone é a fonte de instalação; depois de instalar, os comandos globais não dependem da pasta do repositório.

## O que é instalado

- `claude`: perfil original em `~/.claude`, login da assinatura Anthropic, Sonnet 5.5 / Opus 5.5.
- `clauderouter`: perfil independente em `~/.claude/profiles/router`, com a equipe gratuita abaixo.
- Suporte dos comandos em `~/.claude/launcher`, compartilhamento em `~/.gemini/config/{skills,agents,global_workflows}`.
- OmniRoute instalado por npm e configurado em `~/.omniroute/.env`, com acesso somente em `127.0.0.1:20128`.

O fluxo Claude usa um pequeno filtro local que chama o OpenRouter diretamente. O OmniRoute fica disponível para outros clientes e seu dashboard; não é um elo obrigatório desse fluxo. Isso preserva o bloqueio de modelos pagos e as reservas exatas. Não prometa que mudar combos do OmniRoute modifica a equipe deste kit.

## Equipe obrigatória

| Função | Principal | Reserva |
|---|---|---|
| Orquestrador | Inkling | Nemotron 3 Ultra |
| Programador principal | Inkling Small | Laguna S 2.1 |
| Especialista visual | Nemotron 3.5 Super VL | Inkling Small |
| Executor rápido | North Mini Code | Laguna XS 2.1 |
| Programador auxiliar | Laguna XS 2.1 | North Mini Code |

São **10 posições, 5 principais e 5 reservas, com 7 modelos distintos**. O seletor `/model` mostra os nomes originais dos sete modelos. `models.json` registra os IDs e as duplas. `router-*` são nomes internos de funções/agentes, não nomes de modelos.

Escolher um modelo principal usa sua reserva por função em falhas elegíveis antes de começar a resposta. Escolher Nemotron Ultra ou Laguna S diretamente mantém esse modelo, sem inventar uma terceira alternativa. North Mini Code, Laguna XS e Inkling Small também aparecem como reservas de outras funções: a função do agente determina essa relação.

O filtro revalida preços, disponibilidade, suporte a ferramentas, imagens e expiração. Só aceita os sete IDs `:free`, bloqueia recursos pagos e nunca manda imagem a modelo sem suporte visual. Zero preço não significa capacidade ou cota ilimitada.

**Disponibilidade conhecida em 18/10/2026:** Inkling e Inkling Small recusaram a conta/rota testada com a restrição “only available on agentic harnesses”; Nemotron Ultra foi a reserva usada. Laguna S também apresentou limite temporário. Ambos Laguna constavam com expiração em 31/10/2026. O instalador não contorna restrições nem substitui os modelos por conta própria. Consulte o catálogo ao instalar; uma dupla pode ficar indisponível.

## Instalar no Windows

Pré-requisitos: Python **3.12+**, Node.js LTS **22.19+**, Git for Windows e acesso à internet. Instale-os pelos sites oficiais ou pelos gerenciadores oficiais do seu sistema. A IA pode verificar e instalar os ausentes antes de continuar. Não use o Python embutido em outro aplicativo.

Na pasta clonada, voce tambem pode abrir INSTALAR.cmd. Pelo terminal:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

O script instala o Claude nativo se estiver ausente e o OmniRoute 3.8.51 se ainda nao houver uma instalacao, aplica o kit e pede sua chave OpenRouter com entrada oculta. A chave é cifrada com DPAPI para o usuário Windows. Reabra o terminal para atualizar o PATH.

Para inspecionar o plano sem instalar:

```powershell
python install.py --dry-run
```

## Instalar no macOS

Pré-requisitos: Python **3.12+**, Node.js LTS **22.19+** e internet. Com Homebrew já instalado, você pode usar `brew install python@3.12 node@22 git`; siga as instruções do Homebrew para disponibilizar os executáveis no PATH. Também pode usar os instaladores oficiais. O kit não exige nem solicita privilégios de administrador por conta própria.

```bash
bash install.sh
```

O script instala o Claude nativo se necessario, o OmniRoute 3.8.51 se ausente e o kit global; preserva uma instalacao OmniRoute existente. O macOS guarda a chave no **Keychain**, com uma referência local no perfil. Autorize o acesso quando o sistema pedir. Não existe fallback para gravar a chave em texto puro. O PATH é configurado em `~/.zshrc`; reabra o terminal. Se usar outra shell, adicione `~/.claude/launcher/bin` ao início do PATH dela.

## Concluir as contas em cada computador

1. Faça login da assinatura pelo Claude nativo: `~/.local/bin/claude` (no Windows, `~/.local/bin/claude.exe`), usando `/login`. Não transporte `.credentials.json` nem histórico entre máquinas por este repositório.
2. A chave OpenRouter é solicitada localmente pelo instalador. Para adiá-la, use `-SkipKey` no Windows ou `--skip-key` no macOS. Depois execute `python ~/.claude/launcher/runtime/replace_key.py` com seu Python instalado.
3. Execute `omniroute serve --no-open` e abra <http://127.0.0.1:20128/dashboard/providers/openrouter>. Conclua o primeiro acesso/login do OmniRoute e adicione sua conexão OpenRouter pelo formulário. A conexão do OmniRoute é separada da credencial protegida do perfil Claude. Uma IA com navegador pode ajudar, mas deve manter segredos fora de prompts, prints, logs e argumentos de comandos. O kit não escreve diretamente no banco nem contorna o login de administração.
4. Abra `clauderouter`, use `/model` e confira os sete nomes. Execute `clauderouter --listar-modelos` para conferir IDs e reservas sem geração.

Nenhum serviço inicia automaticamente com o Windows ou macOS. OmniRoute não precisa permanecer aberto para os dois comandos Claude. Não importe tokens deste computador para outro.

## Continuidade e orquestração

O original mantém a triagem Sonnet/Opus e os agentes especialistas do kit. O router usa os cinco agentes de função e a tabela obrigatória; omite `model` e `effort` na chamada Agent e usa o modelo definido no frontmatter. As políticas são separadas.

Ao reconhecer esgotamento da assinatura, o lançador transfere o trabalho para o router **somente quando verifica que a sessão está ociosa e sem processos descendentes**. Não troca por qualquer 429, erro de login ou indisponibilidade de rede. Processos destacados e estado desconhecido bloqueiam encerramento forçado. A continuidade contém texto selecionado, com remoção de credenciais reconhecíveis, e não uma reprodução integral da sessão. O retorno à assinatura é manual. A mudança de provedor envia o contexto selecionado ao OpenRouter; use projetos compatíveis com as condições dos provedores gratuitos.

`CONTINUIDADE.md` no projeto deve registrar objetivo, estado, testes e operações incertas. Nunca repita publicações, mensagens ou pagamentos apenas porque houve retomada. Se não houver tempo/cota para terminar, entregue esse registro e a próxima ação concreta.

## Skills, agentes e workflows

O conteúdo reutilizável veio do kit fornecido pelo proprietário, removendo referências pessoais, projetos, MCP e settings específicos. Memória Obsidian é opcional e desativada por padrão. Os agentes Antigravity são personas Markdown; não são garantia de subagentes nativos.

Workflows legados também são fornecidos como skills `workflow-*`: no Antigravity, use `/workflow-create`, `/workflow-plan`, `/workflow-debug`, etc. Isso atende à migração oficial de workflows para skills. No Claude, os comandos legados `/create`, `/plan`, `/debug`, etc. permanecem em `~/.claude/commands`. O conteúdo de ambos deriva do mesmo bundle.

O instalador mescla arquivos individualmente, preserva arquivos não relacionados, verifica links existentes e mantém backups privados em `~/.claude/launcher/backups`. Reinstalar atualiza os arquivos do kit; suas edições nesses mesmos arquivos são arquivadas antes. Históricos e credenciais nunca entram no bundle.

## Verificação, reversão e publicação

```bash
python scripts/audit_public.py
python -m unittest discover -s tests -v
python runtime/test_profiles.py
```

Os testes de roteamento usam servidor simulado e não geram cobranças. CI roda Windows e macOS. A validação inicial deste repositório foi feita no Windows; macOS precisa passar no runner e em teste real de Keychain/Claude antes de ser declarado validado de ponta a ponta.

Para reverter a última instalação: `python ~/.claude/launcher/runtime/rollback.py`. A reversão recusa sobrescrever edições posteriores, preserva diretórios, links e credenciais, e não desinstala Python/Node/Claude/OmniRoute. Registros anteriores ficam em cada backup. Caso haja interrupção, leia `installation.json` e o backup correspondente; não execute uma reinstalação cega.

Antes de publicar, execute a auditoria. Publique **somente este repositório**, nunca `.claude`, `.gemini`, `.omniroute`, backups, logs ou pastas de clientes. O `.gitignore` e a auditoria são proteções complementares, não substituem revisar o diff. Este repositório não possui remoto configurado e não publica nada automaticamente.

## Fontes

- [Instalação oficial do Claude](https://code.claude.com/docs/en/setup)
- [Seletor e nomes de modelos](https://code.claude.com/docs/en/settings-reference#modelpicker)
- [Modelos e perfis](https://code.claude.com/docs/en/model-config)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [OmniRoute](https://github.com/diegosouzapw/OmniRoute)
- [Integração OpenRouter/Claude Code](https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration)
- [Migração de workflows do Antigravity](https://antigravity.google/docs/migration/workflows-to-skills)

Veja `docs/PROMPT-INSTALACAO.md` para pedir a instalação a uma IA e `THIRD_PARTY_NOTICES.md` para a origem dos conteúdos reutilizados.

## Contexto e compactacao por modelo

O catalogo oficial consultado em 18/10/2026 esta registrado em models.json, incluindo contexto e resposta maxima por modelo. Ao abrir o router, o lancador recalcula a configuracao com metadados atuais. O gateway revalida metadados periodicamente e limita a resposta ao valor compativel com os candidatos disponiveis. Se uma janela diminuir durante a sessao, bloqueia a chamada e pede reinicializacao para recalcular a compactacao, sem mandar contexto para uma reserva menor.

| Modelo | Contexto publicado | Compactacao configurada |
|---|---:|---:|
| Inkling | 1048576 | 918080 |
| Inkling Small | 1048576 | 212992 |
| Nemotron 3.5 Super VL | 1000000 | 918080 |
| North Mini Code | 256000 | 206848 |
| Laguna XS 2.1 | 262144 | 206848 |
| Nemotron 3 Ultra | 1000000 | 918080 |
| Laguna S 2.1 | 262144 | 206848 |

A compactacao reserva espaco para a resposta e uma margem adicional de 16384 tokens. Inkling Small compacta antes para preservar a reserva Laguna S, cuja janela e menor. O mesmo criterio considera North Mini Code na dupla de codigo auxiliar. Imagens e diferentes tokenizadores podem causar diferencas de contagem; os limites do provedor continuam soberanos.

Limite do Claude Code: modelSettings.autoCompactWindow permite compactacao individual, mas nao existe um campo oficial arbitrario de janela por modelo para esses IDs externos. Por isso modelos com pelo menos 1000000 usam o sufixo oficial [1m] (removido antes da chamada OpenRouter). Os menores usam a janela nativa conservadora de 256000, o menor tamanho desse grupo; Laguna S/XS deixam de aproveitar 6144 tokens da capacidade publicada. Nao foram falsificadas identidades Claude por behavesAs ou modelOverrides, nem desativada a compactacao. O antigo teto global de 200000 foi removido.

A configuracao e isolada do perfil Anthropic original. `clauderouter --listar-modelos` mostra os limites registrados e as reservas sem gerar resposta. Reabra clauderouter para carregar a configuracao nova. A CI e os testes locais usam provedores simulados; a verificacao visual interativa permanece dependente de autorizacao de confianca na pasta e nao foi contornada.

Fontes: https://openrouter.ai/api/v1/models e https://code.claude.com/docs/en/model-config#correct-the-window-for-a-gateway-or-custom-model-id e https://code.claude.com/docs/en/settings-reference#modelsettings
