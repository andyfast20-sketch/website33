import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check account_settings table schema
print("=== Account Settings Table Schema ===")
cursor.execute("PRAGMA table_info(account_settings)")
for col in cursor.fetchall():
    print(f"{col[1]} ({col[2]})")

# Check if phone is in account_settings
print("\n=== Looking for Jim (491) ===")
cursor.execute("SELECT * FROM account_settings")
all_settings = cursor.fetchall()
for setting in all_settings:
    if '491' in str(setting):
        print(f"Found: {setting}")

# Check all users
print("\n=== All Users ===")
cursor.execute("SELECT id, name FROM users")
for user in cursor.fetchall():
    print(f"User ID {user[0]}: {user[1]}")
    # Get their settings
    cursor.execute("SELECT key, value FROM account_settings WHERE user_id = ?", (user[0],))
    settings = cursor.fetchall()
    for s in settings:
        if 'phone' in s[0].lower() or 'greeting' in s[0].lower():
            print(f"  {s[0]}: {s[1]}")

conn.close()
