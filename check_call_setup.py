import sqlite3

# Check the account settings
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=== ACCOUNT SETTINGS ===")
cursor.execute('SELECT * FROM account_settings WHERE user_id=4')
row = cursor.fetchone()
print(f"Row length: {len(row)}")
print(f"\nColumn values:")
cursor.execute('PRAGMA table_info(account_settings)')
columns = [col[1] for col in cursor.fetchall()]
for i, (col_name, value) in enumerate(zip(columns, row)):
    print(f"  [{i}] {col_name}: {value}")

print("\n=== LAST 3 CALLS ===")
cursor.execute('SELECT uuid, call_mode, duration, created_at FROM calls WHERE user_id=4 ORDER BY created_at DESC LIMIT 3')
for call in cursor.fetchall():
    print(f"  UUID: {call[0][:16]}... | Mode: {call[1]} | Duration: {call[2]}s | Time: {call[3]}")

conn.close()
