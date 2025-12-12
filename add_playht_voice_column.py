"""
Add playht_voice_id column to account_settings table
"""
import sqlite3

def add_playht_column():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    try:
        # Add playht_voice_id column
        cursor.execute('''
            ALTER TABLE account_settings 
            ADD COLUMN playht_voice_id TEXT DEFAULT 's3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json'
        ''')
        conn.commit()
        print("✅ Added playht_voice_id column to account_settings")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print("⚠️ Column playht_voice_id already exists")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_playht_column()
