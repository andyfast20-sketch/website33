import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE account_settings ADD COLUMN use_elevenlabs INTEGER DEFAULT 0')
    conn.commit()
    print('✅ use_elevenlabs column added successfully')
except Exception as e:
    if 'duplicate column name' in str(e).lower():
        print('✅ use_elevenlabs column already exists')
    else:
        print(f'❌ Error: {e}')

conn.close()
