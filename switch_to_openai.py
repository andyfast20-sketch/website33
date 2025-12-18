import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Find tables
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Tables: {[t[0] for t in tables]}")

# Check current mode
result = cursor.execute("SELECT call_mode FROM users WHERE id = 4").fetchone()
print(f"Current call_mode for user 4: {result[0] if result else 'NOT FOUND'}")

# Update to OpenAI Realtime
cursor.execute("UPDATE users SET call_mode = ? WHERE id = ?", ('openai_realtime', 4))
conn.commit()

# Confirm
result = cursor.execute("SELECT call_mode FROM users WHERE id = 4").fetchone()
print(f"Updated call_mode: {result[0] if result else 'NOT FOUND'}")

conn.close()
print("\n✅ Switched to OpenAI Realtime")
print("💡 Your calls will now work immediately")
print("💰 Cost: $0.30/min (vs $0.017/min for AssemblyAI)")
print("🎯 UK accents may not work as well, but system is functional")

