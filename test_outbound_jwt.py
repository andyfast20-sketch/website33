import requests
import json
import sqlite3
import os
import jwt
import time

# Load credentials from database
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
cursor.execute('SELECT vonage_application_id, vonage_private_key_pem FROM global_settings WHERE id = 1')
result = cursor.fetchone()

# Also get Nancy's phone number for FROM field
cursor.execute('SELECT phone_number FROM account_settings WHERE user_id = 6')
nancy_row = cursor.fetchone()
conn.close()

if not result or not result[0] or not result[1]:
    print("❌ No Vonage Application credentials found in database")
    print("Please configure Application ID and Private Key in Super Admin")
    exit(1)

app_id = _decrypt_secret(result[0])
private_key_pem = _decrypt_secret(result[1])
from_number = nancy_row[0] if nancy_row else None

if not app_id or not private_key_pem:
    print("❌ Failed to decrypt Vonage credentials")
    exit(1)

print(f"✓ Application ID: {app_id}")
print(f"✓ Private Key: loaded ({len(private_key_pem)} bytes)")
if from_number:
    print(f"✓ FROM number (Nancy): {from_number}")
print()

# Generate JWT
print("Generating JWT token...")
now = int(time.time())
payload = {
    "application_id": app_id,
    "iat": now,
    "exp": now + 900,  # 15 minutes
    "jti": f"jwt-{now}"
}

try:
    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    print(f"✓ JWT generated: {token[:50]}...")
except Exception as e:
    print(f"❌ Failed to generate JWT: {e}")
    exit(1)

print()

# Test outbound call
print("=" * 60)
print("TEST: Creating outbound call via Vonage REST API (JWT Auth)")
print("=" * 60)

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

# Create call using JWT auth
url = "https://api.nexmo.com/v1/calls"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# Simple NCCO - just reads a message
ncco = [
    {
        "action": "talk",
        "text": "This is a test outbound call from your Vonage account using JWT authentication. If you can hear this message, outbound calling is working correctly."
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
    headers=headers
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
elif response.status_code == 401:
    print("❌ ERROR 401: Unauthorized")
    print("JWT authentication failed - check Application ID and Private Key")
else:
    print(f"❌ ERROR {response.status_code}")
    try:
        error_data = response.json()
        print(json.dumps(error_data, indent=2))
    except:
        pass
