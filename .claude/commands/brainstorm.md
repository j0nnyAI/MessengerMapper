<!--
FILE: .claude/commands/brainstorm.md
PURPOSE: Slash command. /brainstorm <topic> runs the OBRA-style interview engine and writes the synthesis to vault/02-ARCHITECTURE/plans/active/. Lighter than /new-feature - produces a brainstorm brief only, NOT a full executable plan.
LINKS: ../../../THE-NEXUS/10-PROMPTS/feature-brainstorm-interview.md, ../../../THE-NEXUS/10-PROMPTS/interview-engine.md, ../../../THE-NEXUS/03-SKILLS/brainstorming.md
-->

# /brainstorm

Run the OBRA-style interview engine to extract a structured brainstorm brief for one feature or topic, and write it to the active plans folder.

## Argument hint

`/brainstorm <topic>`

`<topic>` is a kebab-case name for the feature. Examples: `oauth-login`, `paddle-physics`, `migrate-to-postgres`. If no topic provided, ask the user for one before proceeding.

## Body

Read the canonical interview prompt at `../../../THE-NEXUS/10-PROMPTS/feature-brainstorm-interview.md` and execute it against the user with `<topic>` substituted.

**Specifically**:

1. **Pre-flight**: read `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md` - note `## 2. THE TECHNICAL NARRATIVE` and `## 4. NEXT IMMEDIATE ACTIONS`. If `<topic>` conflicts with current narrative, surface that and ask whether to pivot or finish current work first.

2. **Interview**: follow the question budget (max 5 questions) and shape from `feature-brainstorm-interview.md`. Each question has named options with tradeoffs. One question at a time.

3. **Synthesize**: produce the synthesis block from `interview-engine.md` and ask the operator: "Ship to active plans? (yes / refine)".

4. **Write**: on `yes`, write to `../MessengerMapper-VAULT/02-ARCHITECTURE/plans/active/YYYY-MM-DD-<topic>.md` with frontmatter and a `Next step` line pointing at the `writing-plans` skill. Update `02-ARCHITECTURE/plans/_PLANS-INDEX.md`.

5. **Close**: output exactly:
   ```
   Brainstorm written: 02-ARCHITECTURE/plans/active/YYYY-MM-DD-<topic>.md.
   Next: /new-feature <topic> to expand into an executable plan, or invoke writing-plans directly.
   ```

   Stop. Do not start implementation.

## Difference from /new-feature

| | `/brainstorm <topic>` | `/new-feature <description>` |
|---|---|---|
| Output | brainstorm synthesis (one page) | full executable plan (multi-phase) |
| Question budget | 5 | unbounded |
| Best when | scope is unclear, decisions need exploration | scope is clear, ready to execute |
| Follow-up | `/new-feature` runs after this if approved | none - ready to execute |

## Success criteria

- File exists at the expected path with all synthesis sections.
- `_PLANS-INDEX.md` has a new row.
- User has not been firehose'd; one question per turn.
- No implementation work was started.

## Related

- `/new-feature <description>` - expand a brainstorm into a full plan.
- `../../../THE-NEXUS/03-SKILLS/writing-plans.md` - the skill that produces the plan from this brief.
