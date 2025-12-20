import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT a.user_id, u.name, a.phone_number, a.call_greeting, u.status
    FROM account_settings a 
    JOIN users u ON a.user_id = u.id 
    ORDER BY a.user_id
''')

print("\n=== CURRENT PHONE NUMBERS ===")
for row in cursor.fetchall():
    user_id, name, phone, greeting, status = row
    greeting_short = greeting[:50] if greeting else "(none)"
    print(f"User {user_id} ({name}) [{status}]: {phone}")
    print(f"  Greeting: {greeting_short}")
    print()

conn.close()
