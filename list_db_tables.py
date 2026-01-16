#!/usr/bin/env python3
"""List all database tables"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check for settings table
for table_name in ['settings', 'admin_settings', 'global_settings']:
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        print(f"\n{table_name} exists and has columns:", [desc[0] for desc in cursor.description])
    except:
        pass

conn.close()
