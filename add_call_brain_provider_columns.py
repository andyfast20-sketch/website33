import sqlite3

def ensure_column(cursor: sqlite3.Cursor, table: str, column: str, ddl: str) -> None:
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        print(f"Added column {table}.{column}")
    except Exception:
        # Column likely already exists
        pass


def main() -> None:
    db_path = "call_logs.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Calls table additions for auditing brain selection
    ensure_column(cur, "calls", "selected_brain_provider", "TEXT")
    ensure_column(cur, "calls", "effective_brain_provider", "TEXT")
    ensure_column(cur, "calls", "brain_gating_reasons", "TEXT")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
