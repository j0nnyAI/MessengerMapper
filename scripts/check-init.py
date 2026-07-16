"""
Check that initialize-project.py has been run.

Scans all git-tracked files for unsubstituted MessengerMapper tokens.
Exits 0 if clean, 1 if tokens remain.

Usage:
    python scripts/check-init.py
    python scripts/check-init.py --quiet   # suppress per-file output; exit code only
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Concatenated so initialize-project.py substitution does not rewrite this
# value - this script must always scan for the literal template token, not
# the resolved project name.
TOKEN = "{{" + "PROJECT_NAME}}"
_REPO_ROOT = Path(__file__).resolve().parent.parent


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_REPO_ROOT),
    )
    if result.returncode != 0:
        sys.stderr.write("[check-init] git ls-files failed - are you inside a git repo?\n")
        return []
    return [_REPO_ROOT / line for line in result.stdout.splitlines() if line]


def scan(quiet: bool = False) -> list[Path]:
    hits: list[Path] = []
    for path in tracked_files():
        try:
            if TOKEN in path.read_text(encoding="utf-8", errors="ignore"):
                hits.append(path)
                if not quiet:
                    print(f"  [unsubstituted] {path.relative_to(_REPO_ROOT)}")
        except OSError:
            pass
    return hits


def main() -> int:
    quiet = "--quiet" in sys.argv

    hits = scan(quiet=quiet)
    if hits:
        sys.stderr.write(
            f"\n[check-init] WARNING: {len(hits)} file(s) still contain '{TOKEN}'.\n"
            f"[check-init] Run: python ../THE-NEXUS/scripts/initialize-project.py "
            f"--project-root . --vault-root ../<PROJECT_NAME>-VAULT\n\n"
        )
        return 1

    if not quiet:
        print(f"[check-init] OK - no '{TOKEN}' tokens found in tracked files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
