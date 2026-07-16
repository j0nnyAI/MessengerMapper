---
activation: always_on
nexus_asset: .antigravity/rules.json
cursor_parity: .cursor/rules/00-always.mdc
---

# Nexus spatial invariants - MessengerMapper

This file forms the unbreakable spatial configuration layer for Antigravity engine runtimes. Machine-readable constraints are matched dynamically against `.antigravity/rules.json`.

## 1. WORKSPACE ANCHORS
- project-root: `.` (Git work tree)
- nexus_index: `../THE-NEXUS/_AI-ENTRY-POINTS/INDEX.md`
- context_path: `../MessengerMapper-VAULT/04-CONTEXT/HANDOFF.md`
- hydration_path: `../MessengerMapper-VAULT/04-CONTEXT/HYDRATION-NEXT-SESSION.md` [Optional]
- vault-root: `../MessengerMapper-VAULT/` (All mutations target this directory exclusively; writing to peer vaults is prohibited)

## 2. FIRST ACTION (BOOT & HYDRATION SEQUENCE)
1. **Load State:** Read `context_path` and `hydration_path` (if present).
   - *Epic Link:* If `HANDOFF.md` §1 holds `Epic Pointer: [[wikilink]]`, resolve and read that file immediately.
   - *Strategic Pivot:* If no active roadmap row exists OR query intent is architectural, read `../MessengerMapper-VAULT/02-ARCHITECTURE/_ARCHITECTURE-INDEX.md` and referenced ADRs.
2. **Contract Guard:** Follow roadmap **Active contract** row ID and Session notes pointers exclusively. Ignore loose checkboxes under HANDOFF §4.
3. **Blacklist Pattern:** Never walk or parse paths matching `**/ARCHIVE/**`. Access allowed only via explicit operator `@` mention.
4. **Fail-Loud Gate:** If `context_path` or `nexus_index` do not resolve on disk, emit exactly: `Cannot reach <missing path>. Where does it live?` and halt thread.
5. **Signal:** Confirm boot by printing verbatim: `Hydrated on MessengerMapper. Persona: <active_role>. Ready.`

## 3. OPERATOR CONVERSATIONAL INTENT ROUTING
- **Row Launch** [`resume S-XX` / `start OW-XX` / `OW-XX only`]: Load `../THE-NEXUS/03-SKILLS/resume-roadmap-row.md`. Read row Session notes only.
- **Gaps Registration** [`gaps on` / `enable gaps` / `watch gaps` / `find gaps` / `search for gaps`]: Load `../THE-NEXUS/03-SKILLS/remediation-gap-watch.md`. Set `gap_watch_state=on`, flush before row quality. Off trigger: `gaps off` / `disable gaps`.
- **Value Audit** [`gap analysis on <scope>` / `value audit on <scope>`]: Load `../THE-NEXUS/03-SKILLS/ai-tooling-value-audit.md`.
- **Intent Capture** [`capture intent` / `note design direction` / `architectural direction` / `design intent` / `high-level thinking on`]: Short-circuit roadmap creation. Read `../MessengerMapper-VAULT/02-ARCHITECTURE/_ARCHITECTURE-INDEX.md`, compile spec under `decisions/`, log delta in index file.
- **Teardown Trigger** [`handoff` / `wrap up` / `end session` / `teardown` / `FULL_LIFECYCLE` / `commit and push`]: Route execution directly to `.cursor/rules/04-commit-cycle.mdc`.

## 4. DOCTOR FAILURE PROTOCOL
- If `doctor.py` yields FAIL or WARN during a check cycle, stop feature implementation. Prompt operator:
  > "[ROW-ID] [brief doctor finding]. Remediate, defer, or accept?"
- **Routing:**
  - `remediate`: Apply active workspace repairs; re-run `doctor.py`, clear quality target.
  - `defer`: Set row status metadata parameter to `deferred` (omits from active milestone counts).
  - `accept`: Set row status metadata parameter to `accepted` (flags permanent conscious gap; silences future script exits).

## 5. HARD RULES & EXECUTION BOUNDS
- **Turn Bounds:** One logical file/code change per turn. Narrate architectural targets *before* patching; provide diff code summaries *after* execution. **Never execute full scope in one pass.** Questions or pushback do not constitute permission to proceed.
- **Git Boundaries:** Run zero automated syncs. Never run `git commit --no-verify` or `git push --force`.
- **Sovereign Data Firewalls:** Zero credentials or plain-text secrets in tracked code lines. Running `identity.py --strip` requires direct confirmation.
- **Syntax:** Reference internal vault nodes via `[[wikilinks]]`.
