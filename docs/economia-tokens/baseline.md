# Linha de Base e Custo Fixo de Contexto (`ccusage` + `/context`)

Data da coleta: **2026-11-10** (janela de 30 dias: `2026-10-11` a `2026-11-10`).
Pacote verificado antes da execução: `ccusage@20.0.48` (autor: `ryoppippi`, licença `MIT`, repositório oficial `https://github.com/ccusage/ccusage.git`).

---

## 1. Linha de Base dos Últimos 30 Dias (Passo 1)

### 1.1 Resumo Geral (30 dias)

| Métrica | Valor Medido | Participação |
| --- | ---: | ---: |
| Dias com atividade | 12 dias | — |
| Sessões registradas (`ccusage session`) | 26 sessões | 100,00% |
| **Total de tokens processados** | **1.173.241.048** | **100,00%** |
| Leitura de cache (`cacheReadTokens`) | 1.142.779.290 | 97,40% |
| Criação de cache (`cacheCreationTokens`) | 27.633.049 | 2,36% |
| Saída gerada (`outputTokens`) | 2.691.447 | 0,23% |
| Entrada não cacheada (`inputTokens`) | 137.262 | 0,01% |
| **Custo equivalente de API (USD)** | **$366,16** | **100,00%** |

> **Observação sobre `inputTokens`:** Dos `137.262` tokens de entrada fora de cache, `127.248` vieram de uma única sessão de teste do antigo roteador (`nvidia/nemotron-3-super-120b-a12b:free`). No Claude Code nativo, o `inputTokens` não cacheado foi de apenas `10.014` tokens em 30 dias, pois todo o contexto novo entra como `cacheCreationTokens` (`27,63M`) e é relido a cada turno como `cacheReadTokens` (`1.142,78M`).

### 1.2 Proporção `Cache Read` vs. `Input Novo`

- **Cache Read (`1.142.779.290`) vs. Input Novo (`cacheCreation + input = 27.770.311`):** proporção de **41,15 : 1** (**97,63%** de todo o prompt enviado à API é releitura de cache acumulada ao longo dos turnos).
- **Causa raiz:** cada chamada de ferramenta (`Read`, `Grep`, `PowerShell`, `Agent`) adiciona um turno e reenvia todo o prefixo da sessão (`CLAUDE.md` + descrições de skills/agentes + arquivos lidos + saídas de comandos). Em sessões longas (80–200 turnos) ou com dezenas de subagentes, 1 KB extra no início da sessão é cobrado dezenas ou centenas de vezes como `cacheReadTokens`.

### 1.3 Mistura de Modelos (Últimos 30 Dias)

