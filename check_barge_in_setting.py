import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()
cursor.execute('SELECT barge_in_min_speech_seconds FROM global_settings')
result = cursor.fetchone()
print(f'Database barge_in_min_speech_seconds: {result[0] if result else "NULL"}')
conn.close()
