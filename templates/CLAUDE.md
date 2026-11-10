# CLAUDE.md — Claude Code Global Rules

Regras globais de operação, triagem de modelos e economia de tokens.

---

## 1. Economia de Contexto e Resposta Enxuta (Sempre Ativo)

- **Zero leitura especulativa no Turno 1:** NÃO leia `AGENTS.md`, `ARCHITECTURE.md`, arquivos de agentes (`~/.claude/agents/*.md`) nem índices antes de analisar o pedido. As descrições já estão nas ferramentas `Skill` e `Agent`. Consulte `ARCHITECTURE.md` ou `_INDEX.md` apenas quando a tarefa exigir histórico entre projetos ou validação global.
- **Agrupe ferramentas no mesmo turno (menos turnos = menos `cache_read`):** cada turno extra reenvia todo o contexto acumulado. Quando precisar ler 2+ arquivos (`Read`) ou buscar (`Grep`/`Glob`), chame todos no **mesmo turno** em paralelo. Em ajustes diretos, execute `Edit` e o comando de teste (`Bash`/`PowerShell`) no **mesmo turno**.
- **Leitura cirúrgica:** use `Grep` e `Glob` para localizar símbolos primeiro e `Read` com `offset` e `limit` em arquivos grandes (>200 linhas). Nunca releia um arquivo que já está no contexto e não foi modificado.
- **Diffs em vez de arquivos inteiros:** prefira `Edit` pontual. Ao mostrar mudanças ao usuário, cite apenas o diff ou linhas relevantes, nunca o arquivo inteiro.
- **Estilo de resposta (Lite):** direto ao ponto, sem introdução bajuladora ("Claro!", "Ótima pergunta!"), sem repetir o enunciado e sem resumo longo ao final. Mantenha toda a precisão técnica e gramática normal.
- **Subagentes com disciplina:** NÃO delegue tarefas simples ou edições pequenas a subagentes (cada subagente abre novo contexto). Use subagentes (`Explore` ou `explorer-agent` em `haiku`) apenas para explorar/buscar em muitos arquivos sem poluir a sessão principal, ou quando o usuário pedir paralelismo explicitamente.

---

## 2. Política de Modelos e Esforço (Níveis 0–5)

Padrão da sessão: **`sonnet` com esforço `medium`**. Todos os 4 modelos (`haiku`, `sonnet`, `opus`, `fable`) permanecem disponíveis via `/model`.

| Nível | Tipo de Tarefa | Modelo Recomendado | Effort |
| :---: | --- | --- | :---: |
| **0** | Leitura, busca, inventário, exploração (`Explore` / `explorer-agent`) | `haiku` (`claude-haiku-5-5`) | `low` |
| **1** | Edição simples, copy, CSS/Tailwind, ajuste localizado em 1–2 arquivos | `sonnet` (`claude-sonnet-5-5`) | `low` |
| **2** | Feature padrão, componente React/Next, endpoint, teste unitário, bug comum | `sonnet` (`claude-sonnet-5-5`) | `medium` |
| **3** | Refatoração multi-arquivo moderada, integração de API/banco, E2E | `sonnet` (`claude-sonnet-5-5`) | `high` |
| **4** | Arquitetura complexa, bug difícil entre camadas, auditoria crítica | `opus` (`claude-opus-5-5`) | `high` |
| **5** | Decisão arquitetural crítica, segurança sensível, raciocínio profundo | `opus` (`claude-opus-5-5`) ou `fable` (`claude-fable-5-1`) sob pedido | `xhigh` |

**Regras da política:**
1. **`haiku`** nos agentes só de leitura/busca (`explorer-agent` tem `model: haiku` no frontmatter; ao chamar `Agent` apenas para busca/leitura, passe `model: "haiku"`). Demais subagentes herdam o modelo da sessão (`sonnet`).
2. **`sonnet`** como padrão para implementação (`effort: medium` por padrão; `low` em ajustes triviais e `high` em mudanças multi-arquivo).
3. **`opus`** somente sob pedido do usuário ou em tarefas de Nível 4–5 (sugira em 1 linha antes se a sessão estiver em `sonnet`).
4. **`fable`** somente sob pedido explícito do usuário ou se `opus` em `xhigh` falhar.

---

## 3. Roteamento e Portão Socrático

- Em tarefas de código/design (Nível 3+), anuncie o especialista em 1 linha (`🤖 Applying knowledge of @<agente>...`) e abra `~/.claude/agents/<agente>.md` somente se precisar do protocolo completo daquele agente. Em tarefas simples (Níveis 0–2), resolva direto sem abrir arquivos de agente.
- **Portão Socrático enxuto:** se o pedido tiver ambiguidade real de escopo, arquitetura ou impacto destrutivo, faça até 3 perguntas curtas e objetivas antes de editar arquivos. Se o pedido já especificar arquivo, correção e critério de verificação, execute diretamente sem perguntas burocráticas.

---

## 4. Hábitos de Economia de Tokens para o Dia a Dia

- **`/clear` ao trocar de assunto:** encerre o histórico acumulado assim que concluir uma frente antes de iniciar outra.
- **`/compact <foco>`:** quando o contexto passar de ~50%, compacte indicando o que manter (ex.: `/compact mantenha apenas o plano atual e os diffs pendentes`).
- **Plan Mode em tarefas grandes:** use `/plan` (ou Shift+Tab) antes de mudanças grandes para alinhar arquivos e etapas com baixo consumo.
- **Subagentes para exploração pesada:** peça *"use um subagente Haiku para localizar X"* quando precisar varrer muitos arquivos; mantenha a edição na sessão principal.
- **Visibilidade de consumo:** acompanhe modelo, contexto, custo e cota `5h`/`7d` na status line nativa, use `/usage` ou `/context` na sessão e `npx ccusage@latest daily` / `session` / `blocks` no terminal.
