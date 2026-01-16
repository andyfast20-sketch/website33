import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Check current transfer_number
c.execute('SELECT user_id, transfer_number FROM account_settings WHERE user_id = 21')
row = c.fetchone()

print("=" * 60)
print("CURRENT TRANSFER NUMBER FOR USER 21")
print("=" * 60)
print(f'User ID: {row[0]}')
print(f'Transfer Number: {row[1]}')
print(f'Transfer Number (repr): {repr(row[1])}')
print()

# Check recent calls to see what number was dialed
print("=" * 60)
print("RECENT CALLS FROM 447595289669")
print("=" * 60)
c.execute('''
    SELECT id, call_uuid, caller_phone, called_phone, start_time 
    FROM call_logs 
    WHERE caller_phone = '447595289669'
    ORDER BY id DESC LIMIT 5
''')

for row in c.fetchall():
    print(f'Call ID: {row[0]}, UUID: {row[1][:20]}..., From: {row[2]}, To: {row[3]}, Time: {row[4]}')

conn.close()
