import sqlite3

conn = sqlite3.connect('agent/phone_agent.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Available tables:")
for table in tables:
    print(f"  - {table[0]}")

# Try to find call-related table
for table in tables:
    table_name = table[0]
    if 'call' in table_name.lower():
        print(f"\n\nChecking {table_name} table:")
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 1")
        columns = [description[0] for description in cursor.description]
        result = cursor.fetchone()
        
        if result:
            print("\nLast call record:")
            for i, col in enumerate(columns):
                value = result[i]
                if col == 'transcript' and value:
                    print(f"{col}: {value[:500]}...")
                else:
                    print(f"{col}: {value}")

conn.close()
