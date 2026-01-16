import sqlite3

conn = sqlite3.connect('vonage_agent.db')
c = conn.cursor()

# List all tables
print("=== DATABASE TABLES ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
for table in tables:
    print(f"  {table}")

# Check users table structure
print("\n=== USERS TABLE STRUCTURE ===")
c.execute("PRAGMA table_info(users)")
for col in c.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Check user 27
print("\n=== USER 27 ===")
c.execute("SELECT * FROM users WHERE id=27")
user = c.fetchone()
if user:
    c.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in c.fetchall()]
    for i, col in enumerate(cols):
        print(f"  {col}: {user[i]}")
else:
    print("  User 27 not found!")

# Check account_settings for user 27
print("\n=== ACCOUNT SETTINGS FOR USER 27 ===")
try:
    c.execute("SELECT * FROM account_settings WHERE user_id=27")
    settings = c.fetchone()
    if settings:
        c.execute("PRAGMA table_info(account_settings)")
        cols = [col[1] for col in c.fetchall()]
        for i, col in enumerate(cols):
            if 'phone' in col.lower() or 'number' in col.lower():
                print(f"  {col}: {settings[i]}")
except:
    print("  account_settings table not found or error")

conn.close()
