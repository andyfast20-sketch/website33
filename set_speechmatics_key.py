import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Add the Speechmatics API key
api_key = "xTqQN5wXm0mkD2airyTSsFPLR3RpHhqW"
cursor.execute('''
    UPDATE global_settings 
    SET speechmatics_api_key = ?, 
        last_updated = CURRENT_TIMESTAMP,
        updated_by = 'admin'
    WHERE id = 1
''', (api_key,))

conn.commit()

# Verify it was saved
cursor.execute('SELECT speechmatics_api_key FROM global_settings WHERE id = 1')
result = cursor.fetchone()

if result and result[0]:
    print(f"✅ Speechmatics API key saved successfully!")
    print(f"   Key: {result[0][:10]}...{result[0][-4:]}")
else:
    print("❌ Failed to save key")

conn.close()
