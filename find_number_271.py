import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=== Searching for phone number ending in 271 ===\n")

# Check account_settings for number ending in 271
cursor.execute("SELECT user_id, phone_number FROM account_settings WHERE phone_number LIKE '%271'")
settings = cursor.fetchall()

if settings:
    for s in settings:
        user_id = s[0]
        phone = s[1]
        print(f"Found: {phone} assigned to user_id: {user_id}")
        
        # Get user details
        cursor.execute("SELECT id, username, email, full_name, business_name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            print(f"  User: {user[1]} (ID: {user[0]})")
            print(f"  Full Name: {user[3]}")
            print(f"  Business: {user[4]}")
            print(f"  Email: {user[2]}")
else:
    print("No phone number ending in 271 found in account_settings")
    
# Show all phone numbers
print("\n=== All assigned phone numbers ===")
cursor.execute("SELECT user_id, phone_number FROM account_settings WHERE phone_number IS NOT NULL AND phone_number != ''")
all_numbers = cursor.fetchall()
for n in all_numbers:
    cursor.execute("SELECT username, business_name FROM users WHERE id = ?", (n[0],))
    user = cursor.fetchone()
    if user:
        print(f"  {n[1]} -> {user[0]} ({user[1]})")

conn.close()
