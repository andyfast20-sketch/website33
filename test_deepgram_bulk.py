"""Make multiple Deepgram API calls to use more credit"""
import os
import requests
import time

API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing DEEPGRAM_API_KEY env var")

headers = {
    "Authorization": f"Token {API_KEY}",
    "Content-Type": "application/json"
}

# Different sample audio URLs to test
test_urls = [
    "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav",
    "https://static.deepgram.com/examples/interview_speech-analytics.wav",
    "https://static.deepgram.com/examples/nasa-spacewalk-interview.wav"
]

print("Making 10 Deepgram API calls to use credit...")
print()

total_duration = 0
successful_calls = 0

for i in range(10):
    try:
        # Cycle through different audio samples
        audio_url = test_urls[i % len(test_urls)]
        
        payload = {"url": audio_url}
        
        response = requests.post(
            "https://api.deepgram.com/v1/listen",
            headers=headers,
            json=payload,
            params={"model": "nova-2", "smart_format": "true"}
        )
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            duration = metadata.get('duration', 0)
            total_duration += duration
            successful_calls += 1
            
            print(f"✅ Call {i+1}/10: {duration:.2f}s processed | Request ID: {metadata.get('request_id', 'N/A')[:20]}...")
        else:
            print(f"❌ Call {i+1}/10: Error {response.status_code}")
            
        time.sleep(0.5)  # Small delay between calls
        
    except Exception as e:
        print(f"❌ Call {i+1}/10: Exception - {e}")

print()
print(f"{'='*60}")
print(f"Completed {successful_calls}/10 calls")
print(f"Total audio processed: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
print(f"Estimated cost: ${(total_duration/60) * 0.0043:.6f}")
print()
print("💰 Check your Deepgram dashboard - balance should update soon!")
print("   (Balance updates may take 15-60 minutes to reflect)")
