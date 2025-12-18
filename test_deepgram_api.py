"""Test Deepgram API key and verify it works"""
import os
import requests
import json

# Your Deepgram API key
API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing DEEPGRAM_API_KEY env var")

# Test with a simple pre-recorded audio transcription
# Using Deepgram's sample audio URL
url = "https://api.deepgram.com/v1/listen"

headers = {
    "Authorization": f"Token {API_KEY}",
    "Content-Type": "application/json"
}

# Use a sample audio URL (Deepgram's test audio)
payload = {
    "url": "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
}

print("Testing Deepgram API...")
print(f"Endpoint: {url}")
print()

try:
    response = requests.post(url, headers=headers, json=payload, params={"model": "nova-2"})
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
        
        print("✅ SUCCESS! Deepgram API is working!")
        print()
        print(f"Transcription: {transcript}")
        print()
        
        # Check metadata
        metadata = result.get('metadata', {})
        print(f"Duration: {metadata.get('duration', 'N/A')} seconds")
        print(f"Model: {metadata.get('model_info', {}).get('name', 'N/A')}")
        print(f"Request ID: {metadata.get('request_id', 'N/A')}")
        print()
        print("💰 This request used some of your $200 credit!")
        
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Exception occurred: {e}")
    import traceback
    traceback.print_exc()
