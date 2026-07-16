<!--
FILE: AGENTS.md
PURPOSE: 2026 cross-tool agent rules. LOADS: Codex, Aider, Copilot, Windsurf, Claude via @import; Antigravity via `.agents/AGENTS.md`.
NOTE: TEMPLATE - init substitutes MessengerMapper, Ingested repository — see INIT-DIRECTIVE.md, INSTALL/TEST/RUN/LICENSE tokens where present.
-->

# AGENTS.md - MessengerMapper

## 1. WORKSPACE ANCHORS
- **Role:** Bootstrapped tenant code workspace surface.
- **Parent Workspace:** Git-aware deploy parent layout (contains sibling folder `../THE-NEXUS/`).
- **Inheritance Plane:** Automatically inherits engine personas, procedural skills, and lint standards.
- **Sentinels:**
  - context_dir: `../MessengerMapper-VAULT/04-CONTEXT/`
  - nexus_index: `../THE-NEXUS/_AI-ENTRY-POINTS/INDEX.md`
  - session_state: `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md`
  - session_context: `../MessengerMapper-VAULT/04-CONTEXT/HYDRATION-NEXT-SESSION.md`
  - active_plans_dir: `../MessengerMapper-VAULT/02-ARCHITECTURE/plans/active/` (authoritative on any "direction/roadmap/what's next" query - read before answering, do not rely on memory/recall alone)

## 2. FIRST ACTION (BOOT SEQUENCE)
1. **Load State:** Read `session_state` (`HANDOFF.md`).
   - *Epic Link:* If `HANDOFF.md` §1 contains `Epic Pointer: [[wikilink]]`, resolve and read targeted block immediately.
   - *Strategic Pivot:* If no active roadmap row exists OR query intent is strategic/architectural, immediately parse `../MessengerMapper-VAULT/02-ARCHITECTURE/_ARCHITECTURE-INDEX.md` and referenced ADRs.
2. **Directive Gate:** If `../MessengerMapper-VAULT/04-CONTEXT/INIT-DIRECTIVE.md` exists and reads `STATUS: INCOMPLETE`, immediately halt standard loop, analyze root repository files, write `02-ARCHITECTURE/project-intent.md` specifications, then stamp `STATUS: COMPLETE`. Freeze further logic execution until resolved.
3. **Load Context:** Parse `session_context` (`HYDRATION-NEXT-SESSION.md`) if it exists before executing tasks.
4. **Contract Lock:** Follow roadmap row ID **Active contract** and Session notes pointers exclusively. Ignore generic checkpoint checkboxes under HANDOFF §4.
5. **Signal:** Confirm bootstrap completion based on `HANDOFF.md` §1 **System Baseline Status**:
   - **Stable** or **Degraded:** print verbatim: `Hydrated on MessengerMapper. Persona: <persona>. [Degraded: <note>] Ready.`
   - **Blocked:** do NOT print `Ready.` State the blocker from HANDOFF §4, then ask: `Hydrated on MessengerMapper. Persona: <persona>. BLOCKED: <blocker from §4>. Address the blocker before proceeding, or confirm override?` Do not start new work until the operator responds.

## 3. CONVERSATIONAL INTENT INTERCEPTION
Match inbound operator directives case-insensitively. Clear all fluff. Actions, scripts, and step allocations inherit boundaries from `../THE-NEXUS/08-DOCS/COMMAND-INDEX.md`.
<!-- COMMAND-SURFACE-COVERAGE: checked by asset_parity.py's validate_command_surface_coverage()
     against .agents/asset-parity.manifest.json's commandSurface.requiredClasses - sync-assets-to-template.py
     --check fails loud if a required class phrase goes missing here after a future COMMAND-INDEX growth. -->
