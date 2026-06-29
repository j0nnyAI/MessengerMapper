---
name: write-handoff-doc
description: Writes a session handoff as a dated file in ../MessengerMapper-VAULT/05-MEMORY/ when context window pressure exceeds 60-65 percent or the session is ending mid-task. Captures TL;DR, current state, in-flight work, immediate next 1-3 actions, open questions, blockers, mental model, and "do NOT" list so the next AI session lands hot. Trigger when context is filling, when user types /handoff, or when work must pause.
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

<!--
FILE: .claude/skills/write-handoff-doc/SKILL.md
PURPOSE: Invokes ../THE-NEXUS/scripts/handoff.py for project workspace compaction and optional dated handoff artifacts.
LINKS: ../../../THE-NEXUS/03-SKILLS/context-handoff.md, ../../../THE-NEXUS/06-WORKFLOWS/handoff-protocol.md, ../../../THE-NEXUS/07-TEMPLATES/handoff-doc.md
-->

# Skill: Write Handoff Doc

> Canonical NEXUS instructions live under `../THE-NEXUS/` — this skill is the project-local trigger.

## Triggers

Any of:

- Context window > 60% (early write); >70% (late; do not let it hit 85%).
- End of session with work in flight.
- `/handoff` slash command.
- Project switch (write before pivoting).
- Emergency interrupt — write a quick partial handoff before disconnecting.

## Protocol

### Step 1 — Pause

Stop pushing product code changes. Saving edits to the handoff files themselves is OK.

### Step 2 — Choose shortname

Pick a kebab-case shortname (≤4 words).

### Step 3 — Run the handoff helper

From the project git root (this repo):

```bash
python3 "../THE-NEXUS/scripts/handoff.py" --project-root "." --vault-root "../MessengerMapper-VAULT" -write <shortname>
```

`handoff.py` compacts session state into the sibling vault:

- **`../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md`** — overwrites sections 1–4 under lock; preserves Section 2 narrative when merging.
- **`../MessengerMapper-VAULT/05-MEMORY/YYYY-MM-DD_HISTORY_LOG.md`** — appends the post-merge Section 2 narrative when compaction succeeds.

For a **dated pause artifact** (long break, mid-task interrupt), also create a file under `../MessengerMapper-VAULT/05-MEMORY/` using `../THE-NEXUS/07-TEMPLATES/handoff-doc.md` as the checklist. Update **Where I left things** in `HANDOFF.md` to reference it.

### Step 4 — Fill the dated artifact (when pausing mid-task)

Open the new dated file under `../MessengerMapper-VAULT/05-MEMORY/` and fill **every** section (skip none, even if "none"):

- TL;DR
- Current state (repo, branch, files, tests)
- In-flight work
- Immediately-next 1–3 actions
- Open questions / Blockers
- Mental model
- Do NOT
- Links / Success criteria

Ensure Section 2 narrative in `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md` reflects the pause context before or after `-write`.

### Step 5 — Optional: commit the code repo with a Refs trailer

If the project repo has uncommitted code changes worth preserving, commit them with a `Refs:` trailer. Never `git add ../MessengerMapper-VAULT/` from inside this repo — the vault is outside the work tree.

```bash
git add <code paths inside this repo>
git commit -m "chore(handoff): paused at <where>

Refs: [[YYYY-MM-DD-HHmm-<shortname>]]"
```

If your vault is itself a separate git repo (optional setup), commit it there in a separate step:

```bash
cd ../MessengerMapper-VAULT
git add 05-MEMORY/ 04-CONTEXT/HANDOFF.md
git commit -m "chore(handoff): paused at <where>"
cd -
```

### Step 6 — Sign off

Output one final line and stop:

```
Handoff written: <path from Step 3>.
Work paused at <step>.
Resume target: <next action>.
```

## Anti-patterns

- Continuing edits AFTER the handoff lands (except filling the scaffold).
- Optimistic handoffs with no "Do NOT" when something failed.
- Vague "next" actions ("continue working").
- Trying to `git add` the sibling vault into the project repo.
- Manually duplicating what `handoff.py` already wires (`_HANDOFFS-INDEX.md`, `HANDOFF.md` sections 1–4).

## Verification

The skill is complete when:

- `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md` sections 1–4 are coherent after `-write`.
- When pausing mid-task: the dated `05-MEMORY/` file exists with all sections filled, and **Where I left things** references it.
- The session ends (no further responses) after sign-off.
