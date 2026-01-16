import sqlite3

conn = sqlite3.connect('voice_agent.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for t in tables:
    print(f"  - {t[0]}")

# Check for accounts table and numbers
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%account%'")
account_tables = cursor.fetchall()
print("\nAccount-related tables:")
for t in account_tables:
    print(f"  - {t[0]}")

# Check accounts table structure
try:
    cursor.execute("PRAGMA table_info(accounts)")
    columns = cursor.fetchall()
    print("\nAccounts table columns:")
    for c in columns:
        print(f"  - {c[1]} ({c[2]})")
except:
    print("\nNo 'accounts' table found")

# Search for Andy Roberts
try:
    cursor.execute("SELECT id, username, email FROM accounts WHERE username LIKE '%andy%' OR username LIKE '%roberts%' OR email LIKE '%andy%' OR email LIKE '%roberts%'")
    users = cursor.fetchall()
    print("\nAndy Roberts account:")
    for u in users:
        print(f"  ID: {u[0]}, Username: {u[1]}, Email: {u[2]}")
except Exception as e:
    print(f"\nError searching accounts: {e}")

# Search for number ending in 271 in accounts table
try:
    cursor.execute("SELECT id, username, phone_number FROM accounts WHERE phone_number LIKE '%271'")
    numbers = cursor.fetchall()
    print("\nAccounts with numbers ending in 271:")
    for n in numbers:
        print(f"  ID: {n[0]}, Username: {n[1]}, Phone: {n[2]}")
except Exception as e:
    print(f"\nError searching phone numbers: {e}")

conn.close()
