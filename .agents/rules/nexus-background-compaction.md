---
activation: model_decision
description: Apply when executing handoff, teardown, commit, push, background compaction, or any write to HANDOFF.md / vault memory.
nexus_asset: .antigravity/rules.json
cursor_parity: .cursor/rules/04-commit-cycle.mdc
---

# Nexus background compaction — MessengerMapper

Background compilations and commit intent must match `handoff.py` / `review-commit.py` lock semantics. Metrics: `.antigravity/rules.json` § `executionMetrics`, `lockBoundaries`, `section2Preservation`.

## 450-character gate

Ledger `-success` / `-failure` and COMPILE message segments: **≤450 characters** (payload right of `|`). Validate length before `handoff.py`. Exit code `2` on violation.

## Section 2 narrative preservation

- Heading: `## 2. THE TECHNICAL NARRATIVE`
- COMPILE may patch Section 2 **before** STEP 1 to seed narrative.
- `handoff.py` acquires `../MessengerMapper-VAULT/04-CONTEXT/handoff.lock` (5.0s timeout), stages to `HANDOFF.md.tmp`, merges with **`_merge_preserve_section2`**: live on-disk Section 2 wins under lock.
- Never write `HANDOFF.md` directly during compaction. Never touch `handoff.lock` manually.

## Atomic git prohibition

Forbidden until STEP 1 **and** STEP 2 both exit `0`:

- `git add`, `git commit`, `git push`, `gh commit`

**STEP 1:** `python3 "../THE-NEXUS/scripts/handoff.py" --project-root "." --vault-root "../MessengerMapper-VAULT" -write "<label>" -success "Category | <summary>"`

**STEP 2:** `python3 "../THE-NEXUS/scripts/review-commit.py" --project-root "." --vault-root "../MessengerMapper-VAULT" --sha HEAD --scope reviewer --dry-run`

Diagnostic `git diff` / `git log` / `git status` allowed during COMPILE.

| Class | Triggers | Terminus |
|---|---|---|
| TEARDOWN | handoff, wrap up, session end, teardown | STEP 1 → STEP 2 → stop |
| FULL_LIFECYCLE | commit, push, ship it, save changes | STEP 1 → STEP 2 → git add → commit (§2 payload) → push |

If both match, FULL_LIFECYCLE wins. Run autonomously; do not ask for confirmation.

Parity: `05-MEMORY/YYYY-MM-DD_HISTORY_LOG.md` and `HANDOFF.md` must be refreshed by STEP 1 before any commit.
