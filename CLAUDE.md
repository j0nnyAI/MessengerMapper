<!--
FILE: CLAUDE.md
PURPOSE: Claude Code memory file. @-imports AGENTS.md and adds Claude-specific bootstrap.
LOADS: Auto-loaded by Claude Code at session start (hierarchical).
-->

# CLAUDE.md - MessengerMapper

@./AGENTS.md

## 1. BINDING & ACTIONS
- **Persona:** `surgeon` | [[../THE-NEXUS/02-PERSONAS/surgeon]] (check `../MessengerMapper-VAULT/03-PERSONAS/` for a project override first - see § 3)
- **Signal:** `Hydrated on MessengerMapper. Persona: surgeon. Ready.`
- **Paths:** context=`../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md`, hydration=`../MessengerMapper-VAULT/04-CONTEXT/HYDRATION-NEXT-SESSION.md`, index=`../THE-NEXUS/_AI-ENTRY-POINTS/INDEX.md`
- **Boot:** 1. Read context/hydration targets. 2. Emit Signal after doctor pre-flight passes. 3. Prioritize Active contract row ID/Session notes over loose checkbox tasks.

## 2. SESSION CONSTRAINTS
- Track workspace mutations exclusively via native Git status commands.
- `HANDOFF.md` & `05-MEMORY/` are read-only to AI; updated exclusively by `handoff.py`.
- `HYDRATION-NEXT-SESSION.md` & `handoff_context.md` are AI-owned; compile during COMPILE before Step 1 starts.
- Lifecycle commands (`TEARDOWN` / `FULL_LIFECYCLE`) execute full cascade (COMPILE → STEP 1 → STEP 2 [→ STEP 3]).
- Route operator requests to existing `../THE-NEXUS/03-SKILLS/` modules; do not write or assume un-tracked behaviors.

## 3. PATHS & SPECIFICATION RULES
- Personas: Base `../THE-NEXUS/02-PERSONAS/<slug>.md`. Project overrides load from `../MessengerMapper-VAULT/03-PERSONAS/<slug>.md` (checks `override_type` to extend or replace).
- Skills Index: [[../THE-NEXUS/03-SKILLS/_SKILLS-INDEX]]
- Identity: Authoritative profile at `../THE-NEXUS/01-USER-DATA/IDENTITY.md` (read on demand; adhere to all constraints).

## RELATED
[[AGENTS]] | [[../THE-NEXUS/_AI-ENTRY-POINTS/AI-START-HERE]] | [[../THE-NEXUS/03-SKILLS/context-handoff]] | [[../THE-NEXUS/_AI-ENTRY-POINTS/INDEX]] | [[../THE-NEXUS/08-DOCS/RUNBOOK]]
