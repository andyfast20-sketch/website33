import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=" * 60)
print("NANCY'S ACCOUNT CONFIGURATION")
print("=" * 60)

cursor.execute('SELECT * FROM account_settings WHERE user_id = 6')
columns = [desc[0] for desc in cursor.description]
row = cursor.fetchone()

if row:
    for col, val in zip(columns, row):
        if val and len(str(val)) > 100:
            print(f'{col}: {str(val)[:100]}...')
        else:
            print(f'{col}: {val}')
else:
    print("No account found for Nancy (user_id 6)")

print("\n" + "=" * 60)
print("RECENT CALLS TO NANCY'S NUMBER (447441474271)")
print("=" * 60)

cursor.execute('''SELECT * FROM call_logs LIMIT 1''')
sample_row = cursor.fetchone()
if sample_row:
    log_columns = [desc[0] for desc in cursor.description]
    print(f"Call logs columns: {', '.join(log_columns)}\n")

cursor.execute('''SELECT * FROM call_logs 
                  ORDER BY timestamp DESC 
                  LIMIT 10''')
rows = cursor.fetchall()

if rows:
    for r in rows:
        print(f'\nCall: {r}')
else:
    print("No recent calls found")

print("\n" + "=" * 60)
print("CHECKING VONAGE NUMBER LINK")
print("=" * 60)

# Check if the phone number is properly configured in global settings
cursor.execute('SELECT * FROM global_settings WHERE id = 1')
global_row = cursor.fetchone()
if global_row:
    global_cols = [desc[0] for desc in cursor.description]
    vonage_idx = global_cols.index('VONAGE_NUMBER') if 'VONAGE_NUMBER' in global_cols else None
    if vonage_idx:
        print(f"Vonage Number in global settings: {global_row[vonage_idx]}")

conn.close()

print("\n" + "=" * 60)
print("DIAGNOSIS")
print("=" * 60)
print("If getting engaged tone:")
print("1. Check if Vonage number is linked to the Vonage Application")
print("2. Verify the answer URL webhook is configured: https://YOUR_NGROK_URL/webhooks/answer")
print("3. Check if server is running and ngrok tunnel is active")
print("4. Verify Vonage Application ID and Private Key are correct")
