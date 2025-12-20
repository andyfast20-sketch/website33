import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

cursor.execute('SELECT phone_number FROM account_settings WHERE user_id = 8')
result = cursor.fetchone()

if result:
    phone = result[0]
    print(f"\nJim's phone number: [{phone}]")
    print(f"Length: {len(phone)}")
    print(f"Repr: {repr(phone)}")
    print(f"Bytes: {phone.encode('utf-8')}")
else:
    print("No phone found for user 8")

conn.close()
