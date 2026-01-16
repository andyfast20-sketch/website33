"""
Add Vapi support to the voice system
"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("Adding Vapi columns to database...")

# Step 1: Add vapi_api_key to global_settings
try:
    cursor.execute('ALTER TABLE global_settings ADD COLUMN vapi_api_key TEXT')
    print("✓ Added vapi_api_key to global_settings")
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e).lower():
        print("✓ vapi_api_key already exists in global_settings")
    else:
        print(f"✗ Error adding vapi_api_key: {e}")

# Step 2: Add vapi_voice_id to account_settings
try:
    cursor.execute('ALTER TABLE account_settings ADD COLUMN vapi_voice_id TEXT')
    print("✓ Added vapi_voice_id to account_settings")
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e).lower():
        print("✓ vapi_voice_id already exists in account_settings")
    else:
        print(f"✗ Error adding vapi_voice_id: {e}")

conn.commit()
conn.close()

print("\n✓ Database migration complete!")
print("\nYou can now:")
print("  1. Set VAPI_API_KEY in global settings")
print("  2. Select 'vapi' as voice_provider for any account")
print("  3. Choose a Vapi voice ID for that account")
