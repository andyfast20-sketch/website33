import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check global instructions
print("=== Global Instructions ===")
cursor.execute("SELECT id, global_instructions FROM global_settings")
result = cursor.fetchone()
if result:
    print(f"ID: {result[0]}")
    print(f"Global Instructions: {result[1]}")
else:
    print("No global instructions found")

conn.close()
