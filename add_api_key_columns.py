"""
Add API key columns to global_settings table
"""
import sqlite3

def add_api_key_columns():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    print("Adding API key columns to global_settings table...")
    
    try:
        # Add speechmatics_api_key column
        cursor.execute('''
            ALTER TABLE global_settings 
            ADD COLUMN speechmatics_api_key TEXT DEFAULT NULL
        ''')
        print("✅ Added speechmatics_api_key column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️ speechmatics_api_key column already exists")
        else:
            raise
    
    try:
        # Add openai_api_key column
        cursor.execute('''
            ALTER TABLE global_settings 
            ADD COLUMN openai_api_key TEXT DEFAULT NULL
        ''')
        print("✅ Added openai_api_key column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️ openai_api_key column already exists")
        else:
            raise
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database migration completed!")
    print("   The super admin page can now save API keys.")

if __name__ == '__main__':
    add_api_key_columns()
