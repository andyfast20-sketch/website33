#!/usr/bin/env python3
"""Check tunnel configuration"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()
cursor.execute('SELECT cloudflare_domain, cloudflare_tunnel_token FROM global_settings WHERE id = 1')
row = cursor.fetchone()

print(f'Domain: {row[0] if row else "Not found"}')
print(f'Token exists: {"Yes" if (row and row[1]) else "No"}')
print(f'Token length: {len(row[1]) if (row and row[1]) else 0}')
if row and row[1]:
    print(f'Token preview: {row[1][:20]}...')

conn.close()
