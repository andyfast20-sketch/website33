import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=== CHECKING 0203 NUMBER ASSIGNMENT ===\n")

# Check all accounts with the 0203 number
cursor.execute('''
    SELECT a.user_id, u.name, a.phone_number, u.status
    FROM account_settings a
    JOIN users u ON a.user_id = u.id
    WHERE a.phone_number LIKE '%2039856179%' OR a.phone_number = '442039856179'
''')

accounts_with_0203 = cursor.fetchall()
print(f"Accounts with 0203 number: {len(accounts_with_0203)}")
for acc in accounts_with_0203:
    print(f"  User {acc[0]} ({acc[1]}): {acc[2]} - Status: {acc[3]}")

print("\n=== CHECKING LYNTON & PAUL PHONE NUMBERS ===\n")
cursor.execute('''
    SELECT u.id, u.name, a.phone_number, u.status
    FROM users u
    LEFT JOIN account_settings a ON u.id = a.user_id
    WHERE u.name IN ('Lynton', 'Paul')
''')

for user in cursor.fetchall():
    print(f"User {user[0]} ({user[1]}): Phone = {user[2] or 'NONE'}, Status = {user[3]}")

print("\n=== RECENT CALLS TO 0203 NUMBER ===\n")
cursor.execute('''
    SELECT c.call_uuid, c.user_id, u.name, c.called_number, c.start_time, c.duration
    FROM calls c
    JOIN users u ON c.user_id = u.id
    WHERE c.called_number LIKE '%2039856179%'
    ORDER BY c.start_time DESC
    LIMIT 15
''')

for call in cursor.fetchall():
    print(f"{call[5]:3}s | User {call[1]:2} ({call[2]:8}) | {call[4][:19]} | UUID: {call[0][:12]}")

conn.close()
