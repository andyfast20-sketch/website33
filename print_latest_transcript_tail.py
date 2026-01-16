import sqlite3

conn = sqlite3.connect('call_logs.db')
cur = conn.cursor()
row = cur.execute(
    "SELECT call_uuid, COALESCE(transcript,''), COALESCE(summary,'') FROM calls ORDER BY start_time DESC LIMIT 1"
).fetchone()
call_uuid, transcript, summary = row
print('call_uuid:', call_uuid)
print('transcript_len:', len(transcript))
print('summary_len:', len(summary))
print('\n--- transcript (tail 1500 chars) ---')
print(transcript[-1500:])
conn.close()
