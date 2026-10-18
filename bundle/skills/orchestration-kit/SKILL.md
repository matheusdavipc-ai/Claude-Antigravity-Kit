---
name: orchestration-kit
description: Master router and framework home for the Antigravity Kit. Use to coordinate multiple specialist agents, decide which agent and skills apply to a request, or run project-wide validation. The framework home for the 17 specialist agents and 11 slash-command workflows (which live in sibling directories), plus master validation scripts and the ARCHITECTURE registry. Load this when a task spans multiple domains, needs orchestration, or when you must confirm which agents/skills exist.
---

# Orchestration Kit — Master Router

This folder is the home of the Antigravity Kit framework. It contains the specialist
agents, workflows, scripts, and the canonical registry.

## Before routing anything

1. **Read `ARCHITECTURE.md`** (in this folder) — it is the single source of truth for
   every agent, skill, workflow, and script that exists. Never route to something not
   listed there.
2. **Apply `intelligent-routing`** (skill) to pick the right specialist(s) from the request.
3. **Load the chosen agent** from `<AGENTS_DIR>/<agent>.md`, then read its `skills:` frontmatter
   and load each referenced SKILL.md.

## What lives here

| Resource | Location |
| --- | --- |
| Registry | `<SKILLS>/orchestration-kit/ARCHITECTURE.md` |
| Agents (17) | `<AGENTS_DIR>/<agent>.md`  *(sibling of skills/, not inside orchestration-kit)* |
| Workflows (11) | `<WORKFLOWS_DIR>/<name>.md`  *(sibling of skills/, not inside orchestration-kit)* |
| Master scripts (4) | `<SKILLS>/orchestration-kit/scripts/<script>.py` |
| ui-ux-pro-max data | `<SKILLS>/orchestration-kit/shared/ui-ux-pro-max/` |

> Path tokens (`<SKILLS>`, `<AGENTS_DIR>`, `<WORKFLOWS_DIR>`) resolve per tool — see the
> AGENTS.md path-resolution table.

## Granular skills

The 28 domain skills live as siblings of this folder, directly under
`~/.gemini/config/skills/`. Antigravity auto-discovers them by description. Agents pull
them in via their `skills:` frontmatter. See `ARCHITECTURE.md` for the full list and
the agent↔skill mapping.

## Master validation

```bash
# Quick audit during development
python ~/.gemini/config/skills/orchestration-kit/scripts/checklist.py .

# Full verification before deploy
python ~/.gemini/config/skills/orchestration-kit/scripts/verify_all.py . --url http://localhost:3000
```
