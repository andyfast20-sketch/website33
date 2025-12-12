#!/usr/bin/env python3
"""Add elevenlabs_voice_id column to account_settings table"""

import sqlite3

def add_elevenlabs_voice_column():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(account_settings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'elevenlabs_voice_id' not in columns:
            print("Adding elevenlabs_voice_id column...")
            cursor.execute('''
                ALTER TABLE account_settings 
                ADD COLUMN elevenlabs_voice_id TEXT DEFAULT 'EXAVITQu4vr4xnSDxMaL'
            ''')
            conn.commit()
            print("✅ Column added successfully!")
        else:
            print("✅ Column already exists")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_elevenlabs_voice_column()
