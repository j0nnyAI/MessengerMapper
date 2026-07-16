---
name: update-roadmap
description: **Roadmap (Phase B only)** — during remediation. Operator says `update roadmap`, `mark S-XX done`, or `mark OW-XX quality`. Updates row status + Session notes on existing active roadmap; syncs `_ROADMAPS-INDEX` open count. **Step 2.5 runs RAT before `quality`.** Never creates a new `16-ROADMAPS/` file.
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

<!--
FILE: .claude/skills/update-roadmap/SKILL.md
PURPOSE: Project-local wrapper for the canonical NEXUS skill.
LINKS: ../../../THE-NEXUS/03-SKILLS/update-roadmap.md
GENERATED: by sync-assets-to-template.py. Safe to hand-edit, but a re-run with --force will overwrite.
-->

# Skill: Update Roadmap

Wraps `../../../THE-NEXUS/03-SKILLS/update-roadmap.md`. Read the canonical file for the full protocol, quality bar, and anti-patterns.

## Trigger

**Roadmap (Phase B only)** — during remediation. Operator says `update roadmap`, `mark S-XX done`, or `mark OW-XX quality`. Updates row status + Session notes on existing active roadmap; syncs `_ROADMAPS-INDEX` open count. **Step 2.5 runs RAT before `quality`.** Never creates a new `16-ROADMAPS/` file.

## Protocol

See the linked canonical skill. Project-specific overrides go here (rare).
