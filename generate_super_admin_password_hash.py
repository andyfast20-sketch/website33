"""Generate a PBKDF2-SHA256 password hash for SUPER_ADMIN_PASSWORD_HASH.

Usage:
  python generate_super_admin_password_hash.py

It prints an env-friendly line like:
  SUPER_ADMIN_PASSWORD_HASH=pbkdf2_sha256$310000$<salt_b64>$<hash_b64>

You can paste it into `.env` (next to `vonage_agent.py`).
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import os
import secrets


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def main() -> None:
    password = getpass.getpass("New super-admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")
    if len(password) < 12:
        raise SystemExit("Password too short (use at least 12 characters)")

    iterations = int(os.getenv("SUPER_ADMIN_PBKDF2_ITERATIONS", "310000"))
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

    # store without '=' padding to keep it copy/paste friendly
    salt_b64 = _b64(salt)
    hash_b64 = _b64(dk)
    print()
    print(f"SUPER_ADMIN_PASSWORD_HASH=pbkdf2_sha256${iterations}${salt_b64}${hash_b64}")
    print("SUPER_ADMIN_USERNAME=admin")


if __name__ == "__main__":
    main()
