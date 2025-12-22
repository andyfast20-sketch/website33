import requests
import sqlite3

# Get Vonage credentials from database
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()
cursor.execute('SELECT vonage_api_key, vonage_api_secret FROM global_settings WHERE id = 1')
row = cursor.fetchone()
conn.close()

if not row or not row[0]:
    print("ERROR: Vonage credentials not found in database")
    exit(1)

api_key = row[0]
api_secret = row[1]

print(f"Using API key: {api_key[:20]}...")

# Use the legacy REST API with GET parameters
url = f'https://rest.nexmo.com/call/json'

params = {
    'api_key': api_key,
    'api_secret': api_secret,
    'to': '447958968621',
    'from': '447441474290',
    'answer_url': 'https://nexmo-community.github.io/ncco-examples/first_call_talk.json'
}

print('\nTesting call from 447441474290 (Beryl) to 447958968621 (Nancy transfer number)...')
print('This will test if the transfer number can receive calls.\n')
print(f'Request URL: {url}')
print(f'Request params: {params}\n')

response = requests.post(url, params)
print(f'Status: {response.status_code}')
print(f'Response text: {response.text}')

try:
    result = response.json()
    print(f'Response JSON: {result}')
    
    if response.status_code == 200 and result.get('status') == '0':
        print('\n✅ SUCCESS! The transfer number CAN receive calls.')
        print('This means the Vonage transfer API should work.')
    else:
        print(f'\n❌ Call failed: {result.get("error-text", "Unknown error")}')
except:
    print(f'\n❌ API request failed - non-JSON response')
