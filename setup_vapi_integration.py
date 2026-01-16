"""
Setup script to integrate Vonage with Vapi properly.

The correct Vapi integration requires:
1. Create a Vapi Assistant (using their API)
2. Import your Vonage number into Vapi OR configure SIP forwarding
3. Configure Vonage webhooks to point to Vapi

This is NOT compatible with the current server-side audio streaming architecture.
"""

import httpx
import asyncio
from vonage_agent import _decrypt_secret
import sqlite3

async def create_vapi_assistant(api_key: str, config: dict):
    """Create a Vapi assistant with your configuration"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.vapi.ai/assistant",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "name": config.get("agent_name", "Assistant"),
                "firstMessage": config.get("call_greeting", "Hello!"),
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": config.get("system_prompt", "You are a helpful assistant.")
                        }
                    ],
                    "temperature": 0.7,
                    "maxTokens": 250
                },
                "voice": {
                    "provider": "playht",
                    "voiceId": "jennifer"
                },
                "endCallPhrases": ["goodbye", "thank you bye"],
                "silenceTimeoutSeconds": 30,
                "responseDelaySeconds": 0.4,
                "interruptionsEnabled": True
            }
        )
        
        if response.status_code == 201:
            assistant_data = response.json()
            print(f"✅ Created Vapi Assistant: {assistant_data['id']}")
            return assistant_data
        else:
            print(f"❌ Failed to create assistant: {response.status_code} - {response.text}")
            return None

async def main():
    print("\n" + "="*60)
    print("VAPI + VONAGE INTEGRATION SETUP")
    print("="*60 + "\n")
    
    # Load Vapi API key from database
    conn = sqlite3.connect("agent_config.db")
    cursor = conn.cursor()
    cursor.execute("SELECT vapi_api_key FROM global_settings WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result[0]:
        print("❌ No Vapi API key found in database")
        print("   Please add your Vapi API key in Super Admin first.")
        return
    
    vapi_key = _decrypt_secret(result[0])
    
    print("📋 IMPORTANT: Vapi Integration requires ONE of these approaches:\n")
    print("OPTION 1: Import Vonage Number to Vapi")
    print("  - Go to https://dashboard.vapi.ai/phone-numbers")
    print("  - Click 'Import Number'")
    print("  - Follow Vapi's instructions to transfer from Vonage")
    print("  - ⚠️  This will move your number away from your current system\n")
    
    print("OPTION 2: Use Vapi's Phone API (Outbound Only)")
    print("  - Vapi makes outbound calls TO your customers")
    print("  - You call Vapi's API when you want to make a call")
    print("  - Cannot receive inbound calls to your Vonage number\n")
    
    print("OPTION 3: Server-Side Streaming (NOT SUPPORTED BY VAPI)")
    print("  - Vapi doesn't support server-side audio streaming")
    print("  - The current architecture won't work with Vapi")
    print("  - Consider Retell AI or Bland AI instead\n")
    
    print("="*60)
    print("RECOMMENDATION:")
    print("="*60)
    print("Keep your current Speechmatics + OpenRouter setup.")
    print("It's already optimized and working well.")
    print("\nOR")
    print("\nSwitch to Retell AI which supports server-side streaming.")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
