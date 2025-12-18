import sqlite3

conn = sqlite3.connect('voice_agent.db')
cursor = conn.cursor()

# Update user 4 to use Deepgram
cursor.execute("UPDATE users SET call_mode='deepgram' WHERE id=4")
conn.commit()

# Verify the change
result = cursor.execute("SELECT username, call_mode FROM users WHERE id=4").fetchone()
print(f"✅ {result[0]} now using: {result[1]}")

conn.close()
