import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check users table structure
print("=== Users table structure ===")
cursor.execute("PRAGMA table_info(users)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Check account_settings table structure
print("\n=== Account_settings table structure ===")
cursor.execute("PRAGMA table_info(account_settings)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Find Andy Roberts
print("\n=== Finding Andy Roberts ===")
cursor.execute("SELECT id, username, email FROM users WHERE username LIKE '%andy%' OR username LIKE '%roberts%' OR email LIKE '%andy%' OR email LIKE '%roberts%'")
users = cursor.fetchall()
for u in users:
    print(f"User ID: {u[0]}, Username: {u[1]}, Email: {u[2]}")
    
    # Get their account settings
    cursor.execute("SELECT business_info, agent_name, call_greeting FROM account_settings WHERE user_id = ?", (u[0],))
    settings = cursor.fetchone()
    if settings:
        print(f"  Business: {settings[0]}")
        print(f"  Agent: {settings[1]}")

# Show all users
print("\n=== All users ===")
cursor.execute("SELECT id, username, email FROM users")
all_users = cursor.fetchall()
for u in all_users:
    print(f"  ID: {u[0]}, Username: {u[1]}, Email: {u[2]}")

conn.close()
