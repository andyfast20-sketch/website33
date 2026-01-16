import sqlite3
import os

db_path = 'vonage_agent.db'
print(f"Database: {db_path}")
print(f"Size: {os.path.getsize(db_path)} bytes")
print(f"Modified: {os.path.getmtime(db_path)}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# List all tables
print("\n=== TABLES ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = c.fetchall()
print(f"Found {len(tables)} tables")
for table in tables:
    print(f"  - {table[0]}")

conn.close()
