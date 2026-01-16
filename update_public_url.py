#!/usr/bin/env python3
"""Check and update public URL in database"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check current URL
cursor.execute('SELECT public_url FROM global_settings WHERE id = 1')
row = cursor.fetchone()
current_url = row[0] if row else None
print(f'Current Database URL: {current_url}')

# Update to permanent URL
new_url = 'https://callansweringandy.uk'
cursor.execute('UPDATE global_settings SET public_url = ? WHERE id = 1', (new_url,))
conn.commit()

# Verify
cursor.execute('SELECT public_url FROM global_settings WHERE id = 1')
row = cursor.fetchone()
print(f'Updated Database URL: {row[0]}')

conn.close()
print('\n✅ Database updated to permanent URL')
