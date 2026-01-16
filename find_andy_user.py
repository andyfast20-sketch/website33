import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=== Finding Andy Roberts ===\n")

# Check users table
cursor.execute("SELECT id, username, email, phone_number FROM users WHERE username LIKE '%andy%' OR username LIKE '%roberts%' OR email LIKE '%andy%' OR email LIKE '%roberts%'")
users = cursor.fetchall()
print("Users matching 'andy' or 'roberts':")
for u in users:
    print(f"  ID: {u[0]}, Username: {u[1]}, Email: {u[2]}, Phone: {u[3]}")

# Find user with number ending in 271
print("\n\nUsers with phone numbers ending in 271:")
cursor.execute("SELECT id, username, email, phone_number FROM users WHERE phone_number LIKE '%271'")
number_users = cursor.fetchall()
for u in number_users:
    print(f"  ID: {u[0]}, Username: {u[1]}, Email: {u[2]}, Phone: {u[3]}")

# Show all users to find the right one
print("\n\nAll users:")
cursor.execute("SELECT id, username, email, phone_number FROM users")
all_users = cursor.fetchall()
for u in all_users:
    phone = u[3] if u[3] else "(no phone)"
    print(f"  ID: {u[0]}, Username: {u[1]}, Email: {u[2]}, Phone: {phone}")

conn.close()
