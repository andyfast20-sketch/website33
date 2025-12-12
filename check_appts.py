import sqlite3

conn = sqlite3.connect('call_logs.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT id, date, time, customer_name, call_uuid, user_id FROM appointments ORDER BY id DESC LIMIT 5')
print('\nRecent appointments:')
print('-' * 80)
for row in cursor.fetchall():
    print(f"ID: {row['id']}, Date: {row['date']}, Time: {row['time']}, Name: {row['customer_name']}, UUID: {row['call_uuid']}, UserID: {row['user_id']}")

cursor.execute('PRAGMA table_info(calls)')
print('\nCalls table columns:')
print('-' * 80)
for row in cursor.fetchall():
    print(f"{row[1]} ({row[2]})")

cursor.execute('SELECT * FROM calls ORDER BY id DESC LIMIT 3')
print('\nRecent calls:')
print('-' * 80)
for row in cursor.fetchall():
    print(dict(row))

conn.close()
