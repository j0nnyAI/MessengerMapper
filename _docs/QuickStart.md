# MessengerMapper — Application Workspace QuickStart

Welcome to `MessengerMapper/` — the code workspace for your Nexus project.

The AI never forgets where it left off because all session state lives in the vault next door (`../MessengerMapper-VAULT/`). It reads `HANDOFF.md` on cold-start and is immediately oriented — no re-briefing, no directory walks.

For the full three-folder model (code, vault, engine): [`NEXUS-CONTEXT.md`](../NEXUS-CONTEXT.md)

---

## Before Your First Commit — Install the Post-Commit Hook

The async review dispatch (optional `Review:` trailer processing) depends on a post-commit hook installed in `.git/hooks/`. It is not active until you run initialization.

```bash
python ../THE-NEXUS/scripts/initialize-project.py --project-root . --vault-root ../MessengerMapper-VAULT
```

Run this once after cloning or bootstrapping the project. If you skip it, commits succeed but `Review:` trailers have no effect. Vault state is managed by STEP 1 (see below) — the hook is secondary verification only, not the primary update engine.

---

## For Python Projects

Before your first commit, create the standard layout:

```bash
mkdir -p src/messengermapper tests
```

The `.cursor/rules/` code style mandates `src/` layout for Python projects. This folder is not created automatically — add it before writing any source files.

---

## The Development Loop

Your day-to-day work is three steps. Step 3 is the important one — do not raw-commit.

### Step 1 — Build

Tell your AI what to build. It reads `HANDOFF.md` on cold-start and picks up exactly where the last session ended.

### Step 2 — Verify

Run your tests or check the running app. The AI has a `verification-before-completion` skill — invoke it before claiming anything is done.

```bash
# Quick health check any time
python ../THE-NEXUS/scripts/doctor.py --project-root . --vault-root ../MessengerMapper-VAULT
```

### Step 3 — Commit (via cascade)

**Say `"commit and push"` in your AI chat.** Do not run `git commit` directly.

The `FULL_LIFECYCLE` cascade fires automatically:

1. **STEP 1 — Vault compaction** (`handoff.py`): writes session state to the vault, refreshes `HANDOFF.md`. Must exit 0.
2. **STEP 2 — Schema validation** (`review-commit.py --dry-run`): confirms vault topology and diff tracking. Must exit 0.
3. **STEP 3 — Git sync**: `git add → git commit → git push`. Only runs after both gates pass.

After the commit lands, the post-commit hook fires asynchronously — it confirms `HANDOFF.md` parity and dispatches any `Review:` trailers you added. It does **not** replace STEP 1. If STEP 1 was skipped, the hook does not backfill missing context.

**If you prefer manual control:**

```bash
# STEP 1
python ../THE-NEXUS/scripts/handoff.py --project-root . --vault-root ../MessengerMapper-VAULT -write <session-label>

# STEP 2
python ../THE-NEXUS/scripts/review-commit.py --project-root . --vault-root ../MessengerMapper-VAULT --sha HEAD --scope reviewer --dry-run

# STEP 3 (only after both exit 0)
git add <files>
git commit -m "your message"
git push
```

**Never:**
```bash
git commit --no-verify    # bypasses the gate — never
git push --force          # on shared or main branches — never
```

---

## Optional: Review Trailers

Add one line to a commit message to trigger a background review pass for that commit:

| Trailer | What it spawns |
|---------|---------------|
| `Review: yes` | Code quality review → `../MessengerMapper-VAULT/14-AUDITS/` |
| `Review: security` | Security audit → `../MessengerMapper-VAULT/14-AUDITS/` |
| `Review: full` | Both in parallel |

Example:
```
feat(auth): add OAuth login

Review: security
```

The post-commit hook picks this up asynchronously. No extra steps required.

---

## Session Close

Say `"wrap up"` to close a session without committing (TEARDOWN):
1. STEP 1 — vault compaction
2. STEP 2 — dry-run validation
3. No git

Say `"commit and push"` to close and ship (FULL_LIFECYCLE):
1. STEP 1 + STEP 2 + git

---

## Further Reading

- [`NEXUS-CONTEXT.md`](../NEXUS-CONTEXT.md) — the three-folder model; what the siblings are
- [`../MessengerMapper-VAULT/_docs/QuickStart.md`](../MessengerMapper-VAULT/_docs/QuickStart.md) — vault orientation: what each folder does
- [`AGENTS.md`](../AGENTS.md) — full operational contract: lifecycle triggers, CLI commands, persona resolution
- [`../THE-NEXUS/08-DOCS/OPERATOR-WORKFLOW.md`](../THE-NEXUS/08-DOCS/OPERATOR-WORKFLOW.md) — full operator lifecycle: audit → roadmap → remediate → handoff → commit
- [`../THE-NEXUS/08-DOCS/RUNBOOK.md`](../THE-NEXUS/08-DOCS/RUNBOOK.md) — engine operator reference; full script argv
