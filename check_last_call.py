import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Get last 3 calls
cursor.execute('SELECT call_uuid, caller_number, start_time, duration, status, transcript FROM calls ORDER BY id DESC LIMIT 3')
rows = cursor.fetchall()

for r in rows:
    print(f"\n{'='*80}")
    print(f"UUID: {r[0]}")
    print(f"Caller: {r[1]}")
    print(f"Start: {r[2]}")
    print(f"Duration: {r[3]}s")
    print(f"Status: {r[4]}")
    if r[5]:
        print(f"Transcript ({len(r[5])} chars):")
        print(r[5])
    else:
        print("No transcript")

conn.close()

