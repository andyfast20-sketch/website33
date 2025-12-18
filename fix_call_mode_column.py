"""
Fix call_mode column - Add to account_settings table
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

try:
    # Check if call_mode column exists in account_settings
    cursor.execute("PRAGMA table_info(account_settings)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'call_mode' not in columns:
        # Add call_mode column to account_settings
        cursor.execute('''
            ALTER TABLE account_settings 
            ADD COLUMN call_mode TEXT DEFAULT 'realtime'
        ''')
        conn.commit()
        print("✅ Added call_mode column to account_settings table")
    else:
        print("ℹ️ call_mode column already exists in account_settings")
    
    # Also remove from users table if it was added there by mistake
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    
    if 'call_mode' in user_columns:
        print("⚠️ Found call_mode in users table (should only be in account_settings)")
        # Note: SQLite doesn't support DROP COLUMN easily, so we'll leave it
        # The important thing is that it's now in the right table
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\nDone!")
