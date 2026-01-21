import argparse
import shutil
from datetime import datetime
from pathlib import Path


def find_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backup local SQLite .db files (and WAL sidecars) into _snapshots/."
    )
    parser.add_argument(
        "--out-dir",
        default="_snapshots",
        help="Output folder (default: _snapshots)",
    )
    args = parser.parse_args()

    repo_root = find_repo_root()
    out_root = (repo_root / args.out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = out_root / f"sqlite_db_backup_{stamp}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    db_files = sorted(repo_root.glob("*.db"))
    if not db_files:
        print("No .db files found in repo root.")
        return 0

    copied = 0
    for db in db_files:
        shutil.copy2(db, dest_dir / db.name)
        copied += 1

        # WAL sidecars (best-effort)
        for sidecar_name in (db.name + "-wal", db.name + "-shm"):
            sidecar = repo_root / sidecar_name
            if sidecar.exists() and sidecar.is_file():
                shutil.copy2(sidecar, dest_dir / sidecar.name)

    print(f"Backed up {copied} DB file(s) to: {dest_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
