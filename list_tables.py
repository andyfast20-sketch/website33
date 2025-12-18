import sqlite3

conn = sqlite3.connect('agents.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in agents.db:")
for table in tables:
    print(f"  - {table}")
conn.close()
