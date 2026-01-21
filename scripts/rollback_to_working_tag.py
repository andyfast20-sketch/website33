import argparse
import os
import subprocess
import sys
import time
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


def _kill_process_on_port_windows(port: int) -> None:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                f"(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue).OwningProcess",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        raw = (result.stdout or "").strip()
        if raw:
            pids = sorted(
                {pid.strip() for pid in raw.splitlines() if pid.strip().isdigit() and int(pid.strip()) > 0},
                key=lambda x: int(x),
            )
            for pid in pids:
                subprocess.run(
                    ["powershell", "-Command", f"Stop-Process -Id {pid} -Force"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                time.sleep(1)
            return
    except Exception:
        pass

    # Fallback: netstat/taskkill
    try:
        netstat = subprocess.run(
            ["cmd", "/c", f"netstat -ano | findstr :{port}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = [ln.strip() for ln in (netstat.stdout or "").splitlines() if ln.strip()]
        pids: set[str] = set()
        for ln in lines:
            parts = ln.split()
            if len(parts) >= 5 and parts[-1].isdigit() and parts[-1] != "0":
                pids.add(parts[-1])
        for pid in sorted(pids, key=lambda x: int(x)):
            subprocess.run(["cmd", "/c", f"taskkill /PID {pid} /F"], capture_output=True, text=True, timeout=5)
            time.sleep(1)
    except Exception:
        return


def restore_sqlite_dbs(*, repo_root: Path, source: Path) -> None:
    if not source.exists():
        raise RuntimeError(f"DB restore source not found: {source}")

    db_files: list[Path] = []
    if source.is_file():
        if source.suffix.lower() != ".db":
            raise RuntimeError("If --restore-db-from is a file, it must end with .db")
        db_files = [source]
    else:
        db_files = sorted(source.glob("*.db"))

    if not db_files:
        raise RuntimeError(f"No .db files found in: {source}")

    print("Stopping server on port 5004 (best-effort) before DB restore...")
    if os.name == "nt":
        _kill_process_on_port_windows(5004)
        time.sleep(2)

    copied = 0
    for db in db_files:
        dest = repo_root / db.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(db.read_bytes())
        copied += 1

        # Copy WAL sidecars if present (best-effort)
        for sidecar_name in (db.name + "-wal", db.name + "-shm"):
            sidecar = db.with_name(sidecar_name)
            if sidecar.exists() and sidecar.is_file():
                (repo_root / sidecar.name).write_bytes(sidecar.read_bytes())

    print(f"Restored {copied} SQLite DB file(s) into repo root.")


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
        "--include-untracked",
        action="store_true",
        help="Also stash untracked files before rollback (NOT recommended if your backups are in _snapshots/)",
    )
    parser.add_argument(
        "--restore-db-from",
        default=None,
        help="Restore SQLite .db files from a folder (or a single .db file) AFTER checking out the tag",
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
            if args.include_untracked:
                run(["git", "stash", "push", "-u", "-m", msg], cwd=repo_root, check=False)
            else:
                run(["git", "stash", "push", "-m", msg], cwd=repo_root, check=False)
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

    if args.restore_db_from:
        try:
            restore_sqlite_dbs(repo_root=repo_root, source=Path(args.restore_db_from).expanduser())
        except Exception as exc:
            print(f"ERROR: DB restore failed: {exc}")
            return 5

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
