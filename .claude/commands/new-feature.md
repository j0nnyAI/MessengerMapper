<!--
FILE: .claude/commands/new-feature.md
PURPOSE: Slash command. /new-feature kicks off a feature: brainstorm -> plan -> save plan to 06-PLANS/active/.
LINKS: ../../../THE-NEXUS/03-SKILLS/brainstorming.md, ../../../THE-NEXUS/03-SKILLS/writing-plans.md, ../../../THE-NEXUS/07-TEMPLATES/plan.md
-->

# /new-feature

Kick off a new feature. Brainstorm load-bearing decisions, then write a plan.

## Argument hint

`/new-feature <short-description>`

If no description provided, ask the user for one before proceeding.

## Body

### Phase 1  Brainstorm

Invoke the `brainstorming` skill at `../../../THE-NEXUS/03-SKILLS/brainstorming.md`:

1. Restate the feature goal in one line. Confirm with user.
2. Identify load-bearing decisions (?3).
3. Ask 1-2 questions on the load-bearing decisions, with options + tradeoffs.
4. Wait. Absorb. Repeat until decisions are settled.

Do NOT firehose. One question at a time.

### Phase 2  Plan

Once design is approved by user, invoke the `writing-plans` skill at `../../../THE-NEXUS/03-SKILLS/writing-plans.md`:

1. Use the template `../../../THE-NEXUS/07-TEMPLATES/plan.md`.
2. Save to `../MessengerMapper-VAULT/06-PLANS/active/YYYY-MM-DD-<short-name>.md` where `<short-name>` is kebab-case ?4 words.
3. Update `06-PLANS/_PLANS-INDEX.md`.
4. Update `## 2. THE TECHNICAL NARRATIVE` in `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md` to reference the new plan.

### Phase 3  Confirm and stop

Output:

```
Plan written: 06-PLANS/active/YYYY-MM-DD-<short-name>.md.
Phases: <N>. Open questions: <count>. Ready to execute.
Awaiting "go" or amendments.
```

Do NOT begin executing. Wait for user direction.

## Success criteria

- Plan file exists with all required sections (Overview, Assumptions, Out-of-scope, Phases, Risks, Open Questions, Success Criteria).
- Plans index updated.
- `HANDOFF.md` §2 narrative references the plan.
- User has not been firehose'd; brainstorming was incremental.

## Related

- `/brainstorm <topic>`  lighter-weight interview that produces just the brainstorm synthesis, before running this command.
