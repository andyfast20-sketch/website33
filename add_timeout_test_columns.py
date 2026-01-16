"""
Add timeout test columns to global_settings table for testing purposes.
This allows super admin to enable a timeout test mode where if the AI agent 
takes more than X seconds to respond, a "deleted response" audio is played.
"""
import sqlite3

def add_timeout_test_columns():
    """Add timeout_test_enabled and timeout_test_seconds columns to global_settings table"""
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(global_settings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add timeout_test_enabled column (default 0 = disabled)
        if 'timeout_test_enabled' not in columns:
            cursor.execute("""
                ALTER TABLE global_settings 
                ADD COLUMN timeout_test_enabled INTEGER DEFAULT 0
            """)
            print("✅ Added timeout_test_enabled column")
        else:
            print("ℹ️ timeout_test_enabled column already exists")
        
        # Add timeout_test_seconds column (default 2.0 seconds)
        if 'timeout_test_seconds' not in columns:
            cursor.execute("""
                ALTER TABLE global_settings 
                ADD COLUMN timeout_test_seconds REAL DEFAULT 2.0
            """)
            print("✅ Added timeout_test_seconds column")
        else:
            print("ℹ️ timeout_test_seconds column already exists")
        
        conn.commit()
        print("✅ Database migration complete")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_timeout_test_columns()
