import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Get transfer number for user 21
c.execute('SELECT user_id, transfer_number FROM account_settings WHERE user_id = 21')
row = c.fetchone()

print(f'User ID: {row[0]}')
print(f'Transfer Number in DB: {row[1]}')
print(f'Transfer Number repr: {repr(row[1])}')
print(f'Transfer Number length: {len(row[1]) if row[1] else 0}')

conn.close()
