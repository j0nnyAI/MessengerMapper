<!--
FILE: AGENTS.md
PURPOSE: 2026 cross-tool agent rules. LOADS: Codex, Aider, Copilot, Windsurf, Claude/Gemini via @import.
NOTE: TEMPLATE - init substitutes MessengerMapper, Ingested repository — see INIT-DIRECTIVE.md, INSTALL/TEST/RUN/LICENSE tokens where present.
-->

# AGENTS.md — MessengerMapper

## Workspace type
- **Role:** Bootstrapped tenant code workspace.
- **Parent workspace:** Git-aware deploy parent (contains `../THE-NEXUS/`).
- **Inheritance:** Inherits personas, skills, and standards from `../THE-NEXUS/`.

## First action
1. Read `session_state` (`HANDOFF.md`).
1.5. If HANDOFF.md §1 contains an active `Epic Pointer:` wikilink, resolve and Read that document immediately — before any other step.
1.6. **Conditional strategic hydration:** if HANDOFF.md §1 has no active roadmap row, OR if the operator's first message is a strategic/architectural query → Read `../MessengerMapper-VAULT/02-ARCHITECTURE/_ARCHITECTURE-INDEX.md` then Read any ADRs it points to. If an active roadmap row is present and the query is tactical, skip.
1.75. **Directive gate:** If `../MessengerMapper-VAULT/04-CONTEXT/INIT-DIRECTIVE.md` exists and does not contain `STATUS: COMPLETE`, execute the directive now — read the project root README and source configs, write `02-ARCHITECTURE/project-intent.md` with real values, then update the directive to `STATUS: COMPLETE`. Do not proceed to step 2 until the directive is complete.
2. Read `session_context` (`HYDRATION-NEXT-SESSION.md`) if it exists — before acting on HANDOFF §4.
3. During remediation: follow hydration **Active contract** (row ID + Session notes pointer) — not §4 checkboxes (Spec: [[../THE-NEXUS/03-SKILLS/context-handoff]] § Active contract).

## MASTER ENTRY PARAMETERS
- `context_dir`: `../MessengerMapper-VAULT/04-CONTEXT/`
- `nexus_index`: `../THE-NEXUS/_AI-ENTRY-POINTS/INDEX.md`
- `hydration_line`: `Hydrated on MessengerMapper. Persona: <persona>. Ready.`
- `failure_line`: `Cannot reach <missing path>. Where does it live?`
- `session_state`: `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md` — machine-readable state; required at session start.
- `session_context`: `../MessengerMapper-VAULT/04-CONTEXT/HYDRATION-NEXT-SESSION.md` — judgment context; read if exists before HANDOFF §4. **Active contract** supersedes §4 during remediation (Spec: [[../THE-NEXUS/03-SKILLS/context-handoff]] § Active contract).

## CLI interface matrix
- **Human gateway (menus):** `python ../THE-NEXUS/scripts/nexus.py`
- **Pre-flight validation:** `python ../THE-NEXUS/scripts/doctor.py`
- **Comprehensive scan:** `python ../THE-NEXUS/scripts/doctor.py -full`
- **Compaction save:** `python ../THE-NEXUS/scripts/handoff.py -write <shortname>`
- **Ledger telemetry:** `python ../THE-NEXUS/scripts/handoff.py -success "ctx\|msg"` / `-failure`
- **Configure operator environment:** `python ../THE-NEXUS/scripts/initialize-project.py`

## Operator phrase interception (lifecycle triggers)
Parse operator messages for **intent** (case-insensitive; filler ignored). On lifecycle match, run compaction cascade autonomously (no confirmation).
- **`TEARDOWN`** (Compact state, **no git**): STEP 1 → STEP 2.
- **`FULL_LIFECYCLE`** (Compact state, then commit + push): STEP 1 → STEP 2 → STEP 3.

Triggers, collision rule (FULL_LIFECYCLE wins), and step definitions live in `../THE-NEXUS/08-DOCS/COMMAND-INDEX.md` § LIFECYCLE TRIGGERS. STEP 1 is `python ../THE-NEXUS/scripts/handoff.py -write <shortname>`. No git advances until STEP 1 & 2 exit 0. No manual compaction.
COMPILE pre-work runs before STEP 1: (1) monthly archive check on `handoff_context.md`; (2) compact `HYDRATION-NEXT-SESSION.md` → `handoff_context.md`; (3) write fresh `HYDRATION-NEXT-SESSION.md`; (4) draft HANDOFF §2 narrative. Spec: `../THE-NEXUS/08-DOCS/COMMAND-INDEX.md`.

