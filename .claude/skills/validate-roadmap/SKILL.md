---
name: validate-roadmap
description: **Roadmap (diagnostic, any phase)** — operator says `validate roadmap <file>` or `validate roadmap`. Read-only cross-check: classifies every row as CLOSED / OPEN / AMBIGUOUS using Session notes + frontmatter + paired GAPS file. No writes. Use before resuming an old roadmap to confirm what is genuinely open.
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

<!--
FILE: .claude/skills/validate-roadmap/SKILL.md
PURPOSE: Project-local wrapper for the canonical NEXUS skill.
LINKS: ../../../THE-NEXUS/03-SKILLS/validate-roadmap.md
GENERATED: by sync-assets-to-template.py. Safe to hand-edit, but a re-run with --force will overwrite.
-->

# Skill: Validate Roadmap

Wraps `../../../THE-NEXUS/03-SKILLS/validate-roadmap.md`. Read the canonical file for the full protocol, quality bar, and anti-patterns.

## Trigger

**Roadmap (diagnostic, any phase)** — operator says `validate roadmap <file>` or `validate roadmap`. Read-only cross-check: classifies every row as CLOSED / OPEN / AMBIGUOUS using Session notes + frontmatter + paired GAPS file. No writes. Use before resuming an old roadmap to confirm what is genuinely open.

## Protocol

See the linked canonical skill. Project-specific overrides go here (rare).
