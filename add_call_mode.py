"""
Add call_mode column to users table
"""
import sqlite3

def add_call_mode_column():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    try:
        # Add call_mode column (default: 'realtime')
        cursor.execute('''
            ALTER TABLE users ADD COLUMN call_mode TEXT DEFAULT 'realtime'
        ''')
        conn.commit()
        print("✅ Added call_mode column to users table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ call_mode column already exists")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_call_mode_column()
