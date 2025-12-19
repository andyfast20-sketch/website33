import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=== PHONE NUMBERS BY USER ===")
cursor.execute('''
    SELECT u.id, u.name, a.phone_number 
    FROM users u
    LEFT JOIN account_settings a ON u.id = a.user_id
    ORDER BY u.id
''')

for row in cursor.fetchall():
    user_id, name, phone = row
    print(f"User {user_id:2} ({name:10}): {phone if phone else 'NO PHONE SET'}")

print("\n=== RECENT CALLS ===")
cursor.execute('''
    SELECT called_number, user_id, COUNT(*) as count
    FROM calls
    WHERE start_time > datetime('now', '-1 hour')
    GROUP BY called_number, user_id
    ORDER BY MAX(start_time) DESC
''')

for row in cursor.fetchall():
    print(f"Phone {row[0]} -> User {row[1]} ({row[2]} calls)")

conn.close()
