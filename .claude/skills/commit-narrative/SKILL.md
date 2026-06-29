---
name: commit-narrative
description: Milestone commits only (release, breaking change, post-incident, architectural pivot). Skip routine commits — the async post-commit hook handles those.
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

<!--
FILE: .claude/skills/commit-narrative/SKILL.md
PURPOSE: Project-local wrapper for the canonical NEXUS skill.
LINKS: ../../../THE-NEXUS/03-SKILLS/commit-narrative.md
GENERATED: by sync-assets-to-template.py. Safe to hand-edit, but a re-run with --force will overwrite.
-->

# Skill: Commit Narrative

Wraps `../../../THE-NEXUS/03-SKILLS/commit-narrative.md`. Read the canonical file for the full protocol, quality bar, and anti-patterns.

## Trigger

Milestone commits only (release, breaking change, post-incident, architectural pivot). Skip routine commits — the async post-commit hook handles those.

## Protocol

See the linked canonical skill. Project-specific overrides go here (rare).
