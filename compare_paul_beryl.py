import sqlite3

conn = sqlite3.connect('call_logs.db')
cur = conn.cursor()

cur.execute('''
    SELECT u.id, u.name, a.phone_number, a.voice_provider, 
           a.speechmatics_voice_id, a.call_mode, a.response_latency
    FROM users u 
    JOIN account_settings a ON u.id = a.user_id 
    WHERE u.id IN (5, 7)
''')

print("Account Comparison:")
print("-" * 80)
for row in cur.fetchall():
    user_id, name, phone, provider, speech_voice, mode, latency = row
    print(f"User {user_id} ({name}):")
    print(f"  Phone: {phone}")
    print(f"  Provider: {provider}")
    print(f"  Speechmatics Voice: {speech_voice}")
    print(f"  Call Mode: {mode}")
    print(f"  Latency: {latency}")
    print()
