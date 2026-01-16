import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print("Tables:", tables)

# Check recent call
c.execute("SELECT call_uuid, created_at FROM calls ORDER BY created_at DESC LIMIT 1")
call = c.fetchone()
if call:
    uuid, created = call
    print(f"\nLast call: {uuid} at {created}")
    
    # Check transcript_parts if it exists
    if 'transcript_parts' in tables:
        c.execute("SELECT role, text FROM transcript_parts WHERE call_uuid = ? ORDER BY id", (uuid,))
        parts = c.fetchall()
        print(f"\nTranscript ({len(parts)} parts):")
        for role, text in parts[:10]:
            print(f"  [{role}] {text[:100]}")

conn.close()
