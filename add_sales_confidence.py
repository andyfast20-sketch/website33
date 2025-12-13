import sqlite3

# Add sales_confidence column to calls table
conn = sqlite3.connect('agent/phone_agent.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE calls ADD COLUMN sales_confidence INTEGER DEFAULT NULL')
    print("✓ Added sales_confidence column to calls table")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("✓ sales_confidence column already exists")
    else:
        print(f"Error: {e}")

conn.commit()
conn.close()
print("\nDatabase updated successfully!")
