#!/usr/bin/env python3
"""Add transfer_instructions column to account_settings table"""
import sqlite3
import os

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'call_logs.db')

def add_transfer_instructions_column():
    """Add transfer_instructions column to account_settings"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(account_settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'transfer_instructions' not in columns:
            # Add the column
            cursor.execute("""
                ALTER TABLE account_settings 
                ADD COLUMN transfer_instructions TEXT DEFAULT ''
            """)
            conn.commit()
            print("✅ Added transfer_instructions column to account_settings")
        else:
            print("ℹ️  transfer_instructions column already exists")
        
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_transfer_instructions_column()
