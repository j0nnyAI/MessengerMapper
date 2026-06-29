---
activation: always_on
nexus_asset: .antigravity/rules.json
cursor_parity: .cursor/rules/00-always.mdc
persona: planner
---

# Nexus spatial invariants — MessengerMapper

Antigravity is blind to Cursor `.mdc` rules. This Always-On rule is the binding spatial map. Machine-readable metrics: `.antigravity/rules.json`.

## Context plane (execution state)

The active workspace token buffer treats **one file** as the execution-state plane:

`../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md` (`context_path`)

At **every session start**, read **only** sections 1–4:

1. `## 1. RUNTIME STATE`
2. `## 2. THE TECHNICAL NARRATIVE`
3. `## 3. ACTIVE CODE DELTAS`
4. `## 4. NEXT IMMEDIATE ACTIONS`

Do not walk other vault paths, run codebase-wide search, or trigger background re-index of vault trees unless the operator explicitly orders it.

**Conditional strategic hydration:** After reading HANDOFF.md §1 — if no active roadmap row is present, OR the operator's first message is strategic/architectural → Read `../MessengerMapper-VAULT/02-ARCHITECTURE/_ARCHITECTURE-INDEX.md` then any ADRs it points to. Load the INDEX only; pull specific docs on demand. If an active roadmap row is present and the query is tactical, skip.

Confirm `../THE-NEXUS/_AI-ENTRY-POINTS/INDEX.md` (`nexus_index`) resolves. If either sentinel is missing, emit verbatim: `Cannot reach <missing path>. Where does it live?` and halt. Silent fallback is forbidden.

On success, emit: `Hydrated on MessengerMapper. Persona: planner. Ready.`

`../THE-NEXUS/01-USER-DATA/IDENTITY.md` and `../THE-NEXUS/` inheritance: **on demand only**.

## Operator command lookup

Remediation, roadmap, audit, and gap-watch intents route per `../THE-NEXUS/_AI-ENTRY-POINTS/AGENTS.md` § Operator command lookup and `../THE-NEXUS/08-DOCS/COMMAND-INDEX.md` § Related operator intents. **Do not duplicate trigger lists here.**

**Phase B (binding):** `resume S-XX` / `OW-XX only` → `../THE-NEXUS/03-SKILLS/resume-roadmap-row.md`. `gaps on` / `enable gaps` / `watch gaps` / `find gaps` (no named scope) → `remediation-gap-watch.md` § **Mandatory cascade**; off: `gaps off`. **`gap analysis on <scope>`** → `ai-tooling-value-audit.md` (Phase A), never gap watch.

## Design-turn buffer discipline

Long design turns must not substitute conversational archaeology for HANDOFF hydration. Before expanding scope, re-read context plane sections 1–4. No parallel state files (`STATUS.md`, `AI-STATE.md`, `SPRINT-LOG.md`, etc.) — `HANDOFF.md` only.

## Communication

Objective systems-engineering tone. No platitudes. One thing at a time; ask before acting; push back with reasons; flag security tradeoffs.

Execution discipline: directives 21–22 in `../THE-NEXUS/01-USER-DATA/IDENTITY.md` § 5 are binding — one logical change per turn, narrate before, summarize after, wait for approval. Scope is not approval: never execute full scope in one pass. Questions and pushback are not approval — answer first, then wait. Surface unexpected findings before continuing.
