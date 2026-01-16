import sqlite3
from typing import List, Tuple


def table_columns(cur: sqlite3.Cursor, table: str) -> List[str]:
    return [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]


def main() -> None:
    conn = sqlite3.connect("call_logs.db")
    cur = conn.cursor()

    call_row = cur.execute(
        "SELECT call_uuid, caller_number, start_time, end_time FROM calls ORDER BY start_time DESC LIMIT 1"
    ).fetchone()
    if not call_row:
        print("No calls found")
        return

    call_uuid, caller_number, start_time, end_time = call_row
    print("=== Latest call ===")
    print("call_uuid:", call_uuid)
    print("caller_number:", caller_number)
    print("start_time:", start_time)
    print("end_time:", end_time)

    for t in ["calls", "call_latency_events", "call_brain_usage", "call_logs"]:
        try:
            cols = table_columns(cur, t)
            print(f"\n{t} columns ({len(cols)}):")
            print(cols)
        except Exception as e:
            print(f"\n{t} columns: ERROR: {e}")

    # Dump latency events
    try:
        rows = cur.execute(
            """
            SELECT turn_index, event_name, ms_from_turn_start
            FROM call_latency_events
            WHERE call_uuid = ?
            ORDER BY turn_index ASC, ms_from_turn_start ASC
            """,
            (call_uuid,),
        ).fetchall()
        print(f"\ncall_latency_events rows: {len(rows)}")
        for r in rows:
            print(r)
    except Exception as e:
        print("Latency events query error:", e)

    # Dump brain usage row (whatever schema is)
    try:
        cols = table_columns(cur, "call_brain_usage")
        if "call_uuid" in cols:
            rows = cur.execute(
                "SELECT * FROM call_brain_usage WHERE call_uuid = ? ORDER BY id DESC LIMIT 5",
                (call_uuid,),
            ).fetchall()
        else:
            rows = cur.execute("SELECT * FROM call_brain_usage ORDER BY id DESC LIMIT 5").fetchall()
        print(f"\ncall_brain_usage recent rows: {len(rows)}")
        for r in rows:
            print(r)
    except Exception as e:
        print("Brain usage query error:", e)

    # Dump call_logs rows for this call, if possible
    try:
        cols = table_columns(cur, "call_logs")
        where_col = None
        for c in ["call_uuid", "uuid", "call_id"]:
            if c in cols:
                where_col = c
                break
        if where_col is None:
            print("\ncall_logs: no call identifier column found")
        else:
            rows = cur.execute(
                f"SELECT * FROM call_logs WHERE {where_col} = ? ORDER BY id DESC LIMIT 60",
                (call_uuid,),
            ).fetchall()
            print(f"\ncall_logs rows for latest call: {len(rows)} (showing oldest->newest)")
            for r in rows[::-1]:
                print(r)
    except Exception as e:
        print("call_logs query error:", e)

    conn.close()


if __name__ == "__main__":
    main()
