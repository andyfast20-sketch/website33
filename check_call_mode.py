import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check current call_mode setting
cursor.execute('SELECT user_id, call_mode FROM account_settings WHERE user_id = 4')
result = cursor.fetchone()
print(f'User 4 call_mode setting: {result[1] if result else "Not found"}')

# Check last call
cursor.execute('SELECT call_uuid, start_time, duration, status FROM calls WHERE user_id = 4 ORDER BY start_time DESC LIMIT 1')
call = cursor.fetchone()
if call:
    print(f'\nLast call:')
    print(f'  UUID: {call[0]}')
    print(f'  Time: {call[1]}')
    print(f'  Duration: {call[2]}s')
    print(f'  Status: {call[3]}')
else:
    print('\nNo calls found')

conn.close()
