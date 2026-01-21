"""Reset the Super Admin password stored in SQLite.

This is a standalone script (no imports from the server module) so it works
even if `vonage_agent.py` is large or has side effects at import time.

Usage:
  python reset_super_admin_password.py <new_password> [username]
"""

import base64
import hashlib
import os
import secrets
import sqlite3
import sys
from datetime import datetime


def _b64url_no_pad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _make_password_hash_spec(password: str, iterations: int) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_b64url_no_pad(salt)}${_b64url_no_pad(dk)}"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python reset_super_admin_password.py <new_password> [username]")
        return 2

    password = (sys.argv[1] or "").strip()
    if len(password) < 6:
        print("Password too short (min 6 characters)")
        return 2

    username = (sys.argv[2] if len(sys.argv) >= 3 else "admin").strip() or "admin"

    try:
        iterations = int((os.getenv("SUPER_ADMIN_PBKDF2_ITERATIONS") or "310000").strip() or "310000")
    except Exception:
        iterations = 310000
    if iterations < 100_000:
        iterations = 310000

    spec = _make_password_hash_spec(password, iterations)
    now = datetime.now().isoformat()

    conn = sqlite3.connect("call_logs.db")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS super_admin_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        "INSERT OR REPLACE INTO super_admin_config (id, username, password_hash, created_at, updated_at) "
        "VALUES (1, ?, ?, COALESCE((SELECT created_at FROM super_admin_config WHERE id = 1), ?), ?)",
        (username, spec, now, now),
    )
    conn.commit()
    conn.close()

    print(f"OK: super-admin password updated for username={username!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
