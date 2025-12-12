import sqlite3

try:
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    # Add voice column if doesn't exist
    cursor.execute('ALTER TABLE account_settings ADD COLUMN voice TEXT DEFAULT "shimmer"')
    conn.commit()
    print('✅ Voice column added successfully')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('✅ Voice column already exists')
    else:
        print(f'❌ Error: {e}')
finally:
    conn.close()
