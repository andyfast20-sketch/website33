import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Update voice from nova to shimmer
cursor.execute('UPDATE account_settings SET voice=? WHERE user_id=?', ('shimmer', 3))
conn.commit()

# Verify the change
cursor.execute('SELECT user_id, voice, use_elevenlabs FROM account_settings WHERE user_id=?', (3,))
result = cursor.fetchone()
print(f"Updated James's settings: user_id={result[0]}, voice={result[1]}, use_elevenlabs={result[2]}")

conn.close()