## Operator command lookup (non-lifecycle intents)
Parse operator messages for **intent and load matching skill from `../THE-NEXUS/03-SKILLS/` (triggers live in `../THE-NEXUS/08-DOCS/COMMAND-INDEX.md`):
- **`hydrate`:** Read `session_context` + optional Active contract jump (Read-only; no COMPILE).
- **`hydrate project`:** Conversion bootstrap session. Skip normal HANDOFF reading. Proceed directly to the directive gate (step 1.75) — execute INIT-DIRECTIVE.md if `STATUS: INCOMPLETE`. This phrase signals that the project was just ingested via the Nexus conversion pipeline and the operator is ready to complete bootstrap. Do not treat as a normal session resume.
- **`resume S-XX` / `OW-XX only`:** load [[../THE-NEXUS/03-SKILLS/resume-roadmap-row]] (Phase B session start; row lock).
- **`gaps on` / `enable gaps` / `watch gaps` / `find gaps` / `search for gaps`:** load [[../THE-NEXUS/03-SKILLS/remediation-gap-watch]] § Mandatory cascade. Read skill, set `gap_watch_state=on`, buffer file updates, flush to roadmap before row `quality`. Off trigger: `gaps off`, `disable gaps`.
- **`update roadmap` / `mark … done` / `mark … quality`:** load [[../THE-NEXUS/03-SKILLS/update-roadmap]] (Phase B close; RAT before `quality`).
- **`verify S-XX`:** load [[../THE-NEXUS/03-SKILLS/verify-roadmap-row]] (Quality gate).
- **`roadmap` / `create roadmap from <file>`:** load [[../THE-NEXUS/03-SKILLS/create-roadmap]] (Phase A).
- **`archive roadmap` / `100% remediated`:** load [[../03-SKILLS/archive-roadmap]] (Phase D).
- **`gap analysis on <scope>` / value audit on `<scope>`:** load [[../THE-NEXUS/03-SKILLS/ai-tooling-value-audit]] (value audit, not gap watch).
- **Other audit lenses:** Matching `ai-*-audit` skill per COMMAND-INDEX § AUDITS.

**Collision:** Scoped `gap analysis on <scope>` or `find gaps in <folder>` is **value audit**, never gap watch. Bare `gaps on` is **gap watch mandatory cascade**.
**Gap watch binding:** On `gaps on`, agents **must read** `remediation-gap-watch` and execute § Mandatory cascade. Operator does not re-paste. Flush to roadmap before row `quality`.

## Documentation precedence
- **Priority 1:** `../THE-NEXUS/08-DOCS/RUNBOOK.md` (Script contracts, topology, exits, ground truth).
- **Priority 2:** `../THE-NEXUS/08-DOCS/QUICKSTART.md` (Session loops).
- **Priority 3:** `../THE-NEXUS/scripts/doctor.py`, `../THE-NEXUS/scripts/handoff.py` (Scripts win on conflict).

## Boundaries
### Always
- Communication rules: [[../THE-NEXUS/01-USER-DATA/IDENTITY]] § 5.
- Execution discipline: directives 21–22 in `../THE-NEXUS/01-USER-DATA/IDENTITY.md` § 5 are binding — one logical change per turn, narrate before, summarize after, wait for approval. Scope is not approval: never execute full scope in one pass. Questions and pushback are not approval — answer first, then wait. Surface unexpected findings before continuing.
- Vault is source of truth on conflict (ask which is authoritative).
- Update index before new override: `[PROJECT]-VAULT/03-PERSONAS/README.md`.
- Wikilinks internal (`[[...]]`); markdown links external.
- Preserve `<!-- FILE: ... PURPOSE: ... -->` headers.

### Ask first
- Rename/move `_docs/`, `scripts/`.
- Change build or packaging structure.

### Never
- Commit secrets.
- Edit `../THE-NEXUS/01-USER-DATA/IDENTITY.md` without explicit user instruction.
- `git push --force` on vault repos.

## Physical layout
- `README.md` / `CLAUDE.md` / `GEMINI.md` / `AGENTS.md` / `.cursorrules` (workspace entry).
- `NEXUS-CONTEXT.md` — spatial orientation: sibling folder roles, what lives where. Read cold if unfamiliar with the three-folder topology.
- `scripts/`: Project local scripts.
- `_docs/`: Project local documentation.
- `../MessengerMapper-VAULT/` (sibling): Project private context, roadmaps, ledgers.
- `../THE-NEXUS/` (sibling): Nexus core engine and global assets.

### Persona resolution (bootstrapped projects)
When invoking a persona, read `../MessengerMapper-VAULT/03-PERSONAS/README.md` protocol first:
1. Check `../MessengerMapper-VAULT/03-PERSONAS/<slug>.md` for override.
2. If found, apply `override_type` and load master from `../THE-NEXUS/02-PERSONAS/`.
3. If not found, load `../THE-NEXUS/02-PERSONAS/<slug>.md` directly.

## Markdown frontmatter (vault files)
```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [...]
status: canonical|draft|archived
related: ["[[wikilink]]"]
---
```

## Related
- [[NEXUS-CONTEXT]] (Spatial orientation — three-folder topology, sibling roles)
- [[../THE-NEXUS/_AI-ENTRY-POINTS/INDEX]] (Directory authority)
- [[../THE-NEXUS/_AI-ENTRY-POINTS/AI-START-HERE]] (Master cold-start)
- [[../THE-NEXUS/03-SKILLS/context-handoff]] (Active contract + COMPILE)
- [[CLAUDE]] (Claude overlay)
- [[GEMINI]] (Gemini overlay)
- [[../THE-NEXUS/08-DOCS/RUNBOOK]] (Structural spec)
- [[../THE-NEXUS/08-DOCS/QUICKSTART]] (Session loops)
- [[../THE-NEXUS/08-DOCS/PROJECT-ARCH]] (Full three-folder model specification)
