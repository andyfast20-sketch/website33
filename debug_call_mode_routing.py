"""Debug: Check what call_mode is being loaded for the session"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check user 4's call_mode setting in account_settings
cursor.execute('''
    SELECT call_mode FROM account_settings WHERE user_id = 4
''')
result = cursor.fetchone()
print(f"User 4 account_settings.call_mode: {result[0] if result else 'NOT SET'}")

# Check the most recent 3 calls
cursor.execute('''
    SELECT call_uuid, start_time, call_mode 
    FROM calls 
    WHERE user_id = 4 
    ORDER BY start_time DESC 
    LIMIT 3
''')
print("\nLast 3 calls:")
for row in cursor.fetchall():
    print(f"  {row[0][:16]}... | {row[1]} | mode={row[2]}")

conn.close()
