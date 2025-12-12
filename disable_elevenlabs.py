import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check table structure
cursor.execute("PRAGMA table_info(account_settings)")
columns = cursor.fetchall()
print("account_settings columns:", [col[1] for col in columns])

# Disable ElevenLabs for user_id 3
cursor.execute("UPDATE account_settings SET use_elevenlabs = 0 WHERE user_id = 3")
conn.commit()

# Verify
cursor.execute("SELECT user_id, use_elevenlabs FROM account_settings WHERE user_id = 3")
result = cursor.fetchone()
if result:
    print(f"\nUser {result[0]}: ElevenLabs enabled = {result[1]}")
    print("\n✅ Switched to OpenAI voice (faster)")
else:
    print("\n❌ No account_settings found for user 3")

conn.close()
