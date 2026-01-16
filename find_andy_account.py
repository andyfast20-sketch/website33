import sqlite3

# Try call_logs.db
print("=== Checking call_logs.db ===")
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("\nTables:")
for t in tables:
    print(f"  - {t[0]}")

# Check accounts table
try:
    cursor.execute("SELECT id, account_name, phone_number FROM accounts WHERE account_name LIKE '%andy%' OR account_name LIKE '%roberts%'")
    accounts = cursor.fetchall()
    print("\nAndy Roberts account:")
    for acc in accounts:
        print(f"  ID: {acc[0]}, Name: {acc[1]}, Phone: {acc[2]}")
        
    # Find number ending in 271
    cursor.execute("SELECT id, account_name, phone_number FROM accounts WHERE phone_number LIKE '%271'")
    number_accounts = cursor.fetchall()
    print("\nAccounts with numbers ending in 271:")
    for acc in number_accounts:
        print(f"  ID: {acc[0]}, Name: {acc[1]}, Phone: {acc[2]}")
        
    # Get all accounts
    cursor.execute("SELECT id, account_name, phone_number FROM accounts")
    all_accounts = cursor.fetchall()
    print("\nAll accounts:")
    for acc in all_accounts:
        print(f"  ID: {acc[0]}, Name: {acc[1]}, Phone: {acc[2]}")
        
except Exception as e:
    print(f"Error: {e}")

conn.close()
