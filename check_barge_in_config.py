import sqlite3
import sys
sys.path.insert(0, '.')
import vonage_agent

# Check database value
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()
cursor.execute('SELECT barge_in_min_speech_seconds FROM global_settings WHERE id = 1')
db_val = cursor.fetchone()[0]
conn.close()

print(f'Database value: {db_val}')
print(f'CONFIG value: {vonage_agent.CONFIG.get("BARGE_IN_MIN_SPEECH_SECONDS", "NOT SET")}')
