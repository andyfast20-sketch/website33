Rollback plan (safe)
====================

Goal: If the Postgres changeover breaks anything, you can instantly revert to the last known-working code.

A) GitHub rollback (recommended)
-------------------------------
1) Make sure this working version is tagged in git (we will push a tag).
2) To rollback, run:
   powershell -ExecutionPolicy Bypass -File scripts\rollback_to_working_tag.ps1 -Tag answerly-working-pre-postgres

   Or using Python (if you prefer running from the venv):
   .venv\Scripts\python.exe scripts\rollback_to_working_tag.py --tag answerly-working-pre-postgres

Notes:
- By default the rollback scripts only stash tracked edits (NOT untracked files). This avoids accidentally hiding backups stored in _snapshots\.
- If you really want to stash untracked too:
  - PowerShell: add -IncludeUntracked
  - Python: add --include-untracked

This will:
- stash any local edits
- checkout the tagged working version
- restart the server via start_server_clean.py

A2) Back up SQLite data (recommended before migration)
----------------------------------------------------
Before attempting Postgres migration, back up your local SQLite DB files:
   .venv\Scripts\python.exe scripts\backup_sqlite_dbs.py

This creates a folder under _snapshots\sqlite_db_backup_YYYYMMDD_HHMMSS\ containing *.db files (and WAL sidecars).

A3) Roll back code + restore SQLite data (if needed)
---------------------------------------------------
If Postgres migration changes data and you want your old SQLite data back:
   .venv\Scripts\python.exe scripts\rollback_to_working_tag.py --tag answerly-working-pre-postgres --restore-db-from _snapshots\sqlite_db_backup_YYYYMMDD_HHMMSS

B) Local snapshot backup (belt-and-braces)
-----------------------------------------
Before starting the Postgres migration, create a local zip snapshot:
   powershell -ExecutionPolicy Bypass -File scripts\backup_working_snapshot.ps1

It creates a zip in _snapshots\ with code/config (excluding .venv, .db files, logs, and known secrets).

Tip: Keep Postgres migration in a separate branch so rollback is a single git checkout.
