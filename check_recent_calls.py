import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Get recent calls
cursor.execute('''
    SELECT call_uuid, timestamp, caller_number, status, duration 
    FROM call_logs 
    ORDER BY timestamp DESC 
    LIMIT 5
''')

calls = cursor.fetchall()
print("Recent calls:")
print("-" * 80)
for call in calls:
    call_uuid, timestamp, caller, status, duration = call
    print(f"UUID: {call_uuid}")
    print(f"Time: {timestamp}")
    print(f"Caller: {caller}")
    print(f"Status: {status}")
    print(f"Duration: {duration}s")
    print("-" * 80)

if calls:
    latest_uuid = calls[0][0]
    print(f"\nChecking transcript for latest call: {latest_uuid}")
    
    cursor.execute('SELECT transcript FROM call_logs WHERE call_uuid = ?', (latest_uuid,))
    transcript = cursor.fetchone()
    if transcript and transcript[0]:
        print(f"Transcript:\n{transcript[0][:500]}")
    else:
        print("No transcript found")

conn.close()
