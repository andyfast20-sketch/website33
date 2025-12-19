import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=== COMPARING BERYL vs PAUL ===\n")

# Get both accounts
cursor.execute('''
    SELECT a.user_id, u.name, a.phone_number, a.voice, a.voice_provider, 
           a.speechmatics_voice_id, a.call_mode, a.response_latency,
           a.call_greeting, a.agent_name, a.business_info
    FROM account_settings a
    JOIN users u ON a.user_id = u.id
    WHERE u.name IN ('Beryl', 'Paul')
    ORDER BY u.name
''')

accounts = cursor.fetchall()

for acc in accounts:
    print(f"{'='*60}")
    print(f"USER: {acc[1]} (ID: {acc[0]})")
    print(f"{'='*60}")
    print(f"Phone Number: {acc[2]}")
    print(f"Voice: {acc[3]}")
    print(f"Voice Provider: {acc[4]}")
    print(f"Speechmatics Voice: {acc[5]}")
    print(f"Call Mode: {acc[6]}")
    print(f"Response Latency: {acc[7]}ms")
    print(f"Call Greeting: {acc[8]}")
    print(f"Agent Name: {acc[9]}")
    print(f"Business Info: {acc[10][:50] if acc[10] else '(empty)'}...")
    print()

# Check recent calls
print("\n=== RECENT CALLS ===\n")
cursor.execute('''
    SELECT c.call_uuid, u.name, c.called_number, c.start_time, c.duration, c.status
    FROM calls c
    JOIN users u ON c.user_id = u.id
    WHERE u.name IN ('Beryl', 'Paul')
    ORDER BY c.start_time DESC
    LIMIT 10
''')

for call in cursor.fetchall():
    print(f"{call[1]:8} | {call[2]} | {call[3][:19]} | {call[4]}s | {call[5]}")

conn.close()
