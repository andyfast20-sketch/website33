#!/usr/bin/env python3
"""Add account status and suspension features to users table"""

import sqlite3

def add_account_status_columns():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add status column (active, suspended, banned)
        if 'status' not in columns:
            print("Adding status column...")
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN status TEXT DEFAULT 'active'
            ''')
            conn.commit()
            print("✅ Status column added")
        else:
            print("✅ Status column already exists")
        
        # Add suspension_message column
        if 'suspension_message' not in columns:
            print("Adding suspension_message column...")
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN suspension_message TEXT
            ''')
            conn.commit()
            print("✅ Suspension message column added")
        else:
            print("✅ Suspension message column already exists")
        
        # Add suspended_at column
        if 'suspended_at' not in columns:
            print("Adding suspended_at column...")
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN suspended_at DATETIME
            ''')
            conn.commit()
            print("✅ Suspended_at column added")
        else:
            print("✅ Suspended_at column already exists")
        
        # Add suspended_by column
        if 'suspended_by' not in columns:
            print("Adding suspended_by column...")
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN suspended_by TEXT
            ''')
            conn.commit()
            print("✅ Suspended_by column added")
        else:
            print("✅ Suspended_by column already exists")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_account_status_columns()
