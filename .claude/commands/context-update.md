<!--
FILE: .claude/commands/context-update.md
PURPOSE: Slash command. /context-update refreshes HANDOFF.md v3 sections mid-session.
LINKS: ../../../THE-NEXUS/06-WORKFLOWS/commit-cycle.md
-->

# /context-update

Refresh `HANDOFF.md` v3 sections mid-session, without committing. Use when the session has progressed and the next AI reply needs to see the new state immediately (full compaction runs at commit-cycle STEP 1).

## Body

1. Read `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md`.
2. Update the v3 sections:
   - `## 2. THE TECHNICAL NARRATIVE` — current task, blockers, and in-progress work. Keep it dense.
   - `## 4. NEXT IMMEDIATE ACTIONS` — file-and-function specific next steps.
   - Do **NOT** rewrite `## 1. RUNTIME STATE` epoch/branch/baseline unless the operator directs it.
   - Do **NOT** manually append `05-MEMORY/` — STEP 1 `handoff.py` owns durable history.
3. Output exactly one line:

   ```
   Context updated. Narrative: <one phrase>. Next actions: <count>. Baseline: <Stable|Degraded|Blocked>.
   ```

## When to use this command

- You discovered something non-obvious and the next AI session needs to know about it.
- You're pivoting focus mid-session and want the new direction reflected.
- You've finished a discrete chunk of work and want to capture state before pivoting.

## When NOT to use this command

- Before commit — run commit-cycle STEP 1 (`handoff.py`) instead.
- End of session — write a handoff instead (`/handoff`).
- Mass rewriting `05-MEMORY/` logs — those are append-only and managed by STEP 1.

## Success criteria

- `HANDOFF.md` §2 and §4 reflect current reality.
- One-line summary output.
- No other vault files touched unless explicitly required.
