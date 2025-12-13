import sqlite3

# Add sales_detection_confidence column to calls table
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(calls)")
columns = [col[1] for col in cursor.fetchall()]

if 'sales_detection_confidence' not in columns:
    cursor.execute('ALTER TABLE calls ADD COLUMN sales_detection_confidence INTEGER DEFAULT NULL')
    print("✓ Added sales_detection_confidence column")
else:
    print("Column already exists")

conn.commit()
conn.close()
print("Database updated successfully")
