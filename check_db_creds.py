import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()
cursor.execute('SELECT vonage_api_key, vonage_api_secret FROM global_settings WHERE id = 1')
result = cursor.fetchone()
conn.close()

if result:
    key_encrypted = result[0] or ''
    secret_encrypted = result[1] or ''
    
    print(f"API Key (first 50 chars): {key_encrypted[:50]}")
    print(f"API Secret (first 50 chars): {secret_encrypted[:50]}")
    print(f"\nAPI Key starts with 'enc:v1:': {key_encrypted.startswith('enc:v1:')}")
    print(f"API Secret starts with 'enc:v1:': {secret_encrypted.startswith('enc:v1:')}")
    print(f"\nAPI Key length: {len(key_encrypted)}")
    print(f"API Secret length: {len(secret_encrypted)}")
else:
    print("No credentials found in database")