- **`handoff`:** Trigger session save pipeline. Run COMPILE, write compaction parameters, **no git operations** (STEP 1 → STEP 2).
- **`FULL_LIFECYCLE`:** Trigger commit + push cascade (COMPILE → STEP 1 → STEP 2 → STEP 3).
- **`hydrate`:** Read `session_context` + look for Active contract row jumps. (Read-only query mode).
- **`hydrate project`:** Conversion bootstrap wake-up. Skip normal state history checks, hop straight to step 2 Directive Gate.
- **`resume S-XX` / `OW-XX only`:** Mount procedural logic node: `../THE-NEXUS/03-SKILLS/resume-roadmap-row.md`.
- **`gaps on` / `enable gaps` / `watch gaps`:** Mount procedural skill node: `../THE-NEXUS/03-SKILLS/remediation-gap-watch.md` § Mandatory cascade.
- **`gaps off` / `disable gaps`:** Clear runtime state gap flags; freeze continuous backlog buffering.
- **`roadmap` / `create roadmap` / `create roadmap from <file>`:** Mount `../THE-NEXUS/03-SKILLS/create-roadmap.md`. Refuses bare `roadmap` when ambiguous (>1 open audit or >1 active roadmap).
- **`validate roadmap` / `validate roadmap <file>`:** Mount `../THE-NEXUS/03-SKILLS/validate-roadmap.md` - read-only CLOSED/OPEN/AMBIGUOUS classification, no writes.
- **`update roadmap` / `mark ... done`:** Mount procedural skill node: `../THE-NEXUS/03-SKILLS/update-roadmap.md`. Run acceptance testing profiles.
- **`verify S-XX`:** Mount quality engineering node: `../THE-NEXUS/03-SKILLS/verify-roadmap-row.md`.
- **`100% remediated` / `archive roadmap`:** Mount `../THE-NEXUS/03-SKILLS/archive-roadmap.md` - atomic retire to `16-ROADMAPS/ARCHIVE/`.
- **`reopen remediation`:** Mount `../THE-NEXUS/06-WORKFLOWS/reopen-remediation.md` - Phase C supersede flow.
- **`gap analysis on <scope>`:** Route intent directly to Phase A value audit module: `../THE-NEXUS/03-SKILLS/ai-tooling-value-audit.md`.
- **`run an audit` / `audit <X>`:** Bind the matching persona + lens per `../THE-NEXUS/08-DOCS/COMMAND-INDEX.md` § AUDITS; do not answer ad hoc.
- **`create ADR` / `create ADR <title>`:** Write a new decision record to `../MessengerMapper-VAULT/02-ARCHITECTURE/decisions/`; mandatory `_ARCHITECTURE-INDEX.md` row before session close.
- **`create architecture note` / `add a note`:** Provision a design ledger stub in `../MessengerMapper-VAULT/02-ARCHITECTURE/notes/`; mandatory index rows in `_ARCHITECTURE-INDEX.md` and `notes/_NOTES-INDEX.md` before session close.
- **`create a spec` / `write a spec` / `spec this out`:** Mount `../THE-NEXUS/03-SKILLS/writing-specs.md`; write-only to `../MessengerMapper-VAULT/02-ARCHITECTURE/specs/`.
- **`live test` / `field test` / `start a test run`:** Mount `../THE-NEXUS/03-SKILLS/live-test-intake.md`; refuses if an `active` run already exists.
- **`capture intent` / `note design direction`:** Open `../MessengerMapper-VAULT/02-ARCHITECTURE/_ARCHITECTURE-INDEX.md`, create/update decision blueprint under `decisions/`, log delta in index file.

## 4. DOCTOR FAILURE PROTOCOL
- If backend diagnostic checks verify a FAIL or WARN state, pause workspace mutations. Output exactly:
  > "[ROW-ID] [brief doctor finding]. Remediate, defer, or accept?"
- **State Selection Routing:**
  - `remediate`: Apply workspace repairs or patch lines; re-run `doctor.py`, pass quality flag.
  - `defer`: Modify active row metadata state token to `deferred` (omits from active milestone counts).
  - `accept`: Modify active row metadata state token to `accepted` (flags permanent conscious exception path; silences future execution halts).

## 5. BOUNDARIES & HARD RULES
- **Turn Bounds:** One clean logical functional step (cohesive edits, tests, and docs for a single task) per messaging turn. Narrate architectural targets *before* patching; provide diff code summaries *after* execution. **Never execute full scope in a single pass.**
- **Anti-Cascade:** Plan approval grants permission to run exactly one functional atomic step (one cohesive group of related file/logical edits for a single task) per turn. Modify the step -> run doctor/verify -> render diff/summary -> halt. Multi-step cascades across unrelated roadmap items are forbidden.
- **Git Boundaries:** No git sync outside the commit-cycle cascade (§3 `FULL_LIFECYCLE`/`handoff`) - never a standalone sync outside that pipeline. Never inject un-validated code trees via `--no-verify` or force remote states via `--force`.
- **Sovereign Distribution Cleanliness:** Zero credentials, keys, or workstation absolute path strings are allowed inside version-controlled lanes. Never modify, copy, or read `../THE-NEXUS/01-USER-DATA/IDENTITY.md` parameters without manual operator direction.
- **Syntax Invariant:** Reference internal vault records and cross-module files via markdown `[[wikilinks]]`.

## RELATED
[[NEXUS-CONTEXT]] | [[../THE-NEXUS/_AI-ENTRY-POINTS/INDEX]] | [[../THE-NEXUS/_AI-ENTRY-POINTS/AI-START-HERE]] | [[CLAUDE]] | [[GEMINI]]
