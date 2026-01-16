import sqlite3

conn = sqlite3.connect('call_center.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Available tables:", tables)
print()

# Check for latency-related tables
latency_tables = [t for t in tables if 'latency' in t.lower() or 'call' in t.lower()]
if latency_tables:
    print("Latency/Call related tables:", latency_tables)
    for table in latency_tables:
        cursor.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"\n{table} (latest 5 rows):")
            print("Columns:", columns)
            for row in rows:
                print(row)

conn.close()
