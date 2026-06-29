---
name: create-roadmap
description: **Roadmap (Phase A only)** — after an audit is complete. Operator says `roadmap`, `create roadmap`, or `create roadmap from <file>`. Requires explicit audit source when >1 recent/open audit or >1 active roadmap; Check C refuses duplicate from linked audit. Phase A.5 sibling reconcile (Step 2.5) before work order. Writes ordered plan to `16-ROADMAPS/`.
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

<!--
FILE: .claude/skills/create-roadmap/SKILL.md
PURPOSE: Project-local wrapper for the canonical NEXUS skill.
LINKS: ../../../THE-NEXUS/03-SKILLS/create-roadmap.md
GENERATED: by sync-assets-to-template.py. Safe to hand-edit, but a re-run with --force will overwrite.
-->

# Skill: Create Roadmap

Wraps `../../../THE-NEXUS/03-SKILLS/create-roadmap.md`. Read the canonical file for the full protocol, quality bar, and anti-patterns.

## Trigger

**Roadmap (Phase A only)** — after an audit is complete. Operator says `roadmap`, `create roadmap`, or `create roadmap from <file>`. Requires explicit audit source when >1 recent/open audit or >1 active roadmap; Check C refuses duplicate from linked audit. Phase A.5 sibling reconcile (Step 2.5) before work order. Writes ordered plan to `16-ROADMAPS/`.

## Protocol

See the linked canonical skill. Project-specific overrides go here (rare).
