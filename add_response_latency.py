"""
Add response_latency column to account_settings table
"""
import sqlite3

def add_response_latency_column():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    print("Adding response_latency column to account_settings...")
    
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN response_latency INTEGER DEFAULT 500')
        conn.commit()
        print("✅ Response latency column added successfully!")
        print("   Default value: 500ms (normal response speed)")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  Response latency column already exists")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_response_latency_column()
