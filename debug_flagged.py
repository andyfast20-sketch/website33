import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=== CHECKING SUSPENSION STATUS ===")
cursor.execute('SELECT user_id, is_suspended, suspension_reason FROM account_settings')
rows = cursor.fetchall()
for row in rows:
    print(f"User {row[0]}: is_suspended={row[1]} (type: {type(row[1])}), reason={row[2]}")

print("\n=== TESTING QUERY WITH = 1 ===")
cursor.execute('''
    SELECT u.id, u.name, a.is_suspended
    FROM users u
    JOIN account_settings a ON u.id = a.user_id
    WHERE a.is_suspended = 1
''')
rows = cursor.fetchall()
print(f"Found {len(rows)} rows with is_suspended = 1:")
for row in rows:
    print(f"  - User {row[0]}: {row[1]} (is_suspended={row[2]})")

print("\n=== TESTING QUERY WITH != 0 ===")
cursor.execute('''
    SELECT u.id, u.name, a.is_suspended
    FROM users u
    JOIN account_settings a ON u.id = a.user_id
    WHERE a.is_suspended != 0
''')
rows = cursor.fetchall()
print(f"Found {len(rows)} rows with is_suspended != 0:")
for row in rows:
    print(f"  - User {row[0]}: {row[1]} (is_suspended={row[2]})")

conn.close()
