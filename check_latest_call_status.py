#!/usr/bin/env python3
"""Quick script to check the status of the latest call"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT call_uuid, caller_number, called_number, start_time, end_time, 
           summary, transcript, recording_url, created_at, call_mode
    FROM calls 
    ORDER BY created_at DESC 
    LIMIT 1
''')

row = cursor.fetchone()

if row:
    print(f"Call UUID: {row[0]}")
    print(f"Caller: {row[1]}")
    print(f"Called: {row[2]}")
    print(f"Start: {row[3]}")
    print(f"End: {row[4]}")
    print(f"Summary: {row[5][:200] if row[5] else 'None'}...")
    print(f"Transcript: {row[6][:200] if row[6] else 'None'}...")
    print(f"Recording URL: {row[7] or 'None'}")
    print(f"Created At: {row[8]}")
    print(f"Call Mode: {row[9]}")
else:
    print("No calls found in database")

conn.close()
