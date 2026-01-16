import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables: {tables}")

# Get most recent call
cursor.execute('SELECT call_uuid, caller_number, start_time, end_time FROM calls ORDER BY start_time DESC LIMIT 1')
call = cursor.fetchone()
if call:
    call_uuid, caller, start_time, end_time = call
    print(f"\n=== Most Recent Call ===")
    print(f"UUID: {call_uuid}")
    print(f"Caller: {caller}")
    print(f"Start: {start_time}")
    print(f"End: {end_time}")
    
    # Check for transcript_parts table
    if 'transcript_parts' in tables:
        cursor.execute('SELECT part_index, speaker, text FROM transcript_parts WHERE call_uuid = ? ORDER BY part_index', (call_uuid,))
        parts = cursor.fetchall()
        print(f"\n=== Transcript ({len(parts)} parts) ===")
        for idx, speaker, text in parts[-10:]:  # Last 10 parts
            print(f"[{idx}] {speaker}: {text[:150]}..." if len(text) > 150 else f"[{idx}] {speaker}: {text}")

conn.close()
