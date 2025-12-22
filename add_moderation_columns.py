"""
Add content moderation columns to existing database
Run this once to update the database schema
"""

import sqlite3

def update_database():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    columns_to_add = [
        ('is_suspended', 'INTEGER DEFAULT 0'),
        ('suspension_reason', 'TEXT DEFAULT NULL'),
        ('suspended_at', 'TEXT DEFAULT NULL'),
        ('suspension_count', 'INTEGER DEFAULT 0'),
        ('last_flag_details', 'TEXT DEFAULT NULL')
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE account_settings ADD COLUMN {column_name} {column_type}')
            print(f'✅ Added column: {column_name}')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f'ℹ️  Column already exists: {column_name}')
            else:
                print(f'❌ Error adding {column_name}: {e}')
    
    conn.commit()
    conn.close()
    print('\n✅ Database updated successfully!')

if __name__ == '__main__':
    update_database()
