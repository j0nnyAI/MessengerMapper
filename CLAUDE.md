<!--
FILE: CLAUDE.md
PURPOSE: Claude Code memory file. @-imports AGENTS.md and adds Claude-specific bootstrap.
LOADS: Auto-loaded by Claude Code at session start (hierarchical).
-->

# CLAUDE.md - MessengerMapper

@./AGENTS.md

## Claude-specific bootstrap

Operator identity and working context live in `../THE-NEXUS/01-USER-DATA/IDENTITY.md`. Read on demand for this project.

Persona: `surgeon`. See `../THE-NEXUS/02-PERSONAS/surgeon.md` and `../THE-NEXUS/01-USER-DATA/IDENTITY.md`.

### Persona binding (overrides AGENTS.md schema)

| Parameter | Value |
|---|---|
| `persona` | `surgeon` |
| `hydration_line` | `Hydrated on MessengerMapper. Persona: surgeon. Ready.` |

All other entry parameters (`context_path`, `nexus_index`, `failure_line`) and the **First action** sequence (read HANDOFF.md → load Epic Pointer doc if present → read hydration → emit hydration line → wait) are inherited unchanged from `./AGENTS.md § Entry parameters (hydration contract)`. Do not paraphrase the ritual - follow AGENTS.md verbatim with this persona slot.

### MDC parity (Claude Code)

Claude Code cannot load Cursor `.mdc` rules. **Every session:** `Read` `.claudecode.json` and internalize `claudeCode.appendSystemPrompt` before any other tool use. That block is the binding translation of `.cursor/rules/00-always.mdc` and `.cursor/rules/04-commit-cycle.mdc` (first-action invariant, atomic git prohibition, 450-character compaction, interception cascade).

### Commits (no manual ritual)

Commit intent triggers commit-cycle STEP 1 (`handoff.py`) before git per `.cursor/rules/04-commit-cycle.mdc`. Post-commit hook is secondary verification only (and spawns review agents when a `Review:` trailer is present). See `../THE-NEXUS/06-WORKFLOWS/commit-cycle.md`.

### Project skills (`.claude/skills/`)

| Skill | Trigger |
|---|---|
| `brainstorming` | Before any creative or non-trivial work |
| `commit-narrative` | Milestone commits only (release, breaking change, post-incident, architectural pivot) |
| `context-handoff` | Context window filling; new session imminent |
| `executing-plans` | Following a written plan with review checkpoints |
| `reading-the-vault-first` | Mandatory first step every session |
| `requesting-code-review` | Completing tasks or before merging |
| `systematic-debugging` | Any bug, test failure, or unexpected behavior |
| `test-driven-development` | Implementing a feature or bugfix before writing code |
| `using-subagents` | 2+ independent tasks with no shared state |
| `verification-before-completion` | Before claiming work is done, fixed, or passing |
| `write-handoff-doc` | Context >60% or `/handoff` |
| `writing-plans` | When you have a spec; produces an executable implementation plan |

Each `SKILL.md` references the NEXUS source-of-truth in `../THE-NEXUS/03-SKILLS/`.

### Subagents (`.claude/agents/`)

| Subagent | Persona | When |
|---|---|---|
| `architect` | `../THE-NEXUS/02-PERSONAS/architect.md` | Design-level decisions before code is written |
| `debugger` | `../THE-NEXUS/02-PERSONAS/debugger.md` | Bugs, test failures, unexpected behavior |
| `devops-engineer` | `../THE-NEXUS/02-PERSONAS/devops-engineer.md` | CI/CD, infra, deploy, fleet operations |
| `docs-writer` | `../THE-NEXUS/02-PERSONAS/docs-writer.md` | Docs, ADRs, READMEs |
| `planner` | `../THE-NEXUS/02-PERSONAS/planner.md` | Spec → executable plan (plan mode; does not execute) |
| `reviewer` | `../THE-NEXUS/02-PERSONAS/reviewer.md` | Pre-commit / pre-PR review |
| `security-auditor` | `../THE-NEXUS/02-PERSONAS/security-auditor.md` | Auth/secrets/IAM/network/dep diffs |
| `surgeon` | `../THE-NEXUS/02-PERSONAS/surgeon.md` | Line-level surgical code changes |
| `teacher` | `../THE-NEXUS/02-PERSONAS/teacher.md` | Explain code/systems at expert-read level |

### Slash commands (`.claude/commands/`)

| Command | What it does |
|---|---|
| `/handoff` | Writes a handoff doc and ends the session cleanly |
| `/context-update` | Updates `HANDOFF.md` §2 narrative and §4 next actions mid-session |
| `/new-feature <name>` | Plan a feature; save plan to `06-PLANS/active/` |
| `/brainstorm <topic>` | OBRA-style interview; save result to `06-PLANS/active/<topic>.md` |

## Tool permissions

Committed baseline: `.claude/settings.json` (mirrors `.claudecode.json` § `claudeCode.permissions`). Personal overrides: `.claude/settings.local.json`. Default: inherit globals; tighten per-project as needed.

## Linked

- `./AGENTS.md`
- `../THE-NEXUS/02-PERSONAS/surgeon.md`
- `../THE-NEXUS/03-SKILLS/_SKILLS-INDEX.md`
