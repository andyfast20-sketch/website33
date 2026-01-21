import argparse
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], *, cwd: Path, check: bool = True, capture: bool = False) -> str:
    if capture:
        proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
        if check and proc.returncode != 0:
            raise RuntimeError(
                f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout}{proc.stderr}"
            )
        return (proc.stdout or "").strip()

    proc = subprocess.run(cmd, cwd=str(cwd))
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}")
    return ""


def find_repo_root() -> Path:
    # scripts/rollback_to_working_tag.py -> repo root is two levels up
    return Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rollback code to a known-good git tag and optionally restart the server."
    )
    parser.add_argument(
        "--tag",
        default="answerly-working-pre-postgres",
        help="Git tag to roll back to (default: answerly-working-pre-postgres)",
    )
    parser.add_argument(
        "--no-restart",
        action="store_true",
        help="Only git checkout; do not restart the server",
    )
    args = parser.parse_args()

    repo_root = find_repo_root()
    os.chdir(repo_root)
    print(f"Repo: {repo_root}")

    # Validate git exists
    try:
        run(["git", "--version"], cwd=repo_root, check=True)
    except Exception as exc:
        print(f"ERROR: git is required but not available: {exc}")
        return 2

    # Stash local changes (including untracked) to avoid losing work
    try:
        status = run(["git", "status", "--porcelain"], cwd=repo_root, capture=True)
        if status:
            stamp = run(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, capture=True)
            msg = f"auto-stash-before-rollback-{stamp}"
            run(["git", "stash", "push", "-u", "-m", msg], cwd=repo_root, check=False)
            print("Stashed local changes.")
    except Exception as exc:
        print(f"Warning: could not stash changes: {exc}")

    # Fetch tags (best-effort)
    print("Fetching latest tags...")
    try:
        run(["git", "fetch", "--all", "--tags"], cwd=repo_root, check=False)
    except Exception as exc:
        print(f"Warning: fetch failed (offline?): {exc}")

    # Ensure tag exists
    tag_list = run(["git", "tag", "--list", args.tag], cwd=repo_root, capture=True)
    if not tag_list:
        print(f"ERROR: tag '{args.tag}' not found. Try: git tag --list")
        return 3

    print(f"Checking out tag: {args.tag}")
    run(["git", "checkout", "-f", args.tag], cwd=repo_root)

    if args.no_restart:
        print("Rollback complete (no restart requested).")
        return 0

    # Restart server using the current Python interpreter (prefer venv)
    python_exe = Path(sys.executable)
    print(f"Restarting server using: {python_exe}")

    start_script = repo_root / "start_server_clean.py"
    if not start_script.exists():
        print(f"ERROR: {start_script} not found; cannot restart server.")
        return 4

    run([str(python_exe), str(start_script)], cwd=repo_root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
