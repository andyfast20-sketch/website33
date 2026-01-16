import sqlite3

conn = sqlite3.connect('voice_agent.db')
cursor = conn.cursor()

print("\n=== Phone numbers ending in 271 ===")
cursor.execute("SELECT phone_number, user_id, country, created_at FROM phone_numbers WHERE phone_number LIKE '%271'")
rows = cursor.fetchall()
for r in rows:
    print(f"Number: {r[0]}, User ID: {r[1]}, Country: {r[2]}, Created: {r[3]}")

print("\n=== Andy Roberts account info ===")
cursor.execute("SELECT id, username, email, created_at FROM users WHERE username LIKE '%andy%' OR username LIKE '%roberts%'")
users = cursor.fetchall()
for u in users:
    print(f"User ID: {u[0]}, Username: {u[1]}, Email: {u[2]}, Created: {u[3]}")
    
    # Check phone numbers for this user
    cursor.execute("SELECT phone_number, country, created_at FROM phone_numbers WHERE user_id = ?", (u[0],))
    numbers = cursor.fetchall()
    print(f"  Phone numbers assigned to this user:")
    if numbers:
        for n in numbers:
            print(f"    - {n[0]} ({n[1]}) - Created: {n[2]}")
    else:
        print(f"    - None")

print("\n=== All unassigned phone numbers ===")
cursor.execute("SELECT phone_number, country, created_at FROM phone_numbers WHERE user_id IS NULL")
unassigned = cursor.fetchall()
for n in unassigned:
    print(f"Number: {n[0]}, Country: {n[1]}, Created: {n[2]}")

conn.close()
