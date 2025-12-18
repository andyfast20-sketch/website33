import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check if call_mode exists in account_settings
cursor.execute('PRAGMA table_info(account_settings)')
columns = [col[1] for col in cursor.fetchall()]
print(f"call_mode in account_settings: {'call_mode' in columns}")

# Get call_mode for user 1
cursor.execute('SELECT user_id, call_mode FROM account_settings LIMIT 5')
results = cursor.fetchall()
print("\nCall modes in account_settings:")
for row in results:
    print(f"  User {row[0]}: {row[1]}")

conn.close()
