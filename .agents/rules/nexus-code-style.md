---
activation: auto
nexus_asset: .agents/asset-parity.manifest.json
cursor_parity: .cursor/rules/10-python.mdc, 11-bash.mdc, 12-typescript.mdc, 13-markdown.mdc
---

<!--
FILE: .agents/rules/nexus-code-style.md
PURPOSE: Antigravity code-style parity compiled from Cursor .mdc rules 10–13.
GENERATED: by sync-assets-to-template.py. Re-run with --force to refresh.
-->

# Nexus code style — MessengerMapper

Antigravity is blind to Cursor `.mdc` globs. Apply these rules when editing matching file types.

## Python

Source: `../THE-NEXUS/04-STANDARDS/code-style/python.md`.

- Tooling: `uv` (deps), `ruff` (lint+format), `mypy --strict` (type), `pytest` (tests).
- `pyproject.toml` is the only config home. `src/` layout mandatory.
- Type hints on all public functions and class attributes. Prefer `collections.abc` over `typing`.
- Google-style docstrings on every public function/class.
- Never bare `except:` or `except Exception` without logging.
- Never `print` in non-CLI code; use `logger = logging.getLogger(__name__)`.
- Never `*` imports or mutable default args.
- `pathlib.Path` over `os.path`. `subprocess.run(..., check=True)`; never `shell=True` with user input.
- `f-strings` for formatting; `%`-formatting only for `logging.*` calls.
- Secrets: `os.environ["KEY"]` — fail loudly; never inline; never silent defaults.

## Shell (Bash / PowerShell)

Source: `../THE-NEXUS/04-STANDARDS/code-style/bash.md`.

Bash header: `#!/usr/bin/env bash`, `set -euo pipefail`, `IFS=$'\n\t'`. Shellcheck-clean. Quote `"$var"`. `mktemp` + `trap` cleanup. Logs to stderr.

PowerShell 7+: `#Requires -Version 7.0`, `[CmdletBinding()]`, `$ErrorActionPreference = "Stop"`, `Set-StrictMode -Version Latest`. Approved verbs. Splat parameters. `Set-Content -Encoding UTF8`.

Cross-shell: prefer Python when both are required. No unquoted variables, `eval`/`Invoke-Expression` on user input, aliases in scripts, or inline secrets.

## TypeScript

Source: `../THE-NEXUS/04-STANDARDS/code-style/typescript.md`.

- `tsconfig.json`: `"strict": true`, `"noUncheckedIndexedAccess": true`, `"noImplicitOverride": true`, `"exactOptionalPropertyTypes": true`.
- Tooling: `pnpm`, `eslint` + `@typescript-eslint`, `prettier`, `tsc --noEmit`, `vitest`.
- No `any`. Use `unknown` + narrowing (validate with `zod` at boundaries).
- Exhaustive switch on unions/enums with `never` default. No inline imports.
- `const` first; `console.log` not in shipped code; structured logging (`pino`).
- Errors include `cause`. Never empty `catch {}`.
- Naming: files `kebab-case.ts`; types/components `PascalCase`; vars/functions `camelCase`; true constants `SCREAMING_SNAKE`.
- Secrets: typed env loader or explicit throw on missing `process.env` keys.

## Markdown

Source: `../THE-NEXUS/04-STANDARDS/code-style/markdown.md` and `documentation-standards.md`.

- Vault frontmatter: `created`, `updated`, `tags`, `status`, `related`.
- File header HTML comment with `FILE:` and `PURPOSE:`.
- One H1 per file. No skip-levels. `[[wikilinks]]` internal; markdown links external.
- Fenced code with language tag. Mermaid default for diagrams.
- Forbidden: emojis (unless project allows), marketing tone, trailing whitespace, multiple blank lines, bare TODO without date/owner.
- AI claims: mark Confirmed / Inferred / Speculative explicitly.

