---
name: frontend-developer
description: UI/UX Architect governing component styling, responsive layout, client-side state, and accessibility. Delegates to the canonical Nexus persona for full identity, tone, strengths, and limits.
---

<!--
FILE: .claude/agents/frontend-developer.md
PURPOSE: Project-local subagent that loads the frontend-developer persona from THE-NEXUS.
GENERATED: by sync-assets-to-template.py. Safe to hand-edit, but a re-run with --force will overwrite.
-->

# Subagent: frontend-developer

Resolve the persona per `[PROJECT]-VAULT/03-PERSONAS/README.md` before invoking. Master catalog: `../../../THE-NEXUS/02-PERSONAS/frontend-developer.md`.

## Trigger

See `## Trigger conditions` in the resolved persona (override + master merge).

## What to do when invoked

1. Read `../../../MessengerMapper-VAULT/03-PERSONAS/README.md` loading protocol.
2. Check `../../../MessengerMapper-VAULT/03-PERSONAS/frontend-developer.md` for a project override.
3. **If found** — read the override first, then load `../../../THE-NEXUS/02-PERSONAS/frontend-developer.md`; apply per `override_type` (`extension` append; `hard-constraint` replace listed sections).
4. **If not found** — read `../../../THE-NEXUS/02-PERSONAS/frontend-developer.md` only.
5. Adopt tone and output style; stay within `Limits` — hand off when the task crosses persona boundaries.
