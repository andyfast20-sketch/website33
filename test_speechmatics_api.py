"""Test Speechmatics TTS API"""
import httpx
import sqlite3

# Get API key from database
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()
cursor.execute('SELECT speechmatics_api_key FROM global_settings WHERE id = 1')
result = cursor.fetchone()
conn.close()

if not result or not result[0]:
    print("❌ No Speechmatics API key found in database")
    exit(1)

api_key = result[0]
print(f"✅ Found API key: {api_key[:10]}...{api_key[-4:]}")

# Test API call
print("\n🔊 Testing Speechmatics API...")

# Speechmatics v1 API
url = "https://flow.api.speechmatics.com/v1/synthesize"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "text": "Hello, this is a test.",
    "voice_id": "sarah",
    "sample_rate": 16000,
    "format": "wav"
}

print(f"URL: {url}")

try:
    response = httpx.post(url, headers=headers, json=data, timeout=30.0)
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        audio_size = len(response.content)
        print(f"✅ SUCCESS! Audio size: {audio_size} bytes")
        
        # Save to file
        with open("speechmatics_test.wav", "wb") as f:
            f.write(response.content)
        print("✅ Saved to speechmatics_test.wav")
    else:
        print(f"❌ Error ({response.status_code}): {response.text[:500]}")
        print("\nLet me try checking if this is a websocket-only API...")
        
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()

# If HTTP doesn't work, it might be websocket-only or not available yet
print("\n💡 Note: Speechmatics TTS might be a preview feature or require different authentication.")
print("   The API key format suggests it's valid, but the endpoint might not be correct.")
