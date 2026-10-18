# Prompts de instalação com uma IA

Estas são as mesmas instruções publicadas no início do [README](../README.md). Copie somente o bloco do seu sistema. Use uma IA com acesso local ao terminal e aos arquivos; você conclui os logins e digita sua chave em entrada oculta no computador. Para conhecer cada recurso, consulte o [catálogo de uso](CATALOGO.md).

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

Configure o OmniRoute em ~/.omniroute/.env, escutando em 127.0.0.1:20128, preservando chaves de criptografia existentes. O filtro do kit chama OpenRouter diretamente; OmniRoute não é obrigatório para abrir claude ou clauderouter. Antes de iniciar, verifique http://127.0.0.1:20128/api/health e confirme que a porta pertence ao OmniRoute. Se ele já estiver saudável, reutilize a instância e execute omniroute dashboard para abrir o painel; não inicie outro servidor. Se estiver parado e a porta estiver livre, inicie omniroute serve --no-open. Se a porta pertencer a outro programa ou a saúde falhar, investigue sem encerrar processos automaticamente. Ajude no primeiro acesso e na conexão OpenRouter pelo dashboard http://127.0.0.1:20128/dashboard/providers/openrouter. Essa conexão é separada da chave protegida do router. Use autenticação legítima; não altere o banco diretamente. Não crie início automático do sistema.

Execute a auditoria pública, os testes do repositório e do runtime, o diagnóstico nativo sem geração, a listagem clauderouter --listar-modelos e a verificação de isolamento dos perfis. Se iniciar OmniRoute, confira saúde HTTP, escuta local e avisos. Distinga testes simulados, login real e disponibilidade dos provedores. Peça autorização antes de testes de geração que consumam cota/créditos. Ao concluir os testes, encerre as instâncias temporárias de OmniRoute que você iniciou e confirme a liberação da porta, para que eu possa executar omniroute no meu terminal. Preserve instâncias que já existiam antes da instalação; informe se alguma permanecer ativa e como encerrá-la legitimamente.

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

Configure o OmniRoute em ~/.omniroute/.env, escutando em 127.0.0.1:20128, preservando chaves de criptografia existentes. O filtro do kit chama OpenRouter diretamente; OmniRoute não é obrigatório para abrir claude ou clauderouter. Antes de iniciar, verifique http://127.0.0.1:20128/api/health e confirme que a porta pertence ao OmniRoute. Se ele já estiver saudável, reutilize a instância e execute omniroute dashboard para abrir o painel; não inicie outro servidor. Se estiver parado e a porta estiver livre, inicie omniroute serve --no-open. Se a porta pertencer a outro programa ou a saúde falhar, investigue sem encerrar processos automaticamente. Ajude no primeiro acesso e na conexão OpenRouter pelo dashboard http://127.0.0.1:20128/dashboard/providers/openrouter. Essa conexão é separada da chave protegida do router. Use autenticação legítima; não altere o banco diretamente. Não crie início automático do sistema.

Execute a auditoria pública, os testes do repositório e do runtime, o diagnóstico nativo sem geração, a listagem clauderouter --listar-modelos e a verificação de isolamento dos perfis. Se iniciar OmniRoute, confira saúde HTTP, escuta local e avisos. Distinga testes simulados, login real e disponibilidade dos provedores. Peça autorização antes de testes de geração que consumam cota/créditos. Ao concluir os testes, encerre as instâncias temporárias de OmniRoute que você iniciou e confirme a liberação da porta, para que eu possa executar omniroute no meu terminal. Preserve instâncias que já existiam antes da instalação; informe se alguma permanecer ativa e como encerrá-la legitimamente.

Entregue os locais finais, comandos de uso, resultados, limitações e reversão. Se a cota, o contexto ou o tempo estiverem acabando, salve CONTINUIDADE.md sem segredos: objetivo, arquivos alterados, backups, etapas e testes concluídos, pendências, operações incertas e próxima ação. Não declare concluído o que não foi verificado.
```

Prefere instalar pelo terminal? Veja [Windows](../README.md#instalar-no-windows) ou [macOS](../README.md#instalar-no-macos). Para escolher e usar os recursos depois, abra o [catálogo completo de skills, agentes e workflows](CATALOGO.md).
