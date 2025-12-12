"""Add google_voice column to account_settings table"""
import sqlite3

def main():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN google_voice TEXT DEFAULT "en-GB-Neural2-A"')
        conn.commit()
        print("✅ Successfully added google_voice column to account_settings")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  google_voice column already exists")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
