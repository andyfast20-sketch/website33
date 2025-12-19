import re

with open('vonage_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the audio sending to use mu-law
old_code = '''            if getattr(self, "_vonage_audio_mode", "bytes") == "json":
                b64 = base64.b64encode(pcm_bytes).decode()'''

new_code = '''            if getattr(self, "_vonage_audio_mode", "bytes") == "json":
                # Convert 16kHz PCM to 8kHz mu-law for Vonage
                try:
                    import audioop
                    pcm_8khz = audioop.ratecv(pcm_bytes, 2, 1, 16000, 8000, None)[0]
                    mulaw_bytes = audioop.lin2ulaw(pcm_8khz, 2)
                    audio_to_send = mulaw_bytes
                except Exception:
                    audio_to_send = pcm_bytes
                b64 = base64.b64encode(audio_to_send).decode()'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Found and replaced audio conversion code")
else:
    print("❌ Pattern not found")
    
# Also replace pcm_bytes with audio_to_send in binary mode
old_binary = '''            else:
                await self.vonage_ws.send_bytes(pcm_bytes)'''
new_binary = '''            else:
                try:
                    import audioop
                    pcm_8khz = audioop.ratecv(pcm_bytes, 2, 1, 16000, 8000, None)[0]
                    mulaw_bytes = audioop.lin2ulaw(pcm_8khz, 2)
                    audio_to_send = mulaw_bytes
                except Exception:
                    audio_to_send = pcm_bytes
                await self.vonage_ws.send_bytes(audio_to_send)'''

if old_binary in content:
    content = content.replace(old_binary, new_binary)
    print("✅ Replaced binary mode code")

with open('vonage_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)
    
print("✅ File updated")
