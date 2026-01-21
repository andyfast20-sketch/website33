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

This will:
- stash any local edits
- checkout the tagged working version
- restart the server via start_server_clean.py

B) Local snapshot backup (belt-and-braces)
-----------------------------------------
Before starting the Postgres migration, create a local zip snapshot:
   powershell -ExecutionPolicy Bypass -File scripts\backup_working_snapshot.ps1

It creates a zip in _snapshots\ with code/config (excluding .venv, .db files, logs, and known secrets).

Tip: Keep Postgres migration in a separate branch so rollback is a single git checkout.
