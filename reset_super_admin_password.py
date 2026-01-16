"""Reset the Super Admin password stored in SQLite.

This updates `super_admin_config.password_hash` to a PBKDF2-SHA256 spec.

Usage:
  python reset_super_admin_password.py

Notes:
- Runs locally against the same DB file the server uses (via `get_db_connection`).
- Does NOT require existing super-admin login.
"""

from __future__ import annotations

import getpass
from datetime import datetime

import vonage_agent


def main() -> None:
    username_default = vonage_agent._get_configured_super_admin_username() or "admin"
    username = input(f"Super-admin username [{username_default}]: ").strip() or username_default

    password = getpass.getpass("New super-admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")
    if len(password) < 6:
        raise SystemExit("Password too short (use at least 6 characters)")

    iterations_env = (vonage_agent.os.getenv("SUPER_ADMIN_PBKDF2_ITERATIONS") or "").strip()
    try:
        iterations = int(iterations_env or "310000")
    except Exception:
        iterations = 310000
    if iterations < 100_000:
        iterations = 310000

    spec = vonage_agent._make_password_hash_spec(password, iterations)
    if vonage_agent._parse_password_hash(spec) is None:
        raise SystemExit("Failed to generate password hash")

    now = datetime.now().isoformat()
    conn = vonage_agent.get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO super_admin_config (id, username, password_hash, created_at, updated_at) "
        "VALUES (1, ?, ?, COALESCE((SELECT created_at FROM super_admin_config WHERE id = 1), ?), ?)",
        (username, spec, now, now),
    )
    conn.commit()
    conn.close()

    print("OK: super-admin password updated.")


if __name__ == "__main__":
    main()
