import os
import sqlite3
from pathlib import Path

from cryptography.fernet import Fernet


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def main() -> None:
    load_dotenv(Path(".env"))
    master = (os.getenv("WEBSITE33_MASTER_KEY") or "").strip().encode("utf-8")
    if not master:
        raise SystemExit("Missing WEBSITE33_MASTER_KEY in env/.env")

    conn = sqlite3.connect("call_logs.db")
    cur = conn.cursor()
    cur.execute("SELECT openrouter_api_key FROM global_settings WHERE id=1")
    row = cur.fetchone()
    conn.close()

    raw = (row[0] if row else "")
    raw = (raw or "").strip()
    if not raw.startswith("enc:v1:"):
        raise SystemExit("openrouter_api_key is not encrypted (unexpected)")

    token = raw[len("enc:v1:") :].encode("utf-8")
    plain = Fernet(master).decrypt(token).decode("utf-8")
    print(f"OK: decrypted openrouter_api_key from DB (len={len(plain)})")


if __name__ == "__main__":
    main()
