import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Check user 27 specifically
print("=== USER 27 DETAILS ===")
c.execute('''
    SELECT u.id, u.name, u.username, u.status, a.phone_number
    FROM users u
    LEFT JOIN account_settings a ON u.id = a.user_id
    WHERE u.id = 27
''')
user = c.fetchone()
if user:
    print(f"  User ID: {user[0]}")
    print(f"  Name: {user[1]}")
    print(f"  Username: {user[2]}")
    print(f"  Status: {user[3]}")
    print(f"  Phone Number: {user[4]}")
else:
    print("  User 27 not found!")

# Check all users with phone numbers ending in 271
print("\n=== SEARCH FOR NUMBERS ENDING IN 271 ===")
c.execute('''
    SELECT u.id, u.name, a.phone_number
    FROM users u
    JOIN account_settings a ON u.id = a.user_id
    WHERE a.phone_number LIKE '%271'
''')
results = c.fetchall()
if results:
    for row in results:
        print(f"  User {row[0]} ({row[1]}): {row[2]}")
else:
    print("  No numbers ending in 271 found")

# Check all phone numbers for user 27
print("\n=== ALL ACCOUNT SETTINGS FOR USER 27 ===")
c.execute('''
    SELECT phone_number, call_greeting
    FROM account_settings
    WHERE user_id = 27
''')
settings = c.fetchone()
if settings:
    print(f"  Phone: {settings[0]}")
    print(f"  Greeting: {settings[1]}")
else:
    print("  No account settings found for user 27")

conn.close()
