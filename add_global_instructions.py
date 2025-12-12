"""
Add global_settings table for admin-controlled global AI instructions
"""
import sqlite3

def add_global_settings_table():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    print("Creating global_settings table...")
    
    try:
        # Create global_settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                global_instructions TEXT DEFAULT '',
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT DEFAULT 'admin'
            )
        ''')
        print("✅ Global settings table created")
        
        # Initialize with default empty instructions
        cursor.execute('INSERT OR IGNORE INTO global_settings (id, global_instructions) VALUES (1, "")')
        print("✅ Global settings initialized")
        
        conn.commit()
        print("\n✅ Global instructions feature ready!")
        print("   Access it through: http://localhost:5004/super-admin.html")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    add_global_settings_table()
