# Antigravity Kit — Architecture & Registry

> **Single source of truth.** This file lists every agent, skill, workflow, and script
> that ACTUALLY exists in this global install. The orchestrator and the
> `intelligent-routing` skill MUST route only to entries listed here.
> If it is not in this file, it does not exist — do not reference it.

---

## Global Location

Everything lives under one flat skills directory:

```plaintext
~/.gemini/
├── GEMINI.md                                   # Global brain / rules (this kit)
└── config/
    ├── mcp_config.json                         # Global MCP servers (github, vercel, ...)
    ├── skills/                                 # ALL skills (auto-discovered by Antigravity)
    │   ├── AGENTS.md                           # Canonical behavioral rules (shared)
    │   ├── <28 skill folders>/SKILL.md
    │   └── orchestration-kit/                  # Framework home (a skill itself)
    │       ├── ARCHITECTURE.md                 # This file
    │       ├── SKILL.md                        # Master router
    │       ├── scripts/                        # 4 master validation scripts
    │       └── shared/ui-ux-pro-max/           # Data for the /ui-ux-pro-max workflow
    ├── agents/                                 # 17 specialist personas (sibling of skills/)
    └── global_workflows/                       # 11 slash commands (sibling of skills/)
```

**Path rules.** Paths below are the physical (Antigravity) location. Under Claude Code the
same files resolve through junctions: `~/.claude/skills/` → `~/.gemini/config/skills/`,
`~/.claude/agents/` → `~/.gemini/config/agents/`, `~/.claude/commands/` → `~/.gemini/config/global_workflows/`.
`~/.claude/CLAUDE.md` is NOT a junction: it is Claude Code's own bootstrap (see Model Routing below).

- Skill: `~/.gemini/config/skills/<skill>/SKILL.md`
- Skill script: `~/.gemini/config/skills/<skill>/scripts/<script>.py`
- Agent: `~/.gemini/config/agents/<agent>.md`  *(moved out of orchestration-kit/)*
- Workflow: `~/.gemini/config/global_workflows/<name>.md`  *(moved out of orchestration-kit/)*
- Master script: `~/.gemini/config/skills/orchestration-kit/scripts/<script>.py`

---

## Agents (17)

Specialist personas. Loaded by the router; each declares which skills it uses.

| Agent | Focus | Skills Used |
| --- | --- | --- |
| `orchestrator` | Multi-agent coordination | parallel-agents, behavioral-modes, plan-writing, brainstorming, architecture, clean-code, lint-and-validate, bash-linux |
| `project-planner` | Discovery, task planning | brainstorming, plan-writing, architecture |
| `frontend-specialist` | Web UI/UX | impeccable, design-motion-principles, nextjs-react-expert, tailwind-patterns |
| `backend-specialist` | API, business logic | api-patterns, nodejs-best-practices, database-design |
| `database-architect` | Schema, SQL | database-design |
| `devops-engineer` | CI/CD, deploy, servers | deployment-procedures, server-management |
| `security-auditor` | Security, OWASP | vulnerability-scanner |
| `test-engineer` | Testing strategy, TDD | testing-patterns, webapp-testing |
| `qa-automation-engineer` | E2E, CI pipelines | webapp-testing, testing-patterns |
| `debugger` | Root cause analysis | systematic-debugging |
| `performance-optimizer` | Speed, Web Vitals | performance-profiling |
| `seo-specialist` | Ranking, visibility | seo-fundamentals, avoid-ai-writing |
| `documentation-writer` | Docs (explicit request only) | documentation-templates, avoid-ai-writing |
| `product-manager` | Requirements, user stories | plan-writing, brainstorming |
| `product-owner` | Strategy, backlog, MVP | plan-writing, brainstorming |
| `code-archaeologist` | Legacy code, refactoring | clean-code, code-review-checklist |
| `explorer-agent` | Codebase discovery | — (read-only analysis) |

> **Web = `frontend-specialist`.** There is no mobile/game/pentest agent in this kit.
> Do NOT reference `mobile-developer`, `game-developer`, `penetration-tester`, or `api-designer`.

---

## Skills (28)

Modular knowledge domains. Auto-discovered by Antigravity from their `description`.

### Frontend & UI (4)

| Skill | Description |
| --- | --- |
| `nextjs-react-expert` | React & Next.js performance (Vercel engineering) |
| `tailwind-patterns` | Tailwind CSS v4 — CSS-first config, container queries, tokens |
| `impeccable` | Ultra-premium UI/UX design engine (pbakaus) — has sub-commands |
| `design-motion-principles` | Motion audit (Emil Kowalski, Jakub Krehel, Jhey Tompkins) |

### Backend & Data (3)

| Skill | Description |
| --- | --- |
| `api-patterns` | REST vs GraphQL vs tRPC, versioning, pagination |
| `nodejs-best-practices` | Node.js async, framework selection, security |
| `database-design` | Schema design, indexing, ORM selection, serverless DBs |

### Testing & Quality (4)

| Skill | Description |
| --- | --- |
| `testing-patterns` | Unit, integration, mocking (AAA pattern) |
| `webapp-testing` | E2E, Playwright, deep audits |
| `code-review-checklist` | Code review standards |
| `lint-and-validate` | Linting, type coverage, static analysis |

