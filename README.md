# Claude + Antigravity — kit global

Instalação pessoal para Windows e macOS, com skills, agentes, workflows, Claude Code nativo, dois perfis e OmniRoute. Não contém contas, chaves, histórico nem configurações de clientes. O clone é a fonte de instalação; depois de instalar, os comandos globais não dependem da pasta do repositório.

**Acesso rápido:** [prompt Windows](#prompt-de-instalação--windows) · [prompt macOS](#prompt-de-instalação--macos) · [catálogo de uso de todos os recursos](docs/CATALOGO.md) · [instalação manual](#instalar-no-windows).

## Instalar pedindo a uma IA

Escolha **somente o prompt do seu sistema** e copie o bloco inteiro para o Claude Code, Antigravity ou outra IA com acesso ao terminal e aos arquivos do computador. Ela poderá instalar e verificar o kit; você conclui os logins e digita sua própria chave OpenRouter localmente. Assinaturas e cotas não acompanham o repositório.

### Prompt de instalação — Windows

```text
Instale globalmente o Claude-Antigravity-Kit neste computador Windows. Estou autorizando a instalação do kit e das dependências necessárias, preservando meus dados.

Repositório: https://github.com/matheusdavipc-ai/Claude-Antigravity-Kit.git
Clone-o em uma pasta do meu usuário, ou reutilize um clone existente depois de conferir origem e alterações locais. Não sobrescreva trabalho existente.

Verifique Git for Windows, Python 3.12+, Node.js LTS 22.19+ e Claude Code nativo 2.1.292+. Na pasta do clone, execute primeiro:
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
Depois, execute:
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
O instalador instala Claude nativo e OmniRoute se ausentes. Verifique a versão do Claude existente antes de prosseguir. Não execute tudo como administrador nem desative proteções globalmente.

Use %USERPROFILE%\.claude, %USERPROFILE%\.claude\profiles\router e %USERPROFILE%\.claude\launcher para os perfis e suporte; compartilhe o bundle em %USERPROFILE%\.gemini\config. A chave OpenRouter deve ser digitada por mim em entrada local oculta e protegida com DPAPI. Nunca solicite a chave no chat nem a coloque em argumentos, logs ou prints. Se seu terminal não permitir entrada oculta, use -SkipKey e me oriente a executar localmente replace_key.py do runtime. Ajude no login Anthropic pelo fluxo nativo, sem copiar credenciais. Reabra o terminal e confira o PATH e os dois comandos.

Leia README.md, AGENTS.md, models.json e docs/CATALOGO.md antes de alterar arquivos. Primeiro faça a auditoria e o dry-run; depois execute a instalação e as verificações. Preserve configurações existentes, use os backups e a reversão do instalador e não copie perfis privados para o clone. Instale dependências ausentes por fontes oficiais, sem usar runtimes embutidos em outros aplicativos.

Configure claude para a assinatura Anthropic original e clauderouter para OpenRouter, em perfis separados. A instalação global deve funcionar sem depender da pasta clonada. Instale todas as skills, agentes e workflows do bundle; use /workflow-* para evitar conflitos com comandos nativos. Memória pessoal permanece desativada.

Respeite exatamente as funções e duplas de models.json:
- Orquestrador: Inkling → Nemotron 3 Ultra.
- Programador principal: Inkling Small → Laguna S 2.1.
- Especialista visual: Nemotron 3.5 Super VL → Inkling Small.
- Executor rápido: North Mini Code → Laguna XS 2.1.
- Programador auxiliar: Laguna XS 2.1 → North Mini Code.
São sete modelos distintos em dez posições. Preserve os nomes originais e descrições de função em /model, os limites de contexto por modelo e as regras de compactação. Não acrescente modelos pagos ou terceiros. Revalide metadados e informe restrições, expiração ou indisponibilidade; não invente substitutos.

Mantenha as políticas de orquestração separadas: Sonnet/Opus e esforço no claude original; os cinco agentes próprios e as duplas acima no router. Preserve a troca automática por esgotamento reconhecido somente em estado ocioso verificado e sem processos auxiliares; o retorno é manual.

Configure o OmniRoute em ~/.omniroute/.env, escutando em 127.0.0.1:20128, preservando chaves de criptografia existentes. O filtro do kit chama OpenRouter diretamente; OmniRoute não é obrigatório para abrir claude ou clauderouter. Se necessário, inicie omniroute serve --no-open e ajude no primeiro acesso e na conexão OpenRouter pelo dashboard http://127.0.0.1:20128/dashboard/providers/openrouter. Essa conexão é separada da chave protegida do router. Use autenticação legítima; não altere o banco diretamente. Não crie início automático do sistema.

Execute a auditoria pública, os testes do repositório e do runtime, o diagnóstico nativo sem geração, a listagem clauderouter --listar-modelos e a verificação de isolamento dos perfis. Se iniciar OmniRoute, confira saúde HTTP, escuta local e avisos. Distinga testes simulados, login real e disponibilidade dos provedores. Peça autorização antes de testes de geração que consumam cota/créditos.

Entregue os locais finais, comandos de uso, resultados, limitações e reversão. Se a cota, o contexto ou o tempo estiverem acabando, salve CONTINUIDADE.md sem segredos: objetivo, arquivos alterados, backups, etapas e testes concluídos, pendências, operações incertas e próxima ação. Não declare concluído o que não foi verificado.
```

### Prompt de instalação — macOS

```text
Instale globalmente o Claude-Antigravity-Kit neste Mac. Estou autorizando a instalação do kit e das dependências necessárias, preservando meus dados.

Repositório: https://github.com/matheusdavipc-ai/Claude-Antigravity-Kit.git
Clone-o em uma pasta do meu usuário, ou reutilize um clone existente depois de conferir origem e alterações locais. Não sobrescreva trabalho existente.

Verifique Git, Python 3.12+, Node.js LTS 22.19+ e Claude Code nativo 2.1.292+. Use Homebrew se já estiver disponível ou os instaladores oficiais. Não instale Homebrew silenciosamente nem recorra a sudo para corrigir permissões de npm. Na pasta do clone, execute primeiro:
bash install.sh --dry-run
Depois, execute:
bash install.sh
O instalador instala Claude nativo e OmniRoute se ausentes. Verifique a versão do Claude existente antes de prosseguir. Se python3 não apontar para Python 3.12+, selecione o executável correto por CLAUDE_KIT_PYTHON.

Use ~/.claude, ~/.claude/profiles/router e ~/.claude/launcher para os perfis e suporte; compartilhe o bundle em ~/.gemini/config. A chave OpenRouter deve ser digitada por mim em entrada local oculta e armazenada no Keychain. Nunca solicite a chave no chat nem a coloque em argumentos, logs ou prints. Se seu terminal não permitir entrada oculta, use --skip-key e me oriente a executar localmente replace_key.py do runtime. Eu concluo as autorizações legítimas do Keychain e o login Anthropic nativo. Não use credenciais de outro computador nem fallback em texto puro. Confira ~/.zshrc; se eu usar outra shell, adapte o PATH dela. Reabra o terminal e confira os dois comandos.

Leia README.md, AGENTS.md, models.json e docs/CATALOGO.md antes de alterar arquivos. Primeiro faça a auditoria e o dry-run; depois execute a instalação e as verificações. Preserve configurações existentes, use os backups e a reversão do instalador e não copie perfis privados para o clone. Instale dependências ausentes por fontes oficiais, sem usar runtimes embutidos em outros aplicativos.

Configure claude para a assinatura Anthropic original e clauderouter para OpenRouter, em perfis separados. A instalação global deve funcionar sem depender da pasta clonada. Instale todas as skills, agentes e workflows do bundle; use /workflow-* para evitar conflitos com comandos nativos. Memória pessoal permanece desativada.

Respeite exatamente as funções e duplas de models.json:
- Orquestrador: Inkling → Nemotron 3 Ultra.
- Programador principal: Inkling Small → Laguna S 2.1.
- Especialista visual: Nemotron 3.5 Super VL → Inkling Small.
- Executor rápido: North Mini Code → Laguna XS 2.1.
- Programador auxiliar: Laguna XS 2.1 → North Mini Code.
São sete modelos distintos em dez posições. Preserve os nomes originais e descrições de função em /model, os limites de contexto por modelo e as regras de compactação. Não acrescente modelos pagos ou terceiros. Revalide metadados e informe restrições, expiração ou indisponibilidade; não invente substitutos.

Mantenha as políticas de orquestração separadas: Sonnet/Opus e esforço no claude original; os cinco agentes próprios e as duplas acima no router. Preserve a troca automática por esgotamento reconhecido somente em estado ocioso verificado e sem processos auxiliares; o retorno é manual.

Configure o OmniRoute em ~/.omniroute/.env, escutando em 127.0.0.1:20128, preservando chaves de criptografia existentes. O filtro do kit chama OpenRouter diretamente; OmniRoute não é obrigatório para abrir claude ou clauderouter. Se necessário, inicie omniroute serve --no-open e ajude no primeiro acesso e na conexão OpenRouter pelo dashboard http://127.0.0.1:20128/dashboard/providers/openrouter. Essa conexão é separada da chave protegida do router. Use autenticação legítima; não altere o banco diretamente. Não crie início automático do sistema.

Execute a auditoria pública, os testes do repositório e do runtime, o diagnóstico nativo sem geração, a listagem clauderouter --listar-modelos e a verificação de isolamento dos perfis. Se iniciar OmniRoute, confira saúde HTTP, escuta local e avisos. Distinga testes simulados, login real e disponibilidade dos provedores. Peça autorização antes de testes de geração que consumam cota/créditos.

Entregue os locais finais, comandos de uso, resultados, limitações e reversão. Se a cota, o contexto ou o tempo estiverem acabando, salve CONTINUIDADE.md sem segredos: objetivo, arquivos alterados, backups, etapas e testes concluídos, pendências, operações incertas e próxima ação. Não declare concluído o que não foi verificado.
```

Prefere instalar pelo terminal? Veja [Windows](#instalar-no-windows) ou [macOS](#instalar-no-macos). Para escolher e usar os recursos depois, abra o [catálogo completo de skills, agentes e workflows](docs/CATALOGO.md).

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

O [catálogo completo](docs/CATALOGO.md) explica **cada recurso**, quando usar e como invocar, com exemplos e links para suas instruções.

| Conteúdo | O que você encontra no catálogo |
|---|---|
| 29 skills de conhecimento e coordenação | Finalidade e exemplo de uso de cada skill; inclui a skill mestre orchestration-kit. |
| 11 skills de workflow | Procedimentos de planejamento, criação, investigação, publicação e outros objetivos. Somadas às 29 acima, são 40 skills. |
| 17 agentes especialistas | Qual especialista escolher no Claude original e como aplicar a persona no Antigravity. |
| 5 agentes do OpenRouter | Função, modelo principal, reserva e exemplos de delegação próprios do perfil router. |
| Recursos internos | As 23 operações do Impeccable e os 13 templates do app-builder, com indicação de uso. |

Exemplos no Claude Code:

```text
/workflow-plan Planeje uma área de login; não implemente ainda.
/api-patterns Defina a API de pedidos com paginação e erros consistentes.
/impeccable audit Revise a acessibilidade e a responsividade desta tela.
Use o agente test-engineer para verificar os casos de borda desta regra.
```

No Antigravity, selecione `/nome-da-skill` ou peça que aplique seu conhecimento. Os agentes distribuídos são personas Markdown: peça a leitura do arquivo correspondente em `~/.gemini/config/agents/`. Isso não garante a criação de um subagente nativo.

Prefira `/workflow-create`, `/workflow-plan`, `/workflow-debug` e os demais nomes `workflow-*` nas duas ferramentas. Os comandos Claude legados continuam em `~/.claude/commands`, mas alguns nomes, como `/status`, `/debug` e `/plan`, podem coincidir com comandos nativos. Os workflows convertidos atendem à migração oficial do Antigravity para skills. No router, siga os cinco agentes próprios; os procedimentos genéricos de orquestração do perfil original não substituem essa política.

O conteúdo foi generalizado a partir do kit fornecido pelo proprietário, removendo referências pessoais, projetos, MCP e settings específicos. Memória Obsidian é opcional e desativada por padrão. Skills e agentes usam a cota do modelo ativo; não incluem novas contas ou créditos.

O instalador mescla arquivos individualmente, preserva arquivos não relacionados, verifica links existentes e mantém backups privados em `~/.claude/launcher/backups`. Reinstalar atualiza os arquivos do kit; suas edições nesses mesmos arquivos são arquivadas antes. Históricos e credenciais nunca entram no bundle.

## Verificação, reversão e publicação

```bash
python scripts/audit_public.py
python -m unittest discover -s tests -v
python runtime/test_profiles.py
```

Os testes de roteamento usam servidor simulado e não geram cobranças. A [primeira execução da CI passou no Windows e no macOS](https://github.com/matheusdavipc-ai/Claude-Antigravity-Kit/actions/runs/39157803472). Isso valida as suites automatizadas, não o login interativo nem o uso real de Keychain/Claude em um Mac. Veja os detalhes e limites em [Validação](docs/VALIDACAO.md).

Para reverter a última instalação: `python ~/.claude/launcher/runtime/rollback.py`. A reversão recusa sobrescrever edições posteriores, preserva diretórios, links e credenciais, e não desinstala Python/Node/Claude/OmniRoute. Registros anteriores ficam em cada backup. Caso haja interrupção, leia `installation.json` e o backup correspondente; não execute uma reinstalação cega.

Antes de publicar, execute a auditoria. Publique **somente este repositório**, nunca `.claude`, `.gemini`, `.omniroute`, backups, logs ou pastas de clientes. O `.gitignore` e a auditoria são proteções complementares, não substituem revisar o diff. Os instaladores não publicam arquivos automaticamente; revise o conteúdo antes de enviar alterações ao GitHub.

## Fontes

- [Instalação oficial do Claude](https://code.claude.com/docs/en/setup)
- [Seletor e nomes de modelos](https://code.claude.com/docs/en/settings-reference#modelpicker)
- [Modelos e perfis](https://code.claude.com/docs/en/model-config)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [OmniRoute](https://github.com/diegosouzapw/OmniRoute)
- [Integração OpenRouter/Claude Code](https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration)
- [Migração de workflows do Antigravity](https://antigravity.google/docs/migration/workflows-to-skills)

Os prompts acima também estão em [Prompts de instalação](docs/PROMPT-INSTALACAO.md). Veja o [catálogo de uso](docs/CATALOGO.md) e os [avisos de terceiros](THIRD_PARTY_NOTICES.md) para conhecer os recursos e sua origem.

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
