"""
Add call_mode column to calls table to track which mode was used for each call
"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

try:
    # Check if call_mode column exists
    cursor.execute("PRAGMA table_info(calls)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'call_mode' not in columns:
        # Add call_mode column
        cursor.execute('''
            ALTER TABLE calls 
            ADD COLUMN call_mode TEXT DEFAULT 'realtime'
        ''')
        conn.commit()
        print("✅ Added call_mode column to calls table")
    else:
        print("ℹ️ call_mode column already exists in calls table")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\nDone!")
