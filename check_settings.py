import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check account_settings structure
print("=== ACCOUNT_SETTINGS TABLE STRUCTURE ===")
cursor.execute("PRAGMA table_info(account_settings)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

print("\n=== ALL ACCOUNT SETTINGS ===")
cursor.execute("SELECT * FROM account_settings")
settings = cursor.fetchall()
cursor.execute("PRAGMA table_info(account_settings)")
columns = [col[1] for col in cursor.fetchall()]

for setting in settings:
    print(f"\n--- User ID: {setting[0]} ---")
    for i, col in enumerate(columns):
        if setting[i] and col not in ['id', 'user_id']:
            print(f"  {col}: {setting[i]}")

conn.close()
