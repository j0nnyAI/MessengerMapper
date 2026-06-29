<!--
FILE: NEXUS-CONTEXT.md
PURPOSE: Spatial orientation for any AI agent opening this workspace cold.
         You are inside a Nexus project. Two sibling folders exist next door.
         This file tells you what they are and what lives where.
         Read this before exploring the filesystem.
READ BY: All AI agents — cold-start, any tool (Claude Code, Cursor, Gemini, Antigravity).
DO NOT WRITE HERE: Operational contracts live in AGENTS.md. Session state lives in the vault.
-->

# Nexus Context — MessengerMapper

## You are here

You are inside `MessengerMapper/` — the code workspace for a Nexus project.

Two sibling folders exist at the same directory level as this one:

```
workspace-root/
├── THE-NEXUS/               ← Engine: tools, scripts, personas, skills, standards
├── MessengerMapper/        ← You are here: source code + AI config
└── MessengerMapper-VAULT/  ← Brain: session state, memory, decisions, plans
```

These three folders are always siblings. Never nested.

---

## What each sibling does

### `../THE-NEXUS/`

The engine. Contains everything that makes this project Nexus-aware. You reach it for:

- Personas: `../THE-NEXUS/02-PERSONAS/<name>.md`
- Skills: `../THE-NEXUS/03-SKILLS/<name>.md`
- Operator manuals: `../THE-NEXUS/08-DOCS/`
- Scripts: `../THE-NEXUS/scripts/` (`nexus.py`, `handoff.py`, `doctor.py`, etc.)
- Standards: `../THE-NEXUS/04-STANDARDS/`

Do not modify THE-NEXUS during project work. It is tooling, not the work surface.

### `../MessengerMapper-VAULT/`

The brain. Private — never version-controlled. You read and write here for all context and memory:

- Session state: `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md` — read this first every session
- Hydration context: `../MessengerMapper-VAULT/04-CONTEXT/HYDRATION-NEXT-SESSION.md`
- Plans: `../MessengerMapper-VAULT/06-PLANS/active/`
- Architecture docs: `../MessengerMapper-VAULT/02-ARCHITECTURE/`
- Roadmaps: `../MessengerMapper-VAULT/16-ROADMAPS/`
- Audit findings: `../MessengerMapper-VAULT/14-AUDITS/`

---

## First action every session

Read `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md`. Full contract: `./AGENTS.md § First action`.

---

## Further reading

- `./AGENTS.md` — operational contract: entry parameters, lifecycle triggers, CLI commands, persona resolution
- `../THE-NEXUS/08-DOCS/PROJECT-ARCH.md` — full three-folder model specification
- `../MessengerMapper-VAULT/_AI-ENTRY-POINTS/AI-START-HERE.md` — vault cold-start reference
