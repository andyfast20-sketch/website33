import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

call_uuid = '6e481980fa59440f870e76d8d108bdee'

c.execute('''
    SELECT event_name, ms_from_turn_start 
    FROM call_latency_events 
    WHERE call_uuid = ? AND turn_index = 5
    ORDER BY ms_from_turn_start
''', (call_uuid,))

rows = c.fetchall()

print(f'Turn 5 events for call {call_uuid}:')
if rows:
    for event_name, ms in rows:
        print(f'  +{int(ms):5d}ms {event_name}')
else:
    print('  Only caller_stopped (already shown), no other events')

print('\n\nChecking all events with "asr" or "missing" in the name:')
c.execute('''
    SELECT turn_index, event_name, ms_from_turn_start
    FROM call_latency_events
    WHERE call_uuid = ? AND (event_name LIKE '%asr%' OR event_name LIKE '%missing%')
    ORDER BY turn_index, ms_from_turn_start
''', (call_uuid,))

rows = c.fetchall()
if rows:
    for turn, event_name, ms in rows:
        print(f'  Turn {turn} +{int(ms):5d}ms {event_name}')
else:
    print('  None found')

conn.close()
