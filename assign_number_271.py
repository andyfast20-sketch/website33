import sqlite3

conn = sqlite3.connect('voice_agent.db')
cursor = conn.cursor()

# Find phone number ending in 271
cursor.execute("SELECT phone_number, user_id FROM phone_numbers WHERE phone_number LIKE '%271'")
number_row = cursor.fetchone()

if not number_row:
    print("❌ No phone number ending in 271 found in database")
    conn.close()
    exit(1)

phone_number = number_row[0]
current_user_id = number_row[1]
print(f"Found number: {phone_number}")
print(f"Current user_id: {current_user_id}")

# Find Andy Roberts user ID
cursor.execute("SELECT id, username FROM users WHERE username LIKE '%andy%' OR username LIKE '%roberts%'")
user_row = cursor.fetchone()

if not user_row:
    print("❌ No user found matching 'andy' or 'roberts'")
    conn.close()
    exit(1)

andy_user_id = user_row[0]
andy_username = user_row[1]
print(f"Found user: {andy_username} (ID: {andy_user_id})")

# Assign the number to Andy Roberts
cursor.execute("UPDATE phone_numbers SET user_id = ? WHERE phone_number = ?", (andy_user_id, phone_number))
conn.commit()

print(f"\n✅ Assigned {phone_number} to {andy_username} (user_id: {andy_user_id})")

# Verify
cursor.execute("SELECT phone_number, user_id FROM phone_numbers WHERE phone_number = ?", (phone_number,))
verify = cursor.fetchone()
print(f"Verification: {verify[0]} -> user_id {verify[1]}")

conn.close()
