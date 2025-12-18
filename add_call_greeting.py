import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Add call_greeting column to account_settings
try:
    cursor.execute('ALTER TABLE account_settings ADD COLUMN call_greeting TEXT')
    print("✓ Added call_greeting column")
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e).lower():
        print("Column already exists")
    else:
        raise

conn.commit()
conn.close()
print("Database updated successfully!")
