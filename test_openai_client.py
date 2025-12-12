import openai

# Test OpenAI client initialization
try:
    client = openai.OpenAI(api_key="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")
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
