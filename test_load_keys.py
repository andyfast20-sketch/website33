import sqlite3
import sys
import os

# Add vonage_agent to path to import its functions
sys.path.insert(0, os.path.dirname(__file__))

# Import the decrypt function
from vonage_agent import _decrypt_secret, get_db_connection, _get_fernet, _get_or_create_master_fernet_key

print("Testing credential loading...")
print("="*60)

# Test Fernet key availability
master_key = _get_or_create_master_fernet_key()
print(f"Master Fernet Key: {'Present (' + str(len(master_key)) + ' bytes)' if master_key else 'MISSING!'}")
f = _get_fernet()
print(f"Fernet instance: {'Available' if f else 'FAILED TO CREATE!'}")
print("="*60)

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT vonage_api_key, vonage_api_secret, vonage_application_id, vonage_private_key_pem FROM global_settings WHERE id = 1')
    result = cursor.fetchone()
    
    if result:
        vonage_key_raw, vonage_secret_raw, vonage_app_id_raw, vonage_private_key_pem_raw = result
        
        print(f"Raw API Key: {vonage_key_raw[:50] if vonage_key_raw else 'None'}...")
        print(f"Raw API Secret: {vonage_secret_raw[:50] if vonage_secret_raw else 'None'}...")
        print(f"Raw App ID: {vonage_app_id_raw[:50] if vonage_app_id_raw else 'None'}...")
        print(f"Raw Private Key: {vonage_private_key_pem_raw[:50] if vonage_private_key_pem_raw else 'None'}...")
        print("="*60)
        
        # Try to decrypt
        vonage_key = _decrypt_secret(vonage_key_raw)
        vonage_secret = _decrypt_secret(vonage_secret_raw)
        vonage_app_id = _decrypt_secret(vonage_app_id_raw)
        vonage_private_key_pem = _decrypt_secret(vonage_private_key_pem_raw)
        
        print(f"Decrypted API Key: {'Present (' + str(len(vonage_key)) + ' chars)' if vonage_key else 'FAILED'}")
        print(f"Decrypted API Secret: {'Present (' + str(len(vonage_secret)) + ' chars)' if vonage_secret else 'FAILED'}")
        print(f"Decrypted App ID: {vonage_app_id if vonage_app_id else 'FAILED'}")
        print(f"Decrypted Private Key: {'Present (' + str(len(vonage_private_key_pem)) + ' chars)' if vonage_private_key_pem else 'FAILED'}")
        
        if vonage_private_key_pem:
            print(f"Private Key starts with: {vonage_private_key_pem[:50]}")
    else:
        print("No global settings found!")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
