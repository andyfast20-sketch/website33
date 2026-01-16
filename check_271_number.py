import sqlite3

conn = sqlite3.connect('vonage_agent.db')
c = conn.cursor()

# Check all phone numbers
print("=== ALL PHONE NUMBERS ===")
c.execute('SELECT id, user_id, number FROM phone_numbers')
for row in c.fetchall():
    print(f"  ID {row[0]}: User {row[1]} - Number: {row[2]}")

# Check user 27
print("\n=== USER 27 DETAILS ===")
c.execute('SELECT id, username, active FROM users WHERE id=27')
user = c.fetchone()
if user:
    print(f"  User ID: {user[0]}")
    print(f"  Username: {user[1]}")
    print(f"  Active: {user[2]}")

# Check if there's any number ending in 271 anywhere
print("\n=== SEARCH FOR 271 ===")
c.execute("SELECT id, user_id, number FROM phone_numbers WHERE number LIKE '%271'")
results = c.fetchall()
if results:
    for row in results:
        print(f"  Found: ID {row[0]}: User {row[1]} - Number: {row[2]}")
else:
    print("  No numbers ending in 271 found")

# Check recent phone number changes/deletions
print("\n=== CHECKING FOR RECENT HISTORY ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print(f"  Available tables: {', '.join(tables)}")

conn.close()
