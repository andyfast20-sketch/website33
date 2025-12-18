"""Check the last call and which mode it used"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Get the most recent call for user 4
cursor.execute('''
    SELECT call_uuid, caller_number, start_time, duration, status, call_mode
    FROM calls 
    WHERE user_id = 4
    ORDER BY start_time DESC
    LIMIT 1
''')

row = cursor.fetchone()
if row:
    call_uuid, caller, start_time, duration, status, call_mode = row
    print(f"\n📞 LAST CALL DETAILS:")
    print(f"   Call UUID: {call_uuid}")
    print(f"   Caller: {caller}")
    print(f"   Start Time: {start_time}")
    print(f"   Duration: {duration}s")
    print(f"   Status: {status}")
    print(f"   Call Mode: {call_mode or 'realtime (default)'}")
    print()
    
    if call_mode == 'economy':
        print("✅ YES - This call used DEEPGRAM economy mode ($0.03/min)")
    else:
        print("❌ NO - This call used OpenAI Realtime mode ($0.30/min)")
else:
    print("No calls found for user 4")

conn.close()
