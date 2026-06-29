---
name: verify-roadmap-row
description: **Roadmap (Phase B quality gate)** — before `mark … quality`. Runs Remediation Acceptance Tests (RAT); refuses false positives; operator may waive with reason. Invoked by update-roadmap Step 2.5 or `verify S-XX`.
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

<!--
FILE: .claude/skills/verify-roadmap-row/SKILL.md
PURPOSE: Project-local wrapper for the canonical NEXUS skill.
LINKS: ../../../THE-NEXUS/03-SKILLS/verify-roadmap-row.md
GENERATED: by sync-assets-to-template.py. Safe to hand-edit, but a re-run with --force will overwrite.
-->

# Skill: Verify Roadmap Row

Wraps `../../../THE-NEXUS/03-SKILLS/verify-roadmap-row.md`. Read the canonical file for the full protocol, quality bar, and anti-patterns.

## Trigger

**Roadmap (Phase B quality gate)** — before `mark … quality`. Runs Remediation Acceptance Tests (RAT); refuses false positives; operator may waive with reason. Invoked by update-roadmap Step 2.5 or `verify S-XX`.

## Protocol

See the linked canonical skill. Project-specific overrides go here (rare).
