"""
Test calling the transfer number directly using Vonage Voice API v1
This will make an outbound call FROM one of our numbers TO the transfer number
to verify it can receive calls
"""

import sqlite3
import requests
import json
import time
import base64
import hmac
import hashlib

def get_db_connection():
    return sqlite3.connect('call_logs.db')

# Get Vonage credentials and phone numbers
conn = get_db_connection()
cursor = conn.cursor()

# Get API credentials
cursor.execute('SELECT vonage_api_key, vonage_api_secret FROM global_settings WHERE id = 1')
creds = cursor.fetchone()
vonage_api_key = creds[0]
vonage_api_secret = creds[1]

# Get Nancy's transfer number (destination)
cursor.execute('SELECT transfer_number FROM account_settings WHERE user_id = 6')
transfer_to = cursor.fetchone()[0]

# Get Beryl's phone number (source - will appear as caller ID)
cursor.execute('SELECT phone_number FROM account_settings WHERE user_id = 5')
from_number = cursor.fetchone()[0]

conn.close()

print(f"Testing call to transfer number:")
print(f"  From: {from_number} (Beryl's number)")
print(f"  To: {transfer_to} (Nancy's transfer number)")
print(f"  API Key: {vonage_api_key[:10]}...")

# Use Vonage Voice API v1 to make outbound call
# Create a simple NCCO (Vonage Call Control Object) that will say something
ncco = [
    {
        "action": "talk",
        "text": "This is a test call from the Vonage voice agent to verify the transfer number can receive calls.",
        "voiceName": "Kimberly"
    },
    {
        "action": "talk",
        "text": "This call will end in 5 seconds. Thank you.",
        "voiceName": "Kimberly"  
    }
]

# Make the API call
call_data = {
    "to": [{
        "type": "phone",
        "number": transfer_to
    }],
    "from": {
        "type": "phone",
        "number": from_number
    },
    "ncco": ncco
}

url = "https://api.nexmo.com/v1/calls"

# Use Basic Auth with API key and secret
auth = (vonage_api_key, vonage_api_secret)

print(f"\nMaking call to Vonage API...")
print(f"URL: {url}")
print(f"Data: {json.dumps(call_data, indent=2)}")

response = requests.post(
    url,
    auth=auth,
    headers={"Content-Type": "application/json"},
    json=call_data
)

print(f"\nStatus: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 201:
    result = response.json()
    print(f"\n✅ SUCCESS! Call created with UUID: {result.get('uuid')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Direction: {result.get('direction')}")
    print(f"\nThe transfer number {transfer_to} should now be ringing!")
else:
    print(f"\n❌ FAILED to create call")
    print(f"   Error: {response.text}")
