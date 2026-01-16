"""
Verify timeout test columns exist in the database
"""
import sqlite3

def verify_timeout_test_setup():
    """Verify the timeout test columns are in the database"""
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(global_settings)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        print("Checking timeout test columns...")
        
        if 'timeout_test_enabled' in columns:
            print(f"✅ timeout_test_enabled exists (type: {columns['timeout_test_enabled']})")
        else:
            print("❌ timeout_test_enabled column NOT found")
        
        if 'timeout_test_seconds' in columns:
            print(f"✅ timeout_test_seconds exists (type: {columns['timeout_test_seconds']})")
        else:
            print("❌ timeout_test_seconds column NOT found")
        
        # Try to read current values
        cursor.execute('SELECT timeout_test_enabled, timeout_test_seconds FROM global_settings WHERE id = 1')
        row = cursor.fetchone()
        
        if row:
            enabled, seconds = row
            print(f"\nCurrent settings:")
            print(f"  Enabled: {bool(enabled) if enabled is not None else 'NULL'}")
            print(f"  Timeout: {seconds if seconds is not None else 'NULL'} seconds")
        else:
            print("\n⚠️ No settings row found (id=1)")
        
        print("\n✅ Database schema is ready!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    verify_timeout_test_setup()
