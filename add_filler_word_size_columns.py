"""Add sized filler word buckets to global_settings.

Adds columns:
- filler_words_small
- filler_words_medium
- filler_words_large

This is backwards compatible; the app will fall back to legacy filler_words
if these columns don't exist.
"""

import sqlite3


def main(db_path: str = "call_logs.db") -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        # Ensure table exists (minimal shape; app can expand as needed).
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS global_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                global_instructions TEXT DEFAULT '',
                filler_words TEXT DEFAULT '',
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT DEFAULT 'admin'
            )
            """
        )
        cur.execute('INSERT OR IGNORE INTO global_settings (id, global_instructions) VALUES (1, "")')

        for col in ("filler_words_small", "filler_words_medium", "filler_words_large"):
            try:
                cur.execute(f"ALTER TABLE global_settings ADD COLUMN {col} TEXT DEFAULT ''")
                print(f"✅ Added column: {col}")
            except sqlite3.OperationalError:
                print(f"ℹ️ Column already exists: {col}")

        conn.commit()
        print("\nDone.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
