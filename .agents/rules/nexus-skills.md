---
activation: auto
nexus_asset: .agents/asset-parity.manifest.json
cursor_parity: .cursor/rules/06-skills.mdc
---

<!--
FILE: .agents/rules/nexus-skills.md
PURPOSE: Antigravity skills catalog compiled from THE-NEXUS/03-SKILLS/_SKILLS-INDEX.md.
GENERATED: by sync-assets-to-template.py. Re-run with --force to refresh.
-->

# Nexus skills — MessengerMapper

Antigravity is blind to Cursor `.mdc` rules. Read the canonical skill before executing any protocol.

Source of truth: `../THE-NEXUS/03-SKILLS/_SKILLS-INDEX.md`.

| Skill | When to Use |
|---|---|
| `brainstorming` | Before any creative or non-trivial work. Refines intent through questions. |
| `writing-plans` | When you have a spec; produces an executable implementation plan. |
| `executing-plans` | When following a written plan with review checkpoints. |
| `systematic-debugging` | Any bug, test failure, or unexpected behavior, before proposing fixes. |
| `test-driven-development` | Implementing any feature or bugfix, before writing implementation. |
| `smoke-testing-and-verification` | Before completing any implementation row or running validation scripts; smoke gates, regression boundaries, decoupled mocks, report interpretation (persona: tester). |
| `zero-downtime-database-migrations` | Before executing any DDL or ORM schema migration; lock analysis, staged backfill, rollback proof (persona: database-administrator). |
| `api-integration-resilience` | Before calling external REST/GraphQL APIs or authoring client wrappers; rate-limit backoff, fallback responses, webhook verification, JSON schema safeguards (persona: integrator). |
| `performance-profiling-and-tracing` | Before claiming a performance fix or running optimization work; cProfile/py-spy, Chrome DevTools traces, query EXPLAIN cost audit, hotspot reports (persona: performance-engineer). |
| `model-evaluation-and-tuning` | Before changing LLM parameters, evaluating prompt quality, or hardening agent workflows; token economics audit, prompt injection mitigation, LLM-as-judge eval harness (persona: model-engineer). |
| `compliance-and-security-hardening` | Before auditing secrets rotation, IAM least-privilege, or regulatory posture; SOC2/GDPR checklists, wildcard IAM removal, workstation/CI hardening (persona: secops). |
| `environment-bootstrap-and-project-init` | Before bootstrapping a Trinity sibling pair or running init; initialize-project.py, token substitution, sibling vault layout, post-init doctor gate (persona: devops-engineer). |
| `context-handoff` | When context window is filling and a new session is imminent. |
| `compress-context` | When episodic memory footprint exceeds 30 entries or 90 days. Distills logs into Phase Arcs. |
| `nexus-benchmark` | Operator says "run a nexus benchmark", "benchmark the system", or "perform a nexus benchmark". Runs the repeatable efficiency benchmark and records results to ARCHIVE/. |
| `commit-narrative` | Milestone commits only (release, breaking change, post-incident, architectural pivot). Skip routine commits — the async post-commit hook handles those. |
| `requesting-code-review` | When completing tasks or before merging. |
| `verification-before-completion` | Before claiming work is "done", "fixed", or "passing". |
| `using-subagents` | When facing 2+ independent tasks with no shared state. |
| `reading-the-vault-first` | Mandatory first step on every session. |
| `ai-doc-truth-audit` | **Doc-Truth lens** — verify documentation claims match code reality (TRUE/STALE/PHANTOM/DRIFTED). Run as docs-writer, scoped to one doc or claim-class. |
| `create-roadmap` | **Roadmap (Phase A only)** — after an audit is complete. Operator says `roadmap`, `create roadmap`, or `create roadmap from <file>`. Requires explicit audit source when >1 recent/open audit or >1 active roadmap; Check C refuses duplicate from linked audit. Phase A.5 sibling reconcile (Step 2.5) before work order. Writes ordered plan to `16-ROADMAPS/`. |
| `update-roadmap` | **Roadmap (Phase B only)** — during remediation. Operator says `update roadmap`, `mark S-XX done`, or `mark OW-XX quality`. Updates row status + Session notes on existing active roadmap; syncs `_ROADMAPS-INDEX` open count. **Step 2.5 runs RAT before `quality`.** Never creates a new `16-ROADMAPS/` file. |
| `validate-roadmap` | **Roadmap (diagnostic, any phase)** — operator says `validate roadmap <file>` or `validate roadmap`. Read-only cross-check: classifies every row as CLOSED / OPEN / AMBIGUOUS using Session notes + frontmatter + paired GAPS file. No writes. Use before resuming an old roadmap to confirm what is genuinely open. |
| `verify-roadmap-row` | **Roadmap (Phase B quality gate)** — before `mark … quality`. Runs Remediation Acceptance Tests (RAT); refuses false positives; operator may waive with reason. Invoked by update-roadmap Step 2.5 or `verify S-XX`. |
| `archive-roadmap` | **Roadmap (Phase D)** — retire a completed track. Operator says `100% remediated` or `archive roadmap`. Atomic done + audit remediated + move to `16-ROADMAPS/ARCHIVE/`; main index active-only. |
| `resume-roadmap-row` | **Roadmap (Phase B session start)** — operator says `resume S-XX`, `start OW-04`, or `OW-04 only`. Loads one row's Session notes; locks session to that row; refuses second row. Read-only until implementation. |
| `remediation-gap-watch` | **Roadmap (Phase B overlay)** — `gaps on` / `enable gaps` / `watch gaps` / `find gaps` (no scope) → § **Mandatory cascade**; buffer on blast-radius traversals; **flush before row `quality`**. Operator does not re-paste watch directive. **Not** `gap analysis on <scope>`. Off: `gaps off`. |
| `framework-asset-author` | **Meta-framework authoring** — before creating, extending, overriding, or importing engine personas, skills, or prompts. Covers PERSONA-SCHEMA, `new-persona.py` / `new-skill.py` / `nexus-import.py`, distribution safety, and `doctor.py -full` gate. **Not** Phase B row work — use [[resume-roadmap-row]] first. |
| `writing-specs` | Operator says "create a spec", "write a spec", "spec this out", or "spec for [feature]". Converts a settled design into a locked-down implementation spec saved to `02-ARCHITECTURE/specs/`. |
| `live-test-intake` | When initializing a new live field test run. Captures pre-conditions and creates the test run log. |
| `folder-architecture-audit-series` | Systematic architectural-soundness sweep across multiple scopes — operator says "audit folder by folder", "gap-enabled audit series", "2nd pass gap analysis across X". Runs the two-audit method per scope, defers remediation, consolidates into one roadmap at close. |
| `retrieve-before-advise` | Before remediating doctor FAIL/WARN, proposing demote/silence/accept/partial-ship of required tooling, or TOOL-MATRIX/parity option menus — run events + lessons query; cite IDs or `none matched`. |

Canonical definitions: `../THE-NEXUS/03-SKILLS/<name>.md`.
