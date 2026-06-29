<!--
FILE: .claude/commands/handoff.md
PURPOSE: Slash command. /handoff writes a session handoff doc and runs TEARDOWN cascade.
LINKS: ../skills/write-handoff-doc/SKILL.md, ../../../THE-NEXUS/06-WORKFLOWS/commit-cycle.md
-->

# /handoff

End the session cleanly. Writes a dated handoff doc to the vault, compacts state, and runs TEARDOWN (STEP 1 + STEP 2, no git).

## Body

1. Load skill: `../skills/write-handoff-doc/SKILL.md` — follow it verbatim.
2. After the handoff doc is written, run TEARDOWN cascade:
   - COMPILE: scan local diff and session; draft narrative ≤450 characters; patch `HANDOFF.md` § 2.
   - STEP 1: `python ../THE-NEXUS/scripts/handoff.py --project-root . --vault-root ../MessengerMapper-VAULT -write handoff -success "Session | <summary>"`
   - STEP 2: `python ../THE-NEXUS/scripts/review-commit.py --project-root . --vault-root ../MessengerMapper-VAULT --sha HEAD --scope reviewer --dry-run`
   - Stop after STEP 2. No git commit or push.
3. Output exactly one line:

   ```
   Handoff written. State compacted. Session closed.
   ```

## When to use this command

- End of any working session.
- Context window approaching 60–65%.
- Handing off to a different AI tool (Cursor → Claude, Claude → Gemini).
- Pausing work mid-task and resuming later.

## When NOT to use this command

- When you want to commit and push — use `FULL_LIFECYCLE` instead (say "commit and push").
- Mid-session state snapshot without ending — use `/context-update`.

## Success criteria

- Dated handoff doc exists in `../MessengerMapper-VAULT/05-MEMORY/`.
- `HANDOFF.md` §2 narrative reflects current session state.
- STEP 1 and STEP 2 both exit 0.
- No git commit was made.