### Security & Performance (2)

| Skill | Description |
| --- | --- |
| `vulnerability-scanner` | OWASP 2025, supply chain, attack surface |
| `performance-profiling` | Core Web Vitals, profiling, Lighthouse |

### Architecture & Planning (5)

| Skill | Description |
| --- | --- |
| `app-builder` | Full-stack scaffolding (13 templates) |
| `architecture` | ADR, trade-off analysis, system design |
| `plan-writing` | Structured task planning |
| `brainstorming` | Socratic questioning protocol (MANDATORY gate) |
| `intelligent-routing` | Auto agent selection (the router itself) |

### Infra & Shell (3)

| Skill | Description |
| --- | --- |
| `deployment-procedures` | Safe deploy, rollback, verification |
| `server-management` | Process management, monitoring, scaling |
| `bash-linux` | Linux commands, piping, scripting |

### Growth & Docs (2)

| Skill | Description |
| --- | --- |
| `seo-fundamentals` | SEO, E-E-A-T, Core Web Vitals |
| `documentation-templates` | README, API docs, changelog formats |

### Writing & Content (1)

| Skill | Description |
| --- | --- |
| `avoid-ai-writing` | Audit/rewrite human-facing text to remove AI-isms (site copy, CTAs, posts, emails, README). GLOBAL rule in AGENTS.md → "Writing Quality". Used by `seo-specialist`, `documentation-writer`, and `frontend-specialist` (for page copy) |

### Global Behavior (4)

| Skill | Description |
| --- | --- |
| `clean-code` | Coding standards (GLOBAL — always active) |
| `behavioral-modes` | Operational modes (brainstorm/implement/debug/review/teach/ship) |
| `parallel-agents` | Multi-agent orchestration patterns |
| `systematic-debugging` | 4-phase debugging methodology |

---

## Workflows (11)

Slash commands. Invoke with `/command`.

| Command | Description |
| --- | --- |
| `/brainstorm` | Socratic discovery |
| `/create` | Create new feature |
| `/debug` | Debug issue |
| `/deploy` | Deploy application |
| `/enhance` | Improve existing code |
| `/orchestrate` | Multi-agent coordination |
| `/plan` | Task breakdown |
| `/preview` | Preview changes |
| `/status` | Check project status |
| `/test` | Run tests |
| `/ui-ux-pro-max` | Design with the ui-ux-pro-max style/palette/font library |

---

## Scripts

### Master (4) — `~/.gemini/config/skills/orchestration-kit/scripts/`

| Script | Purpose |
| --- | --- |
| `checklist.py` | Priority-based project audit (Security → Lint → Schema → Tests → SEO) |
| `verify_all.py` | Full verification suite before deploy |
| `auto_preview.py` | Launch a preview of the running app |
| `session_manager.py` | Session/state management |

### Skill-level (11) — `~/.gemini/config/skills/<skill>/scripts/`

| Script | Skill | When |
| --- | --- | --- |
| `security_scan.py` | vulnerability-scanner | Always on deploy |
| `api_validator.py` | api-patterns | After API change |
| `schema_validator.py` | database-design | After DB change |
| `lint_runner.py` | lint-and-validate | Every code change |
| `type_coverage.py` | lint-and-validate | After TS change |
| `react_performance_checker.py` | nextjs-react-expert | After component change |
| `convert_rules.py` | nextjs-react-expert | Maintenance |
| `test_runner.py` | testing-patterns | After logic change |
| `playwright_runner.py` | webapp-testing | Before deploy |
| `lighthouse_audit.py` | performance-profiling | Before deploy |
| `seo_checker.py` | seo-fundamentals | After page change |

> Invoke any skill script via `python ~/.gemini/config/skills/<skill>/scripts/<script>.py`.

---

## Model Routing (Claude Code only)

Claude Code triages every task before acting and runs it on `sonnet` (levels 1–3) or
`opus` (levels 4–5) with a matching effort — never Haiku or Fable. Source of truth:
`~/.claude/CLAUDE.md` → section 1A. Every Agent-tool call passes `model` + `effort`.
Antigravity ignores this (model chosen in its own picker).

---

## Skill Loading Protocol

```plaintext
Request → intelligent-routing (pick agent) → read agent .md
       → read agent's "skills:" frontmatter → load each SKILL.md (index first)
       → read only the sections that match the request
```

Skill folder layout:

```plaintext
skill-name/
├── SKILL.md        # (required) metadata + instructions
├── scripts/        # (optional) validation scripts
└── reference/      # (optional) deeper docs (e.g. impeccable/reference/*)
```

---

## Per-Project Context (NOT global)

Two files are project-specific and live in each **project root**, not here:

- `PRODUCT.md` — product context the `impeccable` skill loads (`load-context.mjs`)
- `DESIGN.md` — design tokens the `impeccable` skill loads

Update them per project with `$impeccable teach`. Never store a project's
PRODUCT.md/DESIGN.md in the global kit.

---

## Statistics

| Metric | Value |
| --- | --- |
| Agents | 17 |
| Skills | 28 (+ orchestration-kit) |
| Workflows | 11 |
| Scripts | 4 master + 11 skill-level |
