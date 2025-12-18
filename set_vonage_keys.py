import getpass
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "call_logs.db"


def _ensure_columns(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # If global_settings doesn't exist yet, vonage_agent.py will create it.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            global_instructions TEXT DEFAULT '',
            speechmatics_api_key TEXT DEFAULT NULL,
            openai_api_key TEXT DEFAULT NULL,
            vonage_api_key TEXT DEFAULT NULL,
            vonage_api_secret TEXT DEFAULT NULL,
            filler_words TEXT DEFAULT '',
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT DEFAULT 'admin'
        )
        """
    )
    cur.execute('INSERT OR IGNORE INTO global_settings (id, global_instructions) VALUES (1, "")')

    # Make sure columns exist if table was created previously.
    for col, coltype in (
        ("vonage_api_key", "TEXT DEFAULT NULL"),
        ("vonage_api_secret", "TEXT DEFAULT NULL"),
    ):
        try:
            cur.execute(f"ALTER TABLE global_settings ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass

    conn.commit()


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found at {DB_PATH}. Start the server once to create it.")

    print("Set Vonage credentials (stored in call_logs.db global_settings).")
    api_key = input("Vonage API key: ").strip()
    api_secret = getpass.getpass("Vonage API secret: ").strip()

    if not api_key or not api_secret:
        raise SystemExit("Both key and secret are required.")

    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_columns(conn)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE global_settings
            SET vonage_api_key = ?,
                vonage_api_secret = ?,
                last_updated = CURRENT_TIMESTAMP,
                updated_by = 'admin'
            WHERE id = 1
            """,
            (api_key, api_secret),
        )
        conn.commit()
    finally:
        conn.close()

    print("Saved. Restart the server for changes to take effect.")


if __name__ == "__main__":
    main()
