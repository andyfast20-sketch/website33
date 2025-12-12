import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check users
cursor.execute('SELECT name, id FROM users')
users = cursor.fetchall()
print('Users:')
for u in users:
    print(f'  {u[0]} (ID: {u[1]})')

# Check calls by user_id
cursor.execute('SELECT COUNT(*), user_id FROM calls GROUP BY user_id')
counts = cursor.fetchall()
print('\nCalls by user_id:')
for c in counts:
    print(f'  user_id {c[1]}: {c[0]} calls')

# Check recent calls for user_id 3 (James)
cursor.execute('''
    SELECT call_uuid, caller_number, start_time, user_id 
    FROM calls 
    WHERE user_id = 3 
    ORDER BY start_time DESC 
    LIMIT 5
''')
james_calls = cursor.fetchall()
print('\nRecent calls for James (user_id=3):')
for call in james_calls:
    print(f'  UUID: {call[0][:16]}... From: {call[1]} Time: {call[2]} UserID: {call[3]}')

conn.close()
