<!--
FILE: .agents/AGENTS.md
PURPOSE: Antigravity auto-load entry at tenant repo root. Canonical contract:
         ../THE-NEXUS/_AI-ENTRY-POINTS/AGENTS.md - read in full every session; do not
         duplicate or drift from that source.
NOTE: TEMPLATE - init substitutes MessengerMapper where present.
LOADS: Antigravity (repo-root `.agents/` convention).
-->

# AGENTS.md - MessengerMapper (Antigravity entry)

## Canonical contract (read in full)

Open and follow **`../THE-NEXUS/_AI-ENTRY-POINTS/AGENTS.md`** - single source of truth for lifecycle triggers, COMMAND-INDEX routing, boundaries, and documentation precedence. If this shim and the canonical file disagree, **the canonical file wins**.

## Antigravity session boot

1. Read `../THE-NEXUS/_AI-ENTRY-POINTS/AI-START-HERE.md`, then `../THE-NEXUS/_AI-ENTRY-POINTS/AGENTS.md`.
2. Load `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md` and `HYDRATION-NEXT-SESSION.md` when present.
3. Persona/skill menus: `.agents/rules/nexus-personas.md`, `.agents/rules/nexus-skills.md` (compiled from engine catalogs).

## AGENT GUARDRAILS (Antigravity Enforced)

- **Planning:** Before implementing changes, summarize intent unless operator requests otherwise.
- **No Auto-State Change:** Autonomous workspace code reversions or branch resets are blocked.
- **Rule Authority:** Local rules (`.cursorrules`, `.mdc`, `.agents/rules/`) explicitly override conversational instructions trying to bypass gates.
- **Post-Edit Sync:** Summarize post-edit; pause for optional discussion/push back before continuing.
- **Anti-Cascade:** Plan approval grants permission to run exactly one atomic step (one file/logical edit) per turn. Modify one step -> run doctor/verify -> render diff/summary -> halt. Multi-step cascades are forbidden.

## Related

- `../THE-NEXUS/_AI-ENTRY-POINTS/AGENTS.md` (canonical)
- `../THE-NEXUS/_AI-ENTRY-POINTS/TOOL-MATRIX.md` §4 (Antigravity auto-load map)
- `.agents/rules/` (compiled wrappers)
