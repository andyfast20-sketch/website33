import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Get the most recent call
cursor.execute('''
    SELECT call_uuid, caller_number, created_at, status 
    FROM calls 
    ORDER BY created_at DESC 
    LIMIT 1
''')
last_call = cursor.fetchone()

if last_call:
    call_uuid, caller, created, status = last_call
    duration = "N/A"
    print(f"\n=== MOST RECENT CALL ===")
    print(f"UUID: {call_uuid}")
    print(f"Caller: {caller}")
    print(f"Time: {created}")
    print(f"Status: {status}")
    print(f"Duration: {duration}s")
    
    # Check for conversation turns
    cursor.execute('''
        SELECT role, content, timestamp 
        FROM conversation_history 
        WHERE call_uuid = ? 
        ORDER BY timestamp ASC
    ''', (call_uuid,))
    turns = cursor.fetchall()
    
    if turns:
        print(f"\n=== CONVERSATION ({len(turns)} turns) ===")
        for i, (role, content, ts) in enumerate(turns, 1):
            preview = content[:80] + "..." if len(content) > 80 else content
            print(f"{i}. [{role}] {preview}")
    
    # Check for any error logs related to this call
    cursor.execute('''
        SELECT message, timestamp 
        FROM call_events 
        WHERE call_uuid = ? AND (message LIKE '%error%' OR message LIKE '%latency%' OR message LIKE '%slow%')
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (call_uuid,))
    events = cursor.fetchall()
    
    if events:
        print(f"\n=== EVENTS/ERRORS ===")
        for msg, ts in events:
            print(f"[{ts}] {msg}")
else:
    print("No calls found in database")

conn.close()
