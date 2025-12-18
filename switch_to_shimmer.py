import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check current voice
result = cursor.execute("SELECT voice FROM account_settings WHERE user_id = 4").fetchone()
print(f"Current voice: {result[0]}")

# Switch to shimmer (HeyJodie-style voice)
cursor.execute("UPDATE account_settings SET voice = ? WHERE user_id = ?", ('shimmer', 4))
conn.commit()

# Confirm
result = cursor.execute("SELECT voice FROM account_settings WHERE user_id = 4").fetchone()
print(f"Updated voice: {result[0]}")

conn.close()
print("\n✅ Switched to 'shimmer' voice")
print("🎤 This is OpenAI's premium female voice - clear, professional, natural")
print("📞 Call 442039856179 to test it!")
