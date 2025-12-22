import requests
import json
import sqlite3
import os

# Load credentials from database (same method as vonage_agent.py)
try:
    import keyring
except:
    keyring = None

try:
    from cryptography.fernet import Fernet, InvalidToken
except:
    Fernet = None
    InvalidToken = Exception

_SECRET_PREFIX = "enc:v1:"
_KEYRING_SERVICE = "website33"
_KEYRING_MASTER_KEY_NAME = "MASTER_FERNET_KEY"

def _get_master_key():
    env_key = (os.getenv("WEBSITE33_MASTER_KEY") or "").strip()
    if env_key:
        return env_key.encode("utf-8")
    if keyring:
        try:
            stored = keyring.get_password(_KEYRING_SERVICE, _KEYRING_MASTER_KEY_NAME)
            if stored:
                return stored.encode("utf-8")
        except:
            pass
    return None

def _decrypt_secret(value):
    raw = (value or "").strip()
    if not raw:
        return ""
    if not raw.startswith(_SECRET_PREFIX):
        return raw
    if Fernet is None:
        return ""
    master_key = _get_master_key()
    if not master_key:
        return ""
    try:
        f = Fernet(master_key)
        token = raw[len(_SECRET_PREFIX):]
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except:
        return ""

# Load from database
print("Loading Vonage credentials from database...")
conn = sqlite3.connect("call_logs.db")
cursor = conn.cursor()
cursor.execute('SELECT vonage_api_key, vonage_api_secret FROM global_settings WHERE id = 1')
result = cursor.fetchone()

# Also get Nancy's phone number for FROM field
cursor.execute('SELECT phone_number FROM account_settings WHERE user_id = 6')
nancy_row = cursor.fetchone()
conn.close()

if not result or not result[0] or not result[1]:
    print("❌ No Vonage API credentials found in database")
    print("Please configure them in Super Admin first")
    exit(1)

api_key = _decrypt_secret(result[0])
api_secret = _decrypt_secret(result[1])
from_number = nancy_row[0] if nancy_row else None

if not api_key or not api_secret:
    print("❌ Failed to decrypt Vonage credentials")
    exit(1)

print(f"✓ API Key: {api_key[:10]}...")
print(f"✓ API Secret: {'*' * 10}")
if from_number:
    print(f"✓ FROM number (Nancy): {from_number}")
print()

# Test outbound call
print("=" * 60)
print("TEST: Creating outbound call via Vonage REST API")
print("=" * 60)

# Use Nancy's number as FROM and user's test number as TO
if not from_number:
    print("❌ No FROM number found for Nancy's account")
    exit(1)

TO_NUMBER = "07595289669"  # User's test number

# Normalize numbers to E.164
if from_number.startswith('0'):
    from_number = '44' + from_number[1:]
if TO_NUMBER.startswith('0'):
    TO_NUMBER = '44' + TO_NUMBER[1:]

print(f"\nAttempting outbound call:")
print(f"  FROM: {from_number} (Nancy's Vonage number)")
print(f"  TO: {TO_NUMBER} (test destination)")
print()

# Create call using basic auth
url = "https://api.nexmo.com/v1/calls"
headers = {
    "Content-Type": "application/json"
}

# Simple NCCO - just reads a message
ncco = [
    {
        "action": "talk",
        "text": "This is a test outbound call from your Vonage account. If you can hear this message, outbound calling is working correctly."
    }
]

payload = {
    "to": [{"type": "phone", "number": TO_NUMBER}],
    "from": {"type": "phone", "number": from_number},
    "ncco": ncco
}

print("Payload:")
print(json.dumps(payload, indent=2))
print()

response = requests.post(
    url,
    json=payload,
    auth=(api_key, api_secret)
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
print()

if response.status_code == 201:
    print("✅ SUCCESS! Outbound call created successfully")
    print(f"Your phone ({TO_NUMBER}) should be ringing now")
    data = response.json()
    print(f"Call UUID: {data.get('uuid')}")
elif response.status_code == 403:
    print("❌ ERROR 403: Permission denied")
    print("This means:")
    print("  - The FROM number may not be authorized for outbound calls")
    print("  - Account lacks permission for outbound calling")
    print("  - Country/destination restrictions apply")
    print("  - Insufficient balance (though you have €4.50)")
else:
    print(f"❌ ERROR {response.status_code}")
    try:
        error_data = response.json()
        print(json.dumps(error_data, indent=2))
    except:
        pass
