import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# List all tables
print("=== TABLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for table in cursor.fetchall():
    print(f"  {table[0]}")

# Check if accounts table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
if cursor.fetchone():
    print("\n=== ACCOUNTS ===")
    cursor.execute("SELECT id, account_name, phone_number, api_key FROM accounts")
    accounts = cursor.fetchall()
    for acc in accounts:
        print(f"ID: {acc[0]}, Name: {acc[1]}, Phone: {acc[2]}, Has API Key: {bool(acc[3])}")

# Check calls table structure
print("\n=== CALLS TABLE STRUCTURE ===")
cursor.execute("PRAGMA table_info(calls)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

conn.close()
