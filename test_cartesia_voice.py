import asyncio
from cartesia import Cartesia
import base64

async def test_cartesia():
    client = Cartesia(api_key='sk_car_5S1GHCuxH1zeN2UEY3Mz9u')
    ws = client.tts.websocket()
    
    print("Testing Cartesia WebSocket...")
    
    # ws.send() returns a regular generator, not async generator
    for chunk in ws.send(
        model_id='sonic-english',
        transcript='Hello! This is a test of the Cartesia voice.',
        voice={
            'mode': 'id',
            'id': 'a0e99841-438c-4a64-b679-ae501e7d6091'
        },
        output_format={
            'container': 'raw',
            'encoding': 'pcm_s16le',
            'sample_rate': 16000
        },
        stream=True
    ):
        print(f"Chunk type: {type(chunk)}")
        if isinstance(chunk, dict):
            print(f"Keys: {list(chunk.keys())}")
            if 'audio' in chunk:
                audio_bytes = base64.b64decode(chunk['audio'])
                print(f"Audio bytes: {len(audio_bytes)}")
        break
    
    await ws.close()
    print("Test complete!")

if __name__ == '__main__':
    asyncio.run(test_cartesia())
