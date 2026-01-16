import sqlite3
import json

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

c.execute('SELECT call_uuid, created_at, transcript FROM calls ORDER BY created_at DESC LIMIT 1')
row = c.fetchone()

if row:
    print(f'Latest call: {row[0]}')
    print(f'Time: {row[1]}')
    print('\n=== TRANSCRIPT ===')
    
    transcript = json.loads(row[2]) if row[2] else []
    for t in transcript[-25:]:
        speaker = t.get('speaker', 'unknown')
        text = t.get('text', '')
        print(f"{speaker}: {text}")
else:
    print('No calls found')

conn.close()
