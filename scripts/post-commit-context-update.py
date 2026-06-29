"""
Post-commit hook for MessengerMapper.

Fires AFTER `git commit` lands. Runs in the background. Two responsibilities:

  1. Dispatch an async secondary verification pass on HANDOFF.md v3 sections (parity check; STEP 1 is primary).
  2. If the commit message contains a `Review:` trailer, dispatch the matching
     review/audit agent. Recognized values:
       Review: yes     -> reviewer only
       Review: code    -> reviewer only (alias)
       Review: security-> security-auditor only
       Review: full    -> reviewer + security-auditor in parallel
     Anything else / missing trailer = no review spawned.

Never blocks the completed commit. Path resolution delegates to
``nexus_paths.resolve_project_context()`` (CLI overrides, then ``NEXUS_VAULT_PATH``,
then structural sibling layout). If a review was requested and dispatch fails,
writes ``<sha>-DISPATCH-FAILURE.md`` into the vault under ``05-MEMORY/hook-logs/``.

Exit codes (post-commit hook contract):
  0 = hook finished (including resolver/dispatch failures — commit already landed)
  2 = invalid ``--project-root`` / ``--vault-root`` invocation
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types

PROJECT_NAME = "MessengerMapper"

_SCRIPT_DIR = Path(__file__).resolve().parent

EXIT_HOOK_OK = 0
EXIT_INVALID_ARGS = 2

PROJECT_ROOT: Path | None = None
NEXUS_DIR: Path | None = None
VAULT_DIR: Path | None = None
HANDOFF_FILE: Path | None = None
DISPATCH_FAILURE_DIR: Path | None = None
REVIEW_COMMIT_SCRIPT: Path | None = None
HANDOFF_ASYNC_UPDATE_SCRIPT: Path | None = None

VAULT_HANDOFF_REL = Path("04-CONTEXT") / "HANDOFF.md"
VAULT_OUTPUTS_REL = Path("05-MEMORY") / "hook-logs"

_REVIEW_TRAILER_RE = re.compile(r"^\s*Review\s*:\s*(\S+)\s*$", re.IGNORECASE | re.MULTILINE)


def _discover_engine_scripts_via_find_nexus() -> Path | None:
    """Locate engine scripts via find-nexus.py (sys.path or NEXUS_PATH only)."""
    find_nexus: Path | None = None

    nexus_path = os.environ.get("NEXUS_PATH")
    if nexus_path:
        candidate = Path(nexus_path).expanduser().resolve() / "scripts" / "find-nexus.py"
        if candidate.is_file():
            find_nexus = candidate

    if find_nexus is None:
        for entry in sys.path:
            if not entry:
                continue
            candidate = Path(entry) / "find-nexus.py"
            if candidate.is_file():
                find_nexus = candidate
                break

    if find_nexus is None:
        return None

    completed = subprocess.run(
        [sys.executable, str(find_nexus), "--nexus-dir"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_SCRIPT_DIR.parent),
    )
    if completed.returncode != 0:
        return None
    scripts = Path(completed.stdout.strip()) / "scripts"
    if (scripts / "nexus_paths.py").is_file():
        return scripts
    return None


def _early_engine_bootstrap() -> None:
    """Tier-1 import bootstrap: NEXUS_PATH, hook PYTHONPATH, or find-nexus subprocess."""
    if "nexus_paths" in sys.modules:
        return
    try:
        import nexus_paths  # noqa: F401
        return
    except ImportError:
        pass

    nexus_path = os.environ.get("NEXUS_PATH")
    if nexus_path:
        scripts = Path(nexus_path).expanduser().resolve() / "scripts"
        module_file = scripts / "nexus_paths.py"
        if module_file.is_file():
            scripts_str = str(scripts)
            if scripts_str not in sys.path:
                sys.path.insert(0, scripts_str)
            return

    scripts = _discover_engine_scripts_via_find_nexus()
    if scripts is not None:
        scripts_str = str(scripts)
        if scripts_str not in sys.path:
            sys.path.insert(0, scripts_str)


_nexus_paths_module: types.ModuleType | None = None


def _get_nexus_paths() -> types.ModuleType:
    """Return the cached nexus_paths module, importing it on first call."""
    global _nexus_paths_module
    if _nexus_paths_module is None:
        import nexus_paths as _np  # noqa: WPS433
        _nexus_paths_module = _np
    return _nexus_paths_module


_early_engine_bootstrap()


def _import_nexus_paths_module(module_path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("nexus_paths", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load engine module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["nexus_paths"] = module
    spec.loader.exec_module(module)
    return module


def bootstrap_engine_import(
    *,
    project_root_override: Path | None = None,
    vault_root_override: Path | None = None,
) -> None:
    """Ensure ``nexus_paths`` is importable from tenant ``scripts/`` without inlined walks."""
    if "nexus_paths" in sys.modules:
        return

    _early_engine_bootstrap()
    if "nexus_paths" in sys.modules:
        return

    nexus_path = os.environ.get("NEXUS_PATH")
    if nexus_path:
        module_file = Path(nexus_path).expanduser().resolve() / "scripts" / "nexus_paths.py"
        if module_file.is_file():
            _import_nexus_paths_module(module_file)
            return

    raise ImportError(
        "Cannot import nexus_paths from tenant scripts/. Set NEXUS_PATH, export "
        "PYTHONPATH to include THE-NEXUS/scripts (post-commit hook does this by "
        "default), or pass --project-root / --vault-root."
    )


def _decode_utf8_no_bom(data: bytes) -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.decode("utf-8", errors="replace")


def init_topology(
    *,
    project_root_override: Path | None = None,
    vault_root_override: Path | None = None,
) -> bool:
    global PROJECT_ROOT, NEXUS_DIR, VAULT_DIR
    global HANDOFF_FILE, DISPATCH_FAILURE_DIR
    global REVIEW_COMMIT_SCRIPT, HANDOFF_ASYNC_UPDATE_SCRIPT

    np = _get_nexus_paths()
    try:
        project_root, nexus_dir, vault_dir = np.resolve_project_context(
            _SCRIPT_DIR,
            project_root_override=project_root_override,
            vault_root_override=vault_root_override,
        )
    except np.NexusPathError as exc:
        _log_telemetry_unbound(f"[FAIL] path resolution failed: {exc}")
        return False

    PROJECT_ROOT = project_root
    NEXUS_DIR = nexus_dir
    VAULT_DIR = vault_dir
    HANDOFF_FILE = vault_dir / VAULT_HANDOFF_REL
    DISPATCH_FAILURE_DIR = vault_dir / VAULT_OUTPUTS_REL
    REVIEW_COMMIT_SCRIPT = nexus_dir / "scripts" / "review-commit.py"
    HANDOFF_ASYNC_UPDATE_SCRIPT = nexus_dir / "scripts" / "handoff-async-update.py"
    return True


def _ensure_bounded(path: Path) -> Path | None:
    if PROJECT_ROOT is None or VAULT_DIR is None:
        return None
    np = _get_nexus_paths()
    try:
        resolved = np.normalize_path(path)
        project_root = np.normalize_path(PROJECT_ROOT)
        vault_root = np.normalize_path(VAULT_DIR)
        if resolved.is_relative_to(project_root) or resolved.is_relative_to(vault_root):
            return resolved
        if NEXUS_DIR is not None:
            nexus_root = np.normalize_path(NEXUS_DIR)
            if resolved.is_relative_to(nexus_root):
                return resolved
    except (OSError, ValueError):
        pass
    _log_telemetry("FAIL", f"path escapes allowed roots: {path}")
    return None


def _log_telemetry(level: str, message: str) -> None:
    if level == "FAIL":
        sys.stderr.write(f"[post-commit] [{level}] {message}\n")


def _log_telemetry_unbound(message: str) -> None:
    sys.stderr.write(f"[post-commit] {message}\n")


def _run_git(*args: str) -> subprocess.CompletedProcess[bytes] | None:
    if PROJECT_ROOT is None:
        return None
    try:
        return subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), *args],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None


def _git_text(*args: str) -> str | None:
    completed = _run_git(*args)
    if completed is None or completed.returncode != 0:
        return None
    return _decode_utf8_no_bom(completed.stdout or b"")


def commit_message(sha: str = "HEAD") -> str:
    return _git_text("log", "-1", "--format=%B", sha) or ""


def commit_sha() -> str:
    return (_git_text("rev-parse", "--short", "HEAD") or "unknown").strip()


def parse_review_trailer(message: str) -> str | None:
    for match in _REVIEW_TRAILER_RE.finditer(message):
        value = match.group(1).lower()
        if value in ("yes", "code", "reviewer", "review"):
            return "reviewer"
        if value in ("security", "sec", "audit"):
            return "security"
        if value in ("full", "both", "all"):
            return "full"
    return None


def spawn(cmd: list[str]) -> None:
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        _log_telemetry("FAIL", f"spawn failed for {cmd!r}: {exc}")


def write_dispatch_failure(sha: str, scope: str, reason: str, detail: str) -> Path | None:
    if DISPATCH_FAILURE_DIR is None:
        _log_telemetry("FAIL", f"dispatch failure artifact unavailable: {reason}")
        return None

    out_dir = _ensure_bounded(DISPATCH_FAILURE_DIR)
    if out_dir is None:
        return None

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        _log_telemetry("FAIL", f"cannot create dispatch failure directory {out_dir}: {exc}")
        return None

    target = _ensure_bounded(out_dir / f"{sha}-DISPATCH-FAILURE.md")
    if target is None:
        return None

    timestamp = datetime.now().isoformat(timespec="seconds")
    content = (
        f"---\n"
        f"created: {timestamp}\n"
        f"sha: {sha}\n"
        f"scope: {scope}\n"
        f"status: FAILED\n"
        f"---\n\n"
        f"# Review dispatch FAILED -- {sha}\n\n"
        f"**Requested scope:** `{scope}`\n\n"
        f"**Reason:** {reason}\n\n"
        f"## Resolver trace\n\n"
        f"```\n{detail.strip()}\n```\n\n"
        f"## Why this matters\n\n"
        f"The commit succeeded, but the review you opted in to via the `Review:` trailer "
        f"was NOT run. Without remediation, future commits with the same trailer will keep "
        f"failing silently (apart from this file).\n\n"
        f"## Remediation\n\n"
        f"1. Confirm THE-NEXUS is reachable from this project root (``NEXUS_PATH``, sibling "
        f"layout, or junction/symlink).\n"
        f"2. Run the doctor: "
        f"`python THE-NEXUS/scripts/doctor.py --project-root {PROJECT_ROOT} "
        f"--vault-root {VAULT_DIR}`\n"
        f"3. Rerun the review manually once fixed:\n"
        f"   ```\n"
        f"   python THE-NEXUS/scripts/review-commit.py --sha {sha} --scope {scope}"
        f" --project-root {PROJECT_ROOT} --vault-root {VAULT_DIR}\n"
        f"   ```\n"
    )

    np = _get_nexus_paths()
    try:
        np.atomic_write_text(target, content)
        return target
    except (OSError, np.AtomicWriteError) as exc:
        _log_telemetry("FAIL", f"cannot write dispatch failure artifact {target}: {exc}")
        return None


def _topology_detail() -> str:
    return (
        f"PROJECT_NAME = {PROJECT_NAME}\n"
        f"PROJECT_ROOT = {PROJECT_ROOT}\n"
        f"NEXUS_DIR = {NEXUS_DIR}\n"
        f"VAULT_DIR = {VAULT_DIR}\n"
        f"HANDOFF_FILE = {HANDOFF_FILE}\n"
        f"HANDOFF_ASYNC_UPDATE_SCRIPT = {HANDOFF_ASYNC_UPDATE_SCRIPT}\n"
        f"REVIEW_COMMIT_SCRIPT = {REVIEW_COMMIT_SCRIPT}"
    )


def dispatch_context_update() -> None:
    if PROJECT_ROOT is None or VAULT_DIR is None or HANDOFF_ASYNC_UPDATE_SCRIPT is None:
        _log_telemetry("FAIL", "context update skipped: topology not initialized")
        return

    script = _ensure_bounded(HANDOFF_ASYNC_UPDATE_SCRIPT)
    if script is None:
        return

    if not script.is_file():
        _log_telemetry("FAIL", f"handoff-async-update.py missing at {script}")
        return

    spawn(
        [
            sys.executable,
            str(script),
            *_get_nexus_paths().path_override_argv(project_root=PROJECT_ROOT, vault_root=VAULT_DIR),
        ]
    )


def dispatch_review(scope: str, sha: str) -> None:
    if NEXUS_DIR is None or REVIEW_COMMIT_SCRIPT is None:
        reason = "THE-NEXUS topology is not initialized."
        failure_path = write_dispatch_failure(sha, scope, reason, _topology_detail())
        _emit_dispatch_failure(scope, reason, failure_path)
        return

    script = _ensure_bounded(REVIEW_COMMIT_SCRIPT)
    if script is None:
        reason = f"review-commit.py path rejected: {REVIEW_COMMIT_SCRIPT}"
        failure_path = write_dispatch_failure(sha, scope, reason, _topology_detail())
        _emit_dispatch_failure(scope, reason, failure_path)
        return

    if not script.is_file():
        reason = f"THE-NEXUS found at {NEXUS_DIR} but review-commit.py is missing."
        failure_path = write_dispatch_failure(sha, scope, reason, _topology_detail())
        _emit_dispatch_failure(scope, reason, failure_path)
        return

    spawn(
        [
            sys.executable,
            str(script),
            "--sha",
            sha,
            "--scope",
            scope,
            *_get_nexus_paths().path_override_argv(project_root=PROJECT_ROOT, vault_root=VAULT_DIR),
        ]
    )


def _emit_dispatch_failure(scope: str, reason: str, failure_path: Path | None) -> None:
    sys.stderr.write(
        f"\n[post-commit] LOUD FAILURE: requested `Review: {scope}` was NOT run.\n"
        f"[post-commit] {reason}\n"
    )
    if failure_path:
        sys.stderr.write(f"[post-commit] See: {failure_path}\n\n")
    else:
        sys.stderr.write(
            "[post-commit] Could not write dispatch-failure artifact — "
            "vault may be missing too.\n\n"
        )
    _log_telemetry("FAIL", reason)


def main() -> int:
    try:
        bootstrap_engine_import()
    except ImportError as exc:
        _log_telemetry_unbound(f"[FAIL] engine import failed: {exc}")
        return EXIT_HOOK_OK

    np = _get_nexus_paths()
    try:
        _remaining_argv, project_root_override, vault_root_override = np.pop_path_override_argv(
            sys.argv[1:]
        )
    except ValueError as exc:
        _log_telemetry_unbound(f"[FAIL] {exc}")
        return EXIT_INVALID_ARGS

    try:
        bootstrap_engine_import(
            project_root_override=project_root_override,
            vault_root_override=vault_root_override,
        )
    except ImportError as exc:
        _log_telemetry_unbound(f"[FAIL] engine import failed: {exc}")
        return EXIT_HOOK_OK

    if not init_topology(
        project_root_override=project_root_override,
        vault_root_override=vault_root_override,
    ):
        return EXIT_HOOK_OK

    sha = commit_sha()
    message = commit_message("HEAD")

    print(f"[post-commit] {sha} dispatched. Background work runs silently.")

    if NEXUS_DIR is None or not NEXUS_DIR.is_dir():
        sys.stderr.write("[post-commit] [FAIL] THE-NEXUS not reachable from this project; inheritance layer may dangle\n")

    dispatch_context_update()

    scope = parse_review_trailer(message)
    if scope:
        dispatch_review(scope, sha)

    return EXIT_HOOK_OK


if __name__ == "__main__":
    sys.exit(main())
