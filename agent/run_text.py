"""Simple text-based agent for testing without microphone."""
import os
import asyncio
import pyttsx3

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 175)

DEEPSEEK_API_KEY = (os.getenv("DEEPSEEK_API_KEY") or "").strip()


async def get_response(user_text: str) -> str:
    """Get response from DeepSeek."""
    import aiohttp
    import json

    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in the environment")
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful voice assistant. Keep responses short and conversational."},
            {"role": "user", "content": user_text},
        ],
        "stream": True,
    }
    
    full_response = ""
    
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers) as resp:
            async for line in resp.content:
                line_text = line.decode("utf-8").strip()
                if not line_text.startswith("data: "):
                    continue
                json_str = line_text[6:]
                if json_str == "[DONE]":
                    break
                try:
                    data = json.loads(json_str)
                    content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_response += content
                except json.JSONDecodeError:
                    continue
    
    print()  # newline
    return full_response


def speak(text: str):
    """Speak text using pyttsx3."""
    engine.say(text)
    engine.runAndWait()


async def main():
    print("=" * 50)
    print("AI Voice Agent (Text Mode)")
    print("Type your message and press Enter.")
    print("Type 'quit' to exit.")
    print("=" * 50)
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ('quit', 'exit', 'q'):
                print("Goodbye!")
                break
            
            print("AI: ", end="")
            response = await get_response(user_input)
            
            # Speak the response
            speak(response)
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
