import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check users table structure
print("=== USERS TABLE STRUCTURE ===")
cursor.execute("PRAGMA table_info(users)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

print("\n=== ALL USERS ===")
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

for user in users:
    print(f"\nUser {user[0]}:")
    for i, col in enumerate(columns):
        if user[i]:
            print(f"  {col}: {user[i]}")

conn.close()
