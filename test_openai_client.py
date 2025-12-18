import openai
import os

# Test OpenAI client initialization
try:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = openai.OpenAI(api_key=api_key)
    print("✓ Client created successfully")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Say 'test successful' and nothing else"}
        ],
        max_tokens=10
    )
    
    print(f"✓ API call successful: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