| Modelo | Tokens Totais | % Tokens | Input | Output | Cache Create | Cache Read | Custo Equiv. (USD) | % Custo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-5-5` | 701.592.673 | 59,80% | 6.270 | 1.881.733 | 15.626.921 | 684.077.749 | $275,36 | 75,20% |
| `claude-sonnet-5-5` | 466.218.674 | 39,74% | 3.702 | 804.339 | 11.838.941 | 453.571.692 | $87,77 | 23,97% |
| `claude-opus-4-8` | 4.746.041 | 0,40% | 22 | 3.218 | 132.517 | 4.610.284 | $2,67 | 0,73% |
| `claude-sonnet-5` | 83.936 | 0,01% | 17 | 4.027 | 22.866 | 57.026 | $0,34 | 0,09% |
| `nemotron-3-super` (legado) | 553.402 | 0,05% | 127.248 | 97.697 | 0 | 328.457 | $0,02 | 0,01% |
| `claude-haiku-5-5` | 46.322 | 0,004% | 3 | 433 | 11.804 | 34.082 | $0,01 | <0,01% |

**Diagnóstico da mistura de modelos:**
1. **Opus representou 59,80% dos tokens e 75,20% do custo ($275,36)** porque estava configurado como modelo padrão (`"model": "opus"`, `"effortLevel": "xhigh"`) em `~/.claude/settings.json`.
2. **Haiku representou apenas 0,004% dos tokens (1 única chamada em 30 dias)** porque `ANTHROPIC_DEFAULT_HAIKU_MODEL` apontava anteriormente para `claude-sonnet-5-5` e os subagentes herdavam Opus/Sonnet.

### 1.4 Consumo Diário (Últimos 30 Dias)

| Data | Input | Output | Cache Create | Cache Read | Total Tokens | Custo (USD) | Modelos Utilizados |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `2026-10-21` | 1.976 | 247.420 | 3.553.172 | 125.915.792 | 129.718.360 | $24,49 | `sonnet-5-5`, `opus-4-8` |
| `2026-10-22` | 665 | 173.440 | 4.041.005 | 150.708.131 | 154.923.241 | $27,26 | `sonnet-5-5`, `opus-4-8` |
| `2026-10-23` | 309 | 178.938 | 1.720.236 | 92.606.872 | 94.506.355 | $35,53 | `opus-5-5`, `sonnet-5-5` |
| `2026-10-24` | 326 | 79.317 | 786.103 | 22.878.831 | 23.744.577 | $10,33 | `opus-5-5` |
| `2026-10-26` | 365 | 164.035 | 909.619 | 50.859.092 | 51.933.111 | $21,04 | `opus-5-5` |
| `2026-10-27` | 2.137 | 491.326 | 5.109.160 | 219.634.093 | 225.236.716 | $75,18 | `opus-5-5`, `sonnet-5-5` |
| `2026-10-28` | 2.238 | 759.222 | 5.657.695 | 258.431.787 | 264.850.942 | $85,91 | `opus-5-5`, `sonnet-5-5` |
| `2026-10-29` | 1.119 | 296.529 | 2.863.947 | 112.192.628 | 115.354.223 | $41,56 | `opus-5-5`, `sonnet-5-5` |
| `2026-10-30` | 380 | 69.342 | 1.145.654 | 53.309.766 | 54.525.142 | $19,65 | `opus-5-5`, `sonnet-5-5` |
| `2026-11-05` | 127.619 | 224.212 | 1.563.489 | 55.128.725 | 57.044.045 | $23,83 | `opus-5-5`, `sonnet-5-5`, `haiku-5-5` |
| `2026-11-06` | 120 | 7.647 | 263.495 | 1.073.571 | 1.344.833 | $1,33 | `opus-5-5`, `sonnet-5` |
| `2026-11-10` | 8 | 19 | 19.474 | 40.002 | 59.503 | $0,05 | `opus-5-5` |

### 1.5 Consumo por Projeto e Top 10 Sessões Mais Caras

*(Nomes de projetos de clientes anonimizados conforme política de repositório público)*

| Projeto (Slug Anonimizado) | Sessões | Total Tokens | % Tokens | Custo Equiv. (USD) | % Custo |
| --- | ---: | ---: | ---: | ---: | ---: |
| `projeto-crm` | 4 | 582.644.914 | 49,66% | $165,36 | 45,16% |
| `projeto-imobiliario` | 3 | 300.696.970 | 25,63% | $97,07 | 26,51% |
| `projeto-servicos-rj` | 10 | 178.937.347 | 15,25% | $58,82 | 16,06% |
| `Claude-Antigravity-Kit` | 5 | 97.439.870 | 8,31% | $40,59 | 11,09% |
| `projeto-apresentacao` | 1 | 12.278.734 | 1,05% | $3,74 | 1,02% |
| `workspace-home` | 2 | 637.338 | 0,05% | $0,35 | 0,10% |
| `projeto-estetica` | 1 | 605.875 | 0,05% | $0,23 | 0,06% |

**Top 10 Sessões Mais Caras:**

| # | Sessão (Prefixo) | Projeto | Última Atividade | Tokens Totais | Cache Read | Output | Custo (USD) |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | `312e366d` | `projeto-crm` | `2026-10-28` | 264.850.942 | 258.431.787 | 759.222 | $85,91 |
| 2 | `fb2df325` | `projeto-imobiliario` | `2026-10-28` | 254.093.649 | 248.105.052 | 562.944 | $78,53 |
| 3 | `14fd808f` | `projeto-crm` | `2026-10-29` | 115.354.223 | 112.192.628 | 296.529 | $41,56 |
| 4 | `bb9c0eeb` | `projeto-crm` | `2026-10-22` | 154.504.462 | 150.340.669 | 170.314 | $27,01 |
| 5 | `21c0bcdd` | `Claude-Antigravity-Kit` | `2026-11-05` | 54.563.749 | 53.033.241 | 115.814 | $21,27 |
| 6 | `40f088ac` | `projeto-crm` | `2026-10-22` | 47.935.287 | 46.519.167 | 80.588 | $10,88 |
| 7 | `636cc1ec` | `projeto-imobiliario` | `2026-10-30` | 43.917.241 | 42.905.331 | 52.893 | $17,21 |
| 8 | `8e1c8883` | `projeto-servicos-rj` | `2026-10-26` | 34.160.209 | 33.437.362 | 109.784 | $12,86 |
| 9 | `4c6201f9` | `Claude-Antigravity-Kit` | `2026-10-22` | 40.316.057 | 39.211.791 | 90.068 | $17,12 |
| 10 | `3279c5eb` | `projeto-servicos-rj` | `2026-10-23` | 30.292.115 | 29.749.259 | 57.105 | $11,29 |

### 1.6 Peso dos Subagentes vs. Sessão Principal

Varredura direta dos arquivos JSONL de histórico em `~/.claude/projects/`:

| Categoria | Arquivos JSONL | Respostas de API (Turnos) | Input | Output | Cache Create | Cache Read | Total de Tokens | % do Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Subagentes (`subagents/*.jsonl`)** | **38** | **3.002** | **6.024** | **351.756** | **16.759.297** | **677.626.485** | **694.743.562** | **59,23%** |
| **Sessões Principais (`*.jsonl`)** | **26** | **1.905** | **67.614** | **2.243.258** | **10.873.752** | **464.942.309** | **478.126.933** | **40,77%** |
| **Total Analisado** | **64** | **4.907** | **73.638** | **2.595.014** | **27.633.049** | **1.142.568.794** | **1.172.870.495** | **100,00%** |

**Descoberta crítica sobre subagentes:**
- **59,23% de todos os tokens de 30 dias (`694,74M` tokens em 3.002 turnos)** foram consumidos por **subagentes**!
- Distribuição de modelos dentro dos subagentes:
  - `claude-opus-5-5`: **1.710 chamadas** (`342.304.922` tokens)
  - `claude-sonnet-5-5`: **1.273 chamadas** (`347.692.599` tokens)
  - `claude-opus-4-8`: **19 chamadas** (`4.746.041` tokens)
  - `claude-haiku-5-5`: **0 chamadas** (`0` tokens)
- Cada subagente iniciado abre uma janela de contexto própria, recarrega o contexto fixo e executava em Opus ou Sonnet mesmo para tarefas mecânicas de leitura/exploração.

---

### 1.7 Tarefa Padrão Repetível — Medição ANTES

Para comparar antes e depois em condições idênticas, foi definida uma tarefa padrão automatizada:
- **Ambiente de teste isolado:** diretório temporário contendo `calc.py` (com bug de desconto percentual e de frete grátis após desconto), `test_calc.py` (3 testes `unittest`), além de pastas de ruído (`node_modules/fake-pkg/index.js` e `dist/bundle.min.js`).
- **Prompt exato:** `"Corrija o bug em calc.py para que os testes em test_calc.py passem. Rode python -m unittest test_calc.py para confirmar e responda em no maximo 2 frases."`
- **Execução:** `claude -p "<prompt>" --output-format json --no-session-persistence --dangerously-skip-permissions`

**Resultado medido ANTES e DEPOIS das alterações (mesma tarefa, cache frio):**

| Métrica da Tarefa Padrão | 1. ANTES (`settings.json` em disco: `opus` `xhigh`) | 2. ANTES (`sonnet` `medium` c/ contexto antigo) | 3. DEPOIS (`sonnet` `medium` c/ kit otimizado) | Economia vs. `opus xhigh` (1→3) | Economia pura no `sonnet medium` (2→3) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Modelo e esforço | `claude-opus-5-5` (`xhigh`) | `claude-sonnet-5-5` (`medium`) | `claude-sonnet-5-5` (`medium`) | — | — |
| Turnos de API (`num_turns`) | 7 turnos | 6 turnos | 6 turnos | -1 turno | 0 |
| `input_tokens` | 8 | 8 | 6 | -25,0% | -25,0% |
| `cache_creation_input_tokens` | 49.967 | 39.646 | **29.973** | **-40,0%** | **-24,4% (-9.673 tok)** |
| `cache_read_input_tokens` | 192.490 | 167.621 | **101.406** | **-47,3%** | **-39,5% (-66.215 tok)** |
| `output_tokens` | 1.362 | 1.064 | **999** | **-26,7%** | **-6,1%** |
| **Total de tokens da tarefa** | **243.827 tokens** | **208.339 tokens** | **132.384 tokens** | **-45,7% (-111.443 tok)** | **-36,5% (-75.955 tok)** |
| **Custo equivalente (USD)** | **$0,4655** | **$0,1860** | **$0,1400** *(cache quente: **$0,0237**)* | **-69,9% (-$0,3255)** | **-24,7% (-$0,0460)** |
| Tempo de execução (`duration_ms`) | 23.512 ms | 17.200 ms | **15.100 ms** | **-35,8%** | **-12,2%** |
| Status dos testes (`unittest`) | `OK` (3/3) | `OK` (3/3) | `OK` (3/3) | — | — |

> **De onde veio o `opus` `xhigh` e quanto vem de cada mudança?**
> 1. **Origem do `opus` `xhigh`:** em `~/.claude/settings.json`, o bloco `modelSettings["claude-sonnet-5-5"]` já tinha `"effortLevel": "medium"`, mas o topo do arquivo tinha `"model": "opus"` (linha 40) e `"effortLevel": "xhigh"` (linha 62), fazendo sessões novas sem flag abrirem em Opus `xhigh`.
> 2. **Parcela da troca de modelo (`opus xhigh` → `sonnet medium`):** no contexto antigo, trocar de Opus `xhigh` para Sonnet `medium` reduziu os tokens de `243.827` para `208.339` (**-14,6%** em tokens, pois parou de fazer 1 turno extra de leitura) e o custo de `$0,4655` para `$0,1860` (**-60,0%** pelo preço menor do Sonnet e menos tokens de thinking).
> 3. **Parcela exclusiva da limpeza de contexto e instruções (mesmo modelo `sonnet medium` antes vs. depois):** mantendo exatamente `claude-sonnet-5-5` em `medium`, deduplicar o `~/.claude/CLAUDE.md`, eliminar a leitura obrigatória de `AGENTS.md`/`ARCHITECTURE.md`/`_INDEX.md` no Turno 1 e enxugar as 69 descrições reduziu os tokens da tarefa de **`208.339` para `132.384` (-36,5% / `-75.955` tokens)** e o `cache_read` de **`167.621` para `101.406` (-39,5%)**.

---

## 2. Custo Fixo de Contexto por Sessão (Passo 2)

### 2.1 Medição Real via `/context` e Captura do Payload de Turno 1

Saída medida com `claude -p "/context" --no-session-persistence` no diretório do repositório (janela de 250k tokens):

| Categoria (`/context`) | Tokens Ativos (Turno 1) | % da Janela (250k) | Caracteres Brutos no Payload | Observações |
| --- | ---: | ---: | ---: | --- |
| **Skills (frontmatter listado)** | **9.900** | 4,0% | 28.262 chars | 68 skills listadas (`30` do kit + `11` commands legados + `20` claude.ai + `12` built-in + `6` plugins; `11` `workflow-*` ocultas com `disable-model-invocation: true`) |
| **Memory files (`CLAUDE.md` + `AGENTS.md`)** | **9.500** | 3,8% | 24.640 chars | `~/.claude/CLAUDE.md` (`9.0k` tok / `22.974` chars — duplicado!) + `AGENTS.md` (`449` tok / `1.446` chars) + `MEMORY.md` (`60` tok) |
| **System tools (15 ferramentas nativas)** | **3.600** | 1,4% | 43.320 chars | `Agent`, `PowerShell`, `Read`, `Edit`, `Write`, `Grep`, `Glob`, `Skill`, `ToolSearch`, etc. (+ `14,2k` tok diferidos) |
| **System prompt** | **2.600** | 1,0% | 6.910 chars | Prompt base nativo do Claude Code |
| **MCP server instructions** | **2.300** | 0,9% | ~6.800 chars | Instruções de 10 conectores remotos (`claude.ai`) |
| **Custom agents (17 do kit + 5 plugin)** | **1.900** | 0,8% | 5.120 chars | 17 agentes do kit (`1.546` tok / `3.875` chars) + 5 agentes `edit-labs-ai` (`345` tok) |
| **MCP tools (nomes diferidos)** | **618** | 0,2% | ~2.400 chars | 224 ferramentas remotas diferidas via `ToolSearch` (`206,0k` tok se carregadas) |
| **Hooks ativos** | **0** | 0,0% | 0 chars | Nenhum hook ativo após remoção do router |
| **TOTAL FIXO NO TURNO 1** | **30.500** | **12,2%** | **117.508 bytes** | **+ `10.200` tokens extras lidos no Turno 1–2 pela regra obrigatória da Seção 0 (`AGENTS.md` + `ARCHITECTURE.md` + `_INDEX.md`) = `~40.700` tokens reais** |

### 2.2 Tamanho dos Arquivos de Memória (`CLAUDE.md` / `AGENTS.md`)

| Arquivo | Linhas | Caracteres | Tokens Estimados | Diagnóstico |
| --- | ---: | ---: | ---: | --- |
| `~/.claude/CLAUDE.md` (instalado) | 399 | 22.974 | ~9.000 | **Duplicado:** contém `12.561` chars fora dos marcadores `<!-- claude-openrouter-kit:start -->` e outra cópia quase idêntica de `10.413` chars dentro dos marcadores |
| `templates/CLAUDE.md` (no kit) | 182 | 10.341 | ~3.900 | Muito extenso; repete tabela de 17 agentes (já presente na descrição da ferramenta `Agent`) e obriga leitura de 3 arquivos no Turno 1 |
| `bundle/skills/AGENTS.md` (lido no Turno 1) | 228 | 11.047 | ~3.800 | Lido integralmente no início de toda conversa por ordem da Seção 0 |
| `bundle/skills/orchestration-kit/ARCHITECTURE.md` (lido no Turno 1) | 229 | 10.332 | ~3.600 | Lido integralmente no início de toda conversa por ordem da Seção 0 |
| `AGENTS.md` (deste repositório) | 16 | 1.446 | 449 | Enxuto e objetivo |
| `CLAUDE.md` / `AGENTS.md` de outros projetos locais | 5 a 137 | 325 a 5.059 | 110 a 1.650 | Bem dimensionados (média de ~2,1k chars) |

### 2.3 Quantidade e Tamanho de Skills, Agentes, Workflows, MCPs, Plugins e Hooks

- **Skills do Kit (`bundle/skills/*/SKILL.md`):** 41 pastas no total:
  - 30 skills de domínio ativas no prompt (`disable-model-invocation: false`): **`8.697` caracteres** de descrição (`~3.190` tokens no `/context`). As 10 maiores descrições (`impeccable` 772c, `scrapling` 706c, `nextjs-react-expert` 447c, `testing-patterns` 408c, `seo-fundamentals` 400c, `performance-profiling` 391c, `webapp-testing` 383c, `code-review-checklist` 382c, `documentation-templates` 372c, `orchestration-kit` 370c) somam sozinhas `4.631` caracteres (**53,2%** do total das 30 skills).
  - 11 skills `workflow-*` (`disable-model-invocation: true`): `564` caracteres no arquivo, mas **0 tokens** na listagem de skills do modelo.
- **Workflows Legados (`bundle/global_workflows/*.md` -> `~/.claude/commands/`):** 11 arquivos somando **`1.023` caracteres** (`~380` tokens). Como não têm `disable-model-invocation: true`, aparecem duplicados na lista do `Skill` tool ao lado das skills do kit.
- **Agentes do Kit (`bundle/agents/*.md`):** 17 arquivos somando **`3.875` caracteres** de descrição (`~1.546` tokens na ferramenta `Agent`).
- **Skills Sincronizadas da Conta (`claude.ai`):** 20 skills remotas somando **`10.879` caracteres** (`~3.420` tokens).
- **Plugins Instalados (`enabledPlugins` em `~/.claude/settings.json`):**
  - `edit-labs-ai@edit-labs-ai`: adiciona 5 skills (`~823` tokens) + 5 agentes (`~345` tokens) = **`~1.168` tokens/sessão**.
  - `ui-ux-pro-max@ui-ux-pro-max-skill`: adiciona 1 skill (`~167` tokens).
- **Servidores MCP (`claude.ai` Connectors):** 10 servidores conectados (`Claude_Docs`, `Gmail`, `Google_Calendar`, `Google_Docs`, `Google_Drive`, `Google_Sheets`, `Google_Slides`, `Hostinger_Mail`, `Miro`, `Notion`) com 224 ferramentas diferidas (`2.300` tokens de instruções + `618` tokens de listagem = **`2.918` tokens ativos/sessão**, mais `206.000` tokens diferidos).

---

### 2.4 Os 10 Maiores Consumidores Fixos de Contexto e Cortes Propostos

| # | Consumidor Fixo | Custo Atual por Sessão | Ação / Corte Proposto | Economia Estimada por Turno |
| --- | --- | --- | --- | --- |
| **1** | **Leitura obrigatória no Turno 1 (`AGENTS.md` + `ARCHITECTURE.md` + `_INDEX.md`)** exigida pela Seção 0 do `CLAUDE.md` | **~10.200 tokens** (carregados nos Turnos 1–2 de toda sessão) | Remover a leitura obrigatória prévia no Turno 1; manter regras essenciais direto no `CLAUDE.md` enxuto e consultar `ARCHITECTURE.md` / `_INDEX.md` apenas sob demanda | **~10.200 tokens/turno** após o Turno 1 |
| **2** | **Duplicação em `~/.claude/CLAUDE.md`** (bloco antigo de `12.561` chars fora dos marcadores + bloco gerenciado de `10.413` chars) | **9.000 tokens** (`22.974` chars) | Deduplicar `~/.claude/CLAUDE.md` no `install.py` (preservando o cabeçalho pessoal do usuário) e enxugar `templates/CLAUDE.md` de `10.341` chars para `~2.400` chars | **~7.800 tokens/turno** (`9.0k` → `~1.2k`) |
| **3** | **30 descrições de skills do kit em `bundle/skills/*/SKILL.md`** (`impeccable` 772c, `scrapling` 706c, etc.) | **~3.190 tokens** (`8.697` chars de descrição) | Reescrever todas as descrições para 1–2 frases (`110–150` chars), iniciando com `"Use quando..."` e gatilhos reais sem competição (Passo 5) | **~1.750 tokens/turno** (`8.697` → `~3.800` chars) |
| **4** | **17 descrições de agentes em `bundle/agents/*.md`** + tabela duplicada de 17 agentes no `CLAUDE.md` | **~1.546 tokens** (`3.875` chars) + **~650 tokens** no `CLAUDE.md` | Enxugar as 17 descrições de agentes para 1–2 frases (`Use quando...`) sem conflitos e remover a tabela duplicada do `CLAUDE.md` | **~1.300 tokens/turno** |
| **5** | **11 comandos legados em `bundle/global_workflows/*.md`** duplicando as 11 skills `workflow-*` na ferramenta `Skill` | **~380 tokens** (`1.023` chars) | Adicionar `disable-model-invocation: true` aos 11 arquivos de `bundle/global_workflows/*.md` (continuam funcionando via `/plan`, `/create`, etc., mas saem do prompt fixo) e revisar suas descrições | **~380 tokens/turno** (100% removido do prompt do modelo) |
| **6** | **Topo do `settings.json` em `opus` + `effortLevel: xhigh` + `explorer-agent` sem Haiku** | Multiplicador de **2,5x no custo** e tokens extras de thinking | Definir `sonnet` e `effortLevel: "medium"` no topo do `settings.json`, configurar `model: haiku` no frontmatter de `explorer-agent` (sem forçar variável global nos demais subagentes) e manter `opus`/`fable` sob pedido ou nível 4–5 | Redução de **~60%** no custo por token quando comparado a Opus |
| **7** | **Leitura acidental de pastas geradas e bundles minificados** (`node_modules`, `.next`, `dist`, `build`, `*.map`, `*.min.js`) | **5.000 a 80.000 tokens** quando lidos em sessão | Configurar `permissions.deny` em `~/.claude/settings.json` via `install.py` bloqueando `Read` em `node_modules`, `.next`, `dist`, `build`, `*.map` e `*.min.js` (mantendo `*.log` e lockfiles liberados para diagnóstico) | Evita picos de **10k–80k tokens** |
| **8** | **20 skills sincronizadas do `claude.ai`** (`10.879` chars) | **~3.420 tokens** | Fora do repositório do kit (vêm da conta `claude.ai`), mas documentado: desativar na web do `claude.ai` as skills remotas que não forem usadas no CLI | Até **~2.000 tokens/turno** (opcional pelo painel web) |
| **9** | **10 conectores MCP remotos do `claude.ai`** (`Gmail`, `Google_Drive`, `Miro`, `Notion`, `Hostinger_Mail`, etc.) | **~2.918 tokens** ativos (`2.3k` instruções + `618` tools) | Fora do repositório do kit; recomendação documentada: manter conectados no `claude.ai` apenas os MCPs usados no dia a dia | Até **~2.000 tokens/turno** (opcional pelo painel web) |
| **10** | **Plugins externos em `enabledPlugins`** (`edit-labs-ai` + `ui-ux-pro-max-skill`) | **~1.335 tokens** (6 skills + 5 agentes) | `ui-ux-pro-max` já existe no próprio kit (`/ui-ux-pro-max`); documentado como opcional caso o usuário queira desabilitar plugins redundantes | Até **~1.335 tokens/turno** (opcional) |

**Resumo do corte medido via `/context` (ANTES vs. DEPOIS da instalação global):**

| Categoria do `/context` | ANTES (Tokens) | DEPOIS (Tokens) | Diferença Medida |
| --- | ---: | ---: | ---: |
| `Memory files` (`~/.claude/CLAUDE.md` + `AGENTS.md`) | 9.500 | **3.000** | **-6.500 tok (-68,4%)** |
| `Skills` (todas as skills ativas) | 9.900 | **8.700** | **-1.200 tok (-12,1% geral / -49,3% nas skills do kit)** |
| `Custom agents` (17 do kit + 5 plugin) | 1.900 | **1.500** | **-400 tok (-21,1%)** |
| Outros fixos (`System prompt`, `System tools`, `MCP`) | 9.200 | 10.300 | +1.100 tok *(variação do prompt nativo Sonnet vs Opus)* |
| **Total `/context` no Turno 1** | **30.500** | **23.500** | **-7.000 tok (-23,0%)** |
| Leitura obrigatória no Turno 1 (`AGENTS.md` + `ARCHITECTURE.md` + `_INDEX.md`) | **+10.200** | **0** | **-10.200 tok (-100,0%)** |
| **CONTEXTO INICIAL EFETIVO (Turno 1–2)** | **~40.700** | **23.500** | **-17.200 tok (-42,3%)** |

