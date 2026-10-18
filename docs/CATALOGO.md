# Catálogo de skills, agentes e workflows

Este guia cobre o conteúdo que realmente acompanha o repositório: **40 skills** (28 de domínio, a skill mestre orchestration-kit e 11 workflows convertidos), **17 agentes especialistas**, **5 agentes do router** e **11 workflows**. Os workflows convertidos são os mesmos 11 procedimentos, não 11 modelos adicionais.

**Neste guia:** [como usar nas ferramentas](#como-usar-em-cada-ferramenta) · [skills](#skills-de-conhecimento-e-coordenação-29) · [Impeccable](#impeccable-subcomandos) · [templates](#app-builder-biblioteca-de-templates) · [agentes especialistas](#agentes-especialistas-do-perfil-original-17) · [agentes OpenRouter](#agentes-e-funções-do-openrouter-5) · [workflows](#workflows-e-skills-de-procedimento-11) · [receitas](#receitas-para-começar).

## Entenda a diferença

| Recurso | O que é | Como escolher |
|---|---|---|
| Skill | Conhecimento e instruções para uma área ou procedimento. | Escolha o conhecimento necessário, como API, design ou testes. |
| Agente | Um papel especializado, com instruções e ferramentas definidas. | Escolha quem deve executar ou analisar uma tarefa. |
| Workflow | Uma sequência de trabalho para um objetivo. | Escolha o processo, como planejar, criar, investigar ou publicar. |
| Modelo | O serviço de IA que responde. | É escolhido pelo perfil e pela política de orquestração. |

Skills e agentes não são provedores novos nem contas separadas. Invocá-los usa a sessão e pode consumir a cota do modelo ativo. Scripts incluídos exigem os executáveis, dependências e permissões do projeto; instalar uma skill não instala automaticamente Playwright, bancos, hospedagem ou serviços de clientes.

## Como usar em cada ferramenta

### Claude Code original (`claude`)

Abra o terminal na pasta do projeto e execute `claude`. Digite `/` para procurar as skills disponíveis. Você pode invocar `/nome-da-skill instrução` ou pedir em linguagem natural que a IA aplique a skill. Para um especialista, peça “Use o agente backend-specialist para…”; `/agents` permite inspecionar os subagentes registrados. Apenas citar um nome não comprova que houve uma delegação: confira o resultado informado pela ferramenta. A política Sonnet/Opus e esforço vem do CLAUDE.md original.

Exemplos:

```text
/api-patterns Desenhe uma API de pedidos com paginação e erros consistentes.
/impeccable audit Revise a acessibilidade e a responsividade desta tela.
/workflow-plan Planeje autenticação e recuperação de senha; não implemente ainda.
Use o agente test-engineer para verificar os casos de borda desta regra.
```

Invocação e descoberta seguem as [skills do Claude Code](https://code.claude.com/docs/en/skills) e os [subagentes nativos](https://code.claude.com/docs/en/sub-agents).

### Antigravity

Abra o projeto no Antigravity. Invoque a skill por `/nome-da-skill`, selecionando a opção exibida, ou peça explicitamente que aplique seu conhecimento. Para procedimentos do kit, prefira `/workflow-plan`, `/workflow-create`, etc. Os 17 arquivos de agente são personas Markdown: peça que a IA leia o arquivo de `~/.gemini/config/agents/` e aplique sua especialidade. A existência do arquivo não cria automaticamente um processo ou subagente nativo. A delegação nativa depende das capacidades da sua edição do Antigravity.

Exemplo:

```text
Leia ~/.gemini/config/agents/frontend-specialist.md e aplique sua especialidade
para revisar a tela de cadastro, usando as skills pertinentes.
```

Referências: [skills do Antigravity](https://antigravity.google/docs/skills) e [migração de workflows para skills](https://antigravity.google/docs/migration/workflows-to-skills).

### Perfil OpenRouter (`clauderouter`)

Abra `clauderouter` na pasta do projeto. O coordenador usa a equipe obrigatória do README e os cinco agentes `router-*` abaixo. Peça tarefas por função e use as skills de domínio pertinentes como conhecimento. Não transfira a tabela de esforço Sonnet/Opus nem os agentes do original para este perfil. O hook só permite as cinco funções.

Os workflows genéricos de orquestração do bundle têm instruções do perfil original; não os trate como uma substituição dos agentes router. Para uma tarefa com vários domínios no router, peça ao coordenador que planeje, delegue às funções próprias e revise. Uma skill compartilhada não autoriza trocar a equipe obrigatória.

```text
Planeje esta funcionalidade. Delegue a implementação ao router-coder,
a análise do print ao router-visual e uma tarefa auxiliar delimitada ao
router-assistant. Revise os resultados e não permita edições concorrentes
no mesmo arquivo. Mantenha as duplas principal/reserva configuradas.
```

## Skills de conhecimento e coordenação (29)

Os exemplos de barra abaixo são para o campo de conversa, não comandos do terminal. No Antigravity, selecione a skill correspondente quando o menu aparecer. Também é possível pedir “Aplique a skill X…” em linguagem natural.

| Skill e fonte | Para que usar | Exemplo de uso |
|---|---|---|
| [api-patterns](../bundle/skills/api-patterns/SKILL.md) | Desenhar APIs e escolher REST, GraphQL ou tRPC; cobre respostas, paginação, autenticação e versionamento. | `/api-patterns Projete uma API de pedidos com paginação e erros consistentes.` |
| [app-builder](../bundle/skills/app-builder/SKILL.md) | Transformar uma ideia em uma aplicação, escolhendo stack e um template adequado antes de coordenar a construção. | `/app-builder Planeje e construa um sistema de reservas com painel administrativo.` |
| [architecture](../bundle/skills/architecture/SKILL.md) | Comparar arquiteturas, dependências e custos de manutenção; registrar a decisão e seus motivos em um ADR. | `/architecture Compare monólito modular e serviços separados para este projeto.` |
| [avoid-ai-writing](../bundle/skills/avoid-ai-writing/SKILL.md) | Revisar ou reescrever textos para remover padrões repetitivos e melhorar a voz; não comprova autoria humana ou por IA. | `/avoid-ai-writing --mode detect --context docs Analise o README sem alterá-lo.` |
| [bash-linux](../bundle/skills/bash-linux/SKILL.md) | Preparar comandos e scripts Bash para macOS/Linux, com tratamento de erros, arquivos, pipes e processos. Não é PowerShell. | `/bash-linux Crie um script que valide arquivos antes de iniciar o servidor.` |
| [behavioral-modes](../bundle/skills/behavioral-modes/SKILL.md) | Adequar a atuação da IA a exploração, implementação, depuração, revisão ou ensino, conforme o objetivo. | `/behavioral-modes Atue em modo de ensino e explique esta função passo a passo.` |
| [brainstorming](../bundle/skills/brainstorming/SKILL.md) | Esclarecer objetivo, usuários, restrições e alternativas antes de implementar uma ideia ainda pouco definida. | `/brainstorming Explore três abordagens para um aplicativo de agendamento.` |
| [clean-code](../bundle/skills/clean-code/SKILL.md) | Aplicar nomes claros, funções pequenas e responsabilidades bem separadas, evitando abstrações desnecessárias. | `/clean-code Refatore este módulo mantendo seu comportamento público.` |
| [code-review-checklist](../bundle/skills/code-review-checklist/SKILL.md) | Revisar correção, casos de borda, segurança, desempenho e cobertura antes de integrar uma alteração. | `/code-review-checklist Revise o diff atual e priorize os problemas encontrados.` |
| [database-design](../bundle/skills/database-design/SKILL.md) | Projetar tabelas, relações, índices e migrações; comparar banco e ORM segundo as necessidades reais. | `/database-design Modele clientes, contratos e pagamentos sem duplicar dados.` |
| [deployment-procedures](../bundle/skills/deployment-procedures/SKILL.md) | Preparar publicação, verificações e recuperação; escolher procedimentos adequados à plataforma. Não é um serviço de hospedagem. | `/deployment-procedures Prepare um plano de deploy e rollback, sem executar a publicação.` |
| [design-motion-principles](../bundle/skills/design-motion-principles/SKILL.md) | Avaliar transições, estados hover, animações e feedback visual; melhorar movimento sem atrapalhar o uso. | `/design-motion-principles Audite as animações deste menu e considere movimento reduzido.` |
| [documentation-templates](../bundle/skills/documentation-templates/SKILL.md) | Estruturar README, documentação de APIs, comentários de código e changelog quando a documentação for solicitada. | `/documentation-templates Escreva o README com instalação, uso e exemplos.` |
| [impeccable](../bundle/skills/impeccable/SKILL.md) | Projetar e revisar interfaces, hierarquia visual, acessibilidade, responsividade, tipografia e textos de UX. Possui subcomandos próprios. | `/impeccable audit Revise a tela de cadastro no desktop e no celular.` |
| [intelligent-routing](../bundle/skills/intelligent-routing/SKILL.md) | Identificar o domínio da tarefa e escolher o especialista adequado; no router, a política das cinco funções tem prioridade. | `/intelligent-routing Indique quem deve investigar uma lentidão na API e por quê.` |
| [lint-and-validate](../bundle/skills/lint-and-validate/SKILL.md) | Escolher e executar lint, validação de tipos e análise estática do projeto; relatar o que realmente passou. | `/lint-and-validate Rode as verificações já configuradas e corrija as falhas pertinentes.` |
| [nextjs-react-expert](../bundle/skills/nextjs-react-expert/SKILL.md) | Aplicar os padrões de React/Next.js do bundle para reduzir waterfalls, custo de renderização e tamanho de bundle. | `/nextjs-react-expert Investigue renderizações desnecessárias nesta página Next.js.` |
| [nodejs-best-practices](../bundle/skills/nodejs-best-practices/SKILL.md) | Decidir estrutura, framework e padrões assíncronos de um backend Node.js, considerando erros e segurança. | `/nodejs-best-practices Revise o tratamento de erros e operações assíncronas desta API.` |
| [orchestration-kit](../bundle/skills/orchestration-kit/SKILL.md) | Consultar o registro do framework, localizar skills e agentes e organizar verificações que abrangem vários domínios. | `/orchestration-kit Planeje uma revisão deste projeto por domínio e indique os arquivos pertinentes.` |
| [parallel-agents](../bundle/skills/parallel-agents/SKILL.md) | Dividir tarefas independentes entre agentes quando a ferramenta oferecer delegação; evitar edições concorrentes no mesmo arquivo. | `/parallel-agents Separe análise de testes, segurança e desempenho sem modificar arquivos compartilhados.` |
| [performance-profiling](../bundle/skills/performance-profiling/SKILL.md) | Medir antes de otimizar: carregamento, CPU, memória, bundle e Core Web Vitals; comparar resultados antes/depois. | `/performance-profiling Descubra por que esta página demora a carregar e proponha medições.` |
| [plan-writing](../bundle/skills/plan-writing/SKILL.md) | Transformar um objetivo em etapas pequenas, dependências e critérios verificáveis de conclusão. | `/plan-writing Planeje a implementação de recuperação de senha, sem escrever código ainda.` |
| [seo-fundamentals](../bundle/skills/seo-fundamentals/SKILL.md) | Revisar indexação, metadados, conteúdo, estrutura e sinais técnicos de SEO; não garante posição nas buscas. | `/seo-fundamentals Audite títulos, descrições, sitemap e indexação deste site.` |
| [server-management](../bundle/skills/server-management/SKILL.md) | Planejar processos, monitoramento, logs e capacidade de servidores conforme o ambiente disponível. | `/server-management Analise o gerenciamento do servidor e proponha melhorias sem reiniciá-lo.` |
| [systematic-debugging](../bundle/skills/systematic-debugging/SKILL.md) | Reproduzir o erro, levantar hipóteses e evidências, encontrar a causa e validar a correção. | `/systematic-debugging Investigue por que o login falha somente após renovar o token.` |
| [tailwind-patterns](../bundle/skills/tailwind-patterns/SKILL.md) | Organizar estilos Tailwind, tokens, responsividade e padrões de componentes conforme a versão do projeto. | `/tailwind-patterns Padronize os espaçamentos e a responsividade deste formulário.` |
| [testing-patterns](../bundle/skills/testing-patterns/SKILL.md) | Escolher testes unitários e de integração, fixtures e mocks; verificar comportamento com casos relevantes. | `/testing-patterns Proponha testes para descontos, limites e arredondamento deste cálculo.` |
| [vulnerability-scanner](../bundle/skills/vulnerability-scanner/SKILL.md) | Analisar superfície de ataque, dependências e falhas de aplicação no código e ambientes autorizados. | `/vulnerability-scanner Revise autenticação e dependências deste repositório; apresente as evidências.` |
| [webapp-testing](../bundle/skills/webapp-testing/SKILL.md) | Planejar e executar testes de navegador/E2E com ferramentas disponíveis, como Playwright, e registrar falhas reproduzíveis. | `/webapp-testing Teste cadastro, login e recuperação de senha em um ambiente de teste.` |

### Impeccable: subcomandos

É uma única skill com várias operações. No Claude use `/impeccable operação alvo`; no Antigravity invoque `impeccable` e informe a operação. O texto upstream menciona `$impeccable` para outros hosts; aqui use o formato de invocação reconhecido pela sua ferramenta. Exemplo: `/impeccable polish formulário de cadastro`.

| Operação | Quando usar |
|---|---|
| [craft](../bundle/skills/impeccable/reference/craft.md) | Planejar e construir uma interface ou funcionalidade de ponta a ponta. |
| [shape](../bundle/skills/impeccable/reference/shape.md) | Definir UX, estrutura e decisões visuais antes do código. |
| [teach](../bundle/skills/impeccable/reference/teach.md) | Levantar contexto do produto e preparar PRODUCT.md/DESIGN.md do projeto. |
| [document](../bundle/skills/impeccable/reference/document.md) | Registrar em DESIGN.md o sistema visual já presente no código. |
| [extract](../bundle/skills/impeccable/reference/extract.md) | Extrair tokens e componentes reutilizáveis. |
| [critique](../bundle/skills/impeccable/reference/critique.md) | Avaliar a experiência e a hierarquia com critérios de design. |
| [audit](../bundle/skills/impeccable/reference/audit.md) | Verificar acessibilidade, responsividade e qualidade técnica da interface. |
| [polish](../bundle/skills/impeccable/reference/polish.md) | Refinar alinhamentos, consistência e acabamento antes da entrega. |
| [bolder](../bundle/skills/impeccable/reference/bolder.md) | Dar mais força visual a uma interface sem personalidade. |
| [quieter](../bundle/skills/impeccable/reference/quieter.md) | Reduzir ruído e estímulos em uma interface excessiva. |
| [distill](../bundle/skills/impeccable/reference/distill.md) | Remover complexidade e manter o essencial. |
| [harden](../bundle/skills/impeccable/reference/harden.md) | Tratar erros, casos de borda, internacionalização e estados incompletos. |
| [onboard](../bundle/skills/impeccable/reference/onboard.md) | Melhorar primeiro uso, ativação e estados vazios. |
| [animate](../bundle/skills/impeccable/reference/animate.md) | Adicionar movimento com propósito e feedback. |
| [colorize](../bundle/skills/impeccable/reference/colorize.md) | Aplicar cor de maneira coerente a uma interface monótona. |
| [typeset](../bundle/skills/impeccable/reference/typeset.md) | Melhorar fontes, legibilidade e hierarquia tipográfica. |
| [layout](../bundle/skills/impeccable/reference/layout.md) | Ajustar espaçamentos, organização e ritmo visual. |
| [delight](../bundle/skills/impeccable/reference/delight.md) | Adicionar detalhes de personalidade que ajudem a experiência. |
| [overdrive](../bundle/skills/impeccable/reference/overdrive.md) | Explorar soluções visuais ambiciosas quando fizer sentido para o produto. |
| [clarify](../bundle/skills/impeccable/reference/clarify.md) | Melhorar rótulos, instruções, mensagens e textos de UX. |
| [adapt](../bundle/skills/impeccable/reference/adapt.md) | Adaptar a interface a outros dispositivos e tamanhos. |
| [optimize](../bundle/skills/impeccable/reference/optimize.md) | Investigar e reduzir custos de desempenho da interface. |
| [live](../bundle/skills/impeccable/reference/live.md) | Comparar variações visuais no navegador; depende das ferramentas e dependências disponíveis. |

`pin <operação>` e `unpin <operação>` são as opções de gerenciamento descritas na própria skill. Elas ajustam padrões dessa skill; não instalam um plugin novo. Mantenha PRODUCT.md e DESIGN.md dentro do projeto, nunca no kit global.

### Modos de revisão de texto

`avoid-ai-writing` aceita `rewrite` (reescrever), `detect` (apontar padrões sem editar) e `edit` (alterar um arquivo indicado). As opções de voz incluem `casual`, `professional`, `technical`, `warm` e `blunt`. Exemplo: `/avoid-ai-writing --mode edit --voice technical --file README.md`. Não use esses sinais como prova de autoria de um texto.

### App Builder: biblioteca de templates

O [subguia de templates](../bundle/skills/app-builder/templates/SKILL.md) e o [índice](../bundle/skills/app-builder/templates/INDEX.md) são material de apoio de app-builder, não outro conjunto de agentes. Peça `/app-builder` e descreva requisitos; a IA escolhe um ponto de partida adequado. Templates não trazem contas, banco em produção ou credenciais.

| Template | Ponto de partida |
|---|---|
| [astro-static](../bundle/skills/app-builder/templates/astro-static/TEMPLATE.md) | Site estático de conteúdo. |
| [chrome-extension](../bundle/skills/app-builder/templates/chrome-extension/TEMPLATE.md) | Extensão de navegador. |
| [cli-tool](../bundle/skills/app-builder/templates/cli-tool/TEMPLATE.md) | Ferramenta de linha de comando. |
| [electron-desktop](../bundle/skills/app-builder/templates/electron-desktop/TEMPLATE.md) | Aplicativo desktop baseado em tecnologias web. |
| [express-api](../bundle/skills/app-builder/templates/express-api/TEMPLATE.md) | API em Node.js/Express. |
| [flutter-app](../bundle/skills/app-builder/templates/flutter-app/TEMPLATE.md) | Aplicativo Flutter. |
| [monorepo-turborepo](../bundle/skills/app-builder/templates/monorepo-turborepo/TEMPLATE.md) | Vários pacotes ou aplicações em um monorepo. |
| [nextjs-fullstack](../bundle/skills/app-builder/templates/nextjs-fullstack/TEMPLATE.md) | Aplicação web Next.js com backend. |
| [nextjs-saas](../bundle/skills/app-builder/templates/nextjs-saas/TEMPLATE.md) | Produto SaaS como ponto de partida. |
| [nextjs-static](../bundle/skills/app-builder/templates/nextjs-static/TEMPLATE.md) | Site Next.js com estratégia estática. |
| [nuxt-app](../bundle/skills/app-builder/templates/nuxt-app/TEMPLATE.md) | Aplicação Vue/Nuxt. |
| [python-fastapi](../bundle/skills/app-builder/templates/python-fastapi/TEMPLATE.md) | API Python/FastAPI. |
| [react-native-app](../bundle/skills/app-builder/templates/react-native-app/TEMPLATE.md) | Aplicativo React Native. |

## Agentes especialistas do perfil original (17)

Peça o uso do agente em linguagem natural no Claude original. No Antigravity, peça a leitura da persona e aplicação da especialidade. Estes exemplos descrevem o objetivo, sem prometer ferramentas que seu ambiente não fornece.

| Agente e fonte | Responsabilidade | Pedido de exemplo |
|---|---|---|
| [backend-specialist](../bundle/agents/backend-specialist.md) | APIs, autenticação, regras de negócio e integrações no servidor. | Use o agente backend-specialist para implementar o endpoint de pedidos seguindo a arquitetura existente. |
| [code-archaeologist](../bundle/agents/code-archaeologist.md) | Entendimento e modernização de código legado ou sem documentação. | Use o agente code-archaeologist para mapear este módulo legado antes de propor mudanças. |
| [database-architect](../bundle/agents/database-architect.md) | Modelagem, SQL, índices, consultas e migrações de dados. | Use o agente database-architect para revisar o esquema e justificar os índices necessários. |
| [debugger](../bundle/agents/debugger.md) | Investigação de falhas e identificação de causa raiz. | Use o agente debugger para reproduzir este erro e validar a hipótese antes de corrigi-lo. |
| [devops-engineer](../bundle/agents/devops-engineer.md) | CI/CD, servidores, deploy, observabilidade e rollback. | Use o agente devops-engineer para revisar o pipeline; não publique em produção nesta etapa. |
| [documentation-writer](../bundle/agents/documentation-writer.md) | Documentação técnica solicitada: README, APIs e changelog. | Use o agente documentation-writer para documentar a instalação e os comandos desta ferramenta. |
| [explorer-agent](../bundle/agents/explorer-agent.md) | Reconhecimento do repositório, dependências e pontos de entrada. | Use o agente explorer-agent para explicar o fluxo de autenticação, sem editar arquivos. |
| [frontend-specialist](../bundle/agents/frontend-specialist.md) | Componentes, estado, acessibilidade, estilos e interfaces web. | Use o agente frontend-specialist para implementar esta tela com estados de erro e carregamento. |
| [orchestrator](../bundle/agents/orchestrator.md) | Coordenação de especialistas em tarefas com vários domínios. | Use o agente orchestrator para organizar a implementação de uma funcionalidade que envolve interface, API e testes. |
| [performance-optimizer](../bundle/agents/performance-optimizer.md) | Gargalos de carregamento, renderização, CPU, memória e bundle. | Use o agente performance-optimizer para medir a lentidão e comparar o resultado da correção. |
| [product-manager](../bundle/agents/product-manager.md) | Requisitos, histórias de usuário e critérios de aceitação. | Use o agente product-manager para transformar esta ideia em requisitos verificáveis. |
| [product-owner](../bundle/agents/product-owner.md) | MVP, backlog, prioridades e alinhamento com os objetivos do produto. | Use o agente product-owner para ordenar o backlog por valor e dependências. |
| [project-planner](../bundle/agents/project-planner.md) | Plano técnico, arquivos envolvidos, etapas e dependências. | Use o agente project-planner para criar um plano de implementação antes de alterar o código. |
| [qa-automation-engineer](../bundle/agents/qa-automation-engineer.md) | Infraestrutura de testes automatizados, E2E e regressão em CI. | Use o agente qa-automation-engineer para automatizar os fluxos críticos de compra no ambiente de teste. |
| [security-auditor](../bundle/agents/security-auditor.md) | Revisão de segurança, autorização, exposição de dados e dependências. | Use o agente security-auditor para revisar permissões e isolamento entre usuários neste projeto. |
| [seo-specialist](../bundle/agents/seo-specialist.md) | SEO técnico, estrutura de conteúdo e visibilidade nas buscas. | Use o agente seo-specialist para revisar a página pública e priorizar os ajustes de SEO. |
| [test-engineer](../bundle/agents/test-engineer.md) | Estratégia de testes, casos de borda, cobertura e diagnóstico de falhas. | Use o agente test-engineer para testar as regras de faturamento com casos de borda. |

## Agentes e funções do OpenRouter (5)

A coordenação principal permanece na conversa. Os especialistas recebem tarefas delimitadas; a reserva é selecionada pelo filtro em falhas elegíveis, não pela preferência do agente.

| Agente e fonte | Função | Principal → reserva | Pedido de exemplo |
|---|---|---|---|
| [router-orchestrator](../templates/router-agents/router-orchestrator.md) | Coordenação, planejamento e revisão. A conversa principal já faz a coordenação. | Inkling → Nemotron 3 Ultra | Planeje a tarefa, distribua o trabalho pelas funções do router e revise os resultados. |
| [router-coder](../templates/router-agents/router-coder.md) | Implementação principal de sites, APIs, sistemas e integrações. | Inkling Small → Laguna S 2.1 | Delegue ao router-coder a implementação da API de pedidos e seus testes pertinentes. |
| [router-visual](../templates/router-agents/router-visual.md) | Análise de imagens e referências de interface. | Nemotron 3.5 Super VL → Inkling Small | Use router-visual para analisar este print e descrever hierarquia, espaçamentos e diferenças. |
| [router-fast](../templates/router-agents/router-fast.md) | Trabalhos curtos e bem delimitados. | North Mini Code → Laguna XS 2.1 | Delegue ao router-fast a correção destas mensagens de validação. |
| [router-assistant](../templates/router-agents/router-assistant.md) | Tarefas auxiliares e apoio à implementação principal. | Laguna XS 2.1 → North Mini Code | Delegue ao router-assistant a análise dos testes existentes e a lista de lacunas. |

Ao delegar pelo Agent no router, o coordenador omite `model` e `effort` da chamada; o frontmatter e a política de contexto escolhem o modelo da função. A equipe permanece com sete modelos distintos e cinco duplas.

## Workflows e skills de procedimento (11)

A forma recomendada é **`/workflow-nome` em ambas as ferramentas**. Essas onze skills são parte das 40 listadas na introdução. Os aliases legados são fornecidos por `.claude/commands`; nomes como `/status`, `/debug` e `/plan` podem ter funções próprias da ferramenta. Usar o prefixo evita confundir o comando do kit com comandos nativos. Se o comando não aparecer, confira as pastas de instalação e reabra a sessão; não invente que o workflow rodou.

| Skill de procedimento | Alias legado Claude | O que faz e resultado esperado | Exemplo recomendado |
|---|---|---|---|
| [workflow-brainstorm](../bundle/skills/workflow-brainstorm/SKILL.md) | [/brainstorm](../bundle/global_workflows/brainstorm.md) | Explorar alternativas e esclarecer requisitos antes de escolher uma solução. Planejamento e opções, sem implementação prematura. | `/workflow-brainstorm Compare abordagens para uma plataforma de reservas.` |
| [workflow-create](../bundle/skills/workflow-create/SKILL.md) | [/create](../bundle/global_workflows/create.md) | Iniciar uma aplicação nova e acionar o processo de construção. Escolha de stack, estrutura e implementação conforme as decisões acordadas. | `/workflow-create Crie uma aplicação de agendamento com painel administrativo.` |
| [workflow-debug](../bundle/skills/workflow-debug/SKILL.md) | [/debug](../bundle/global_workflows/debug.md) | Organizar uma investigação de erro com reprodução e validação. Diagnóstico apoiado por evidências e correção verificável. | `/workflow-debug Investigue o erro 500 ao cadastrar um pedido.` |
| [workflow-deploy](../bundle/skills/workflow-deploy/SKILL.md) | [/deploy](../bundle/global_workflows/deploy.md) | Preparar verificações, publicação em ambiente definido e rollback. Checklist e plano; execução somente no destino e escopo autorizados. | `/workflow-deploy check` |
| [workflow-enhance](../bundle/skills/workflow-enhance/SKILL.md) | [/enhance](../bundle/global_workflows/enhance.md) | Evoluir uma aplicação existente respeitando seus padrões. Mudança localizada com impactos e validação descritos. | `/workflow-enhance Adicione filtro por período à listagem de pedidos.` |
| [workflow-orchestrate](../bundle/skills/workflow-orchestrate/SKILL.md) | [/orchestrate](../bundle/global_workflows/orchestrate.md) | Coordenar especialistas em uma tarefa que cruza vários domínios. Divisão de responsabilidades e revisão integrada; no router use as funções próprias. | `/workflow-orchestrate Revise interface, API, segurança e testes desta funcionalidade.` |
| [workflow-plan](../bundle/skills/workflow-plan/SKILL.md) | [/plan](../bundle/global_workflows/plan.md) | Planejar um projeto ou funcionalidade sem escrever o código da implementação. Arquivo de plano com etapas, dependências e critérios de conclusão. | `/workflow-plan Planeje a recuperação de senha e seus testes.` |
| [workflow-preview](../bundle/skills/workflow-preview/SKILL.md) | [/preview](../bundle/global_workflows/preview.md) | Controlar o servidor local de desenvolvimento e conferir seu estado. URL e estado do servidor; não é uma publicação na internet. | `/workflow-preview start` |
| [workflow-status](../bundle/skills/workflow-status/SKILL.md) | [/status](../bundle/global_workflows/status.md) | Resumir o estado do projeto, tarefas e verificações. Resumo baseado nos arquivos e evidências disponíveis, sem inventar agentes em execução. | `/workflow-status Mostre o estado do projeto e o que falta validar.` |
| [workflow-test](../bundle/skills/workflow-test/SKILL.md) | [/test](../bundle/global_workflows/test.md) | Organizar testes e analisar falhas. Resultados dos testes realmente executados e pendências identificadas. | `/workflow-test Verifique os fluxos de cadastro e login.` |
| [workflow-ui-ux-pro-max](../bundle/skills/workflow-ui-ux-pro-max/SKILL.md) | [/ui-ux-pro-max](../bundle/global_workflows/ui-ux-pro-max.md) | Consultar a biblioteca de estilos, cores, fontes e padrões de interface. Direção visual justificada e adaptada ao produto. | `/workflow-ui-ux-pro-max Defina a direção visual de um painel de atendimento acessível.` |

`workflow-deploy` tem as etapas `check`, `preview`, `production` e `rollback` descritas no arquivo de origem. `preview` de deploy significa um ambiente de publicação de teste; `workflow-preview` gerencia o servidor de desenvolvimento local. Não são a mesma coisa. Uma execução que publica ou reverte precisa de destino e autorização claros; a presença do workflow não configura sua hospedagem.

`workflow-preview` também descreve `start`, `stop`, `restart` e `check`. O comando pode iniciar processos locais, mas o projeto precisa ter suas dependências e comandos de desenvolvimento preparados.

As skills workflow-* têm `disable-model-invocation: true` para invocação explícita no Claude. Outros hosts podem tratar esse campo de maneira diferente. Elas são instruções para a IA, não scripts que executam todos os passos automaticamente só por instalar o kit.

## Receitas para começar

| Objetivo | Sequência sugerida no Claude original ou Antigravity |
|---|---|
| Criar uma aplicação | workflow-brainstorm → workflow-plan → workflow-create → workflow-test. |
| Evoluir um sistema | explorer-agent para mapear → workflow-plan → workflow-enhance → workflow-test. |
| Corrigir um erro | workflow-debug → systematic-debugging → test-engineer para validar o caso corrigido. |
| Melhorar uma interface | frontend-specialist → impeccable audit → operação de melhoria pertinente → webapp-testing. |
| Preparar publicação | workflow-test → security-auditor → workflow-deploy check → publicação autorizada. |
| Documentar uma entrega | documentation-writer + documentation-templates; revisar o texto com avoid-ai-writing. |

No router, peça o mesmo objetivo em linguagem natural e deixe o coordenador usar router-coder, router-visual, router-fast e router-assistant, preservando a política desse perfil.

## Onde ficam os recursos depois de instalar

| Recurso | Local global |
|---|---|
| Skills compartilhadas | ~/.gemini/config/skills; expostas também em ~/.claude/skills e ~/.claude/profiles/router/skills. |
| Personas/especialistas | ~/.gemini/config/agents; expostos em ~/.claude/agents. |
| Workflows legados | ~/.gemini/config/global_workflows; expostos em ~/.claude/commands. |
| Agentes router | ~/.claude/profiles/router/agents. |
| Regras gerais | ~/.gemini/GEMINI.md, ~/.claude/CLAUDE.md e o CLAUDE.md do perfil router. |

No Windows, `~` significa a pasta do usuário, indicada por USERPROFILE. No macOS, significa HOME. Links/junctions podem compartilhar conteúdo; não remova essas pastas recursivamente para tentar desinstalar uma skill. Use o registro e o backup do instalador para entender a propriedade dos arquivos.

## Se algo não aparecer ou não funcionar

1. Reabra a sessão depois da instalação e confirme qual perfil foi aberto.
2. No Claude, procure o nome pelo menu `/`; para workflows escolha `workflow-*`.
3. Confira se o SKILL.md ou arquivo de agente existe no local global indicado.
4. Em tarefas do router, peça somente os agentes router-*; o hook recusa os especialistas antigos.
5. Se houver referência a ferramentas ausentes, instale/configure as dependências necessárias ao projeto, ou peça uma abordagem compatível com o ambiente.
6. Confira o relato de execução: ler uma skill ou emitir um plano não comprova teste, deploy ou delegação real.

Voltar ao [README](../README.md) ou aos [prompts de instalação](PROMPT-INSTALACAO.md).
