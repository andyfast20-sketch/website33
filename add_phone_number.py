"""
Add phone_number column to account_settings table
"""
import sqlite3

def add_phone_number_column():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    print("Adding phone_number column to account_settings...")
    
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN phone_number TEXT')
        conn.commit()
        print("✅ Phone number column added successfully!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  Phone number column already exists")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_phone_number_column()
