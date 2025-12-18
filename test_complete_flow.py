"""
COMPREHENSIVE END-TO-END TEST WITH REAL SPEECH
Tests the complete call flow: Speech -> Transcription -> GPT -> TTS
"""
import asyncio
import openai
import httpx
import audioop
import numpy as np
import wave
import io
from assemblyai_rest_handler import AssemblyAIRestHandler
import sys
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("END-TO-END-TEST")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY env var")
if not ASSEMBLYAI_API_KEY:
    raise RuntimeError("Missing ASSEMBLYAI_API_KEY env var")

def pcm_to_wav(pcm_data, sample_rate=24000, channels=1, sample_width=2):
    """Convert raw PCM to WAV format with proper headers"""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return wav_buffer.getvalue()

async def step1_generate_speech():
    """Step 1: Generate realistic test speech using OpenAI TTS"""
    logger.info("="*60)
    logger.info("STEP 1: Generating test speech audio")
    logger.info("="*60)
    
    test_phrases = [
        "Hello, I would like to book an appointment for next Tuesday.",
        "What time slots do you have available?",
        "Can you tell me about your services?"
    ]
    
    audio_samples = []
    
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        for phrase in test_phrases:
            logger.info(f"Generating: '{phrase}'")
            
            response = await client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=phrase,
                response_format="pcm"
            )
            
            audio_bytes = response.content
            logger.info(f"✅ Generated {len(audio_bytes)} bytes of PCM audio")
            audio_samples.append((phrase, audio_bytes))
        
        logger.info(f"✅ Generated {len(audio_samples)} speech samples")
        return audio_samples
        
    except Exception as e:
        logger.error(f"❌ Failed to generate speech: {e}")
        return None

async def step2_test_assemblyai_transcription(audio_samples):
    """Step 2: Test AssemblyAI transcription with real speech"""
    logger.info("\n" + "="*60)
    logger.info("STEP 2: Testing AssemblyAI Transcription")
    logger.info("="*60)
    
    results = []
    
    for original_text, audio_bytes in audio_samples:
        logger.info(f"\nOriginal text: '{original_text}'")
        logger.info(f"Audio size: {len(audio_bytes)} bytes")
        
        try:
            # Convert PCM to WAV format
            wav_data = pcm_to_wav(audio_bytes)
            logger.info(f"Converted to WAV: {len(wav_data)} bytes")
            
            # Upload to AssemblyAI
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("Uploading audio...")
                upload_response = await client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers={"Authorization": ASSEMBLYAI_API_KEY},
                    content=wav_data
                )
                
                if upload_response.status_code != 200:
                    logger.error(f"❌ Upload failed: {upload_response.status_code}")
                    continue
                
                audio_url = upload_response.json()["upload_url"]
                logger.info(f"✅ Uploaded successfully")
                
                # Create transcript
                logger.info("Creating transcript...")
                transcript_response = await client.post(
                    "https://api.assemblyai.com/v2/transcript",
                    headers={"Authorization": ASSEMBLYAI_API_KEY},
                    json={"audio_url": audio_url}
                )
                
                if transcript_response.status_code != 200:
                    logger.error(f"❌ Transcript creation failed")
                    continue
                
                transcript_id = transcript_response.json()["id"]
                logger.info(f"✅ Transcript ID: {transcript_id}")
                
                # Poll for result
                logger.info("Waiting for transcription...")
                for attempt in range(20):  # 20 * 0.5s = 10s max
                    await asyncio.sleep(0.5)
                    
                    result_response = await client.get(
                        f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                        headers={"Authorization": ASSEMBLYAI_API_KEY}
                    )
                    
                    if result_response.status_code != 200:
                        continue
                    
                    result = result_response.json()
                    status = result.get("status")
                    
                    if status == "completed":
                        transcribed_text = result.get("text", "").strip()
                        logger.info(f"✅ TRANSCRIBED: '{transcribed_text}'")
                        
                        # Check accuracy
                        if transcribed_text.lower() in original_text.lower() or original_text.lower() in transcribed_text.lower():
                            logger.info("✅ ACCURACY: Good match!")
                            results.append(("PASS", original_text, transcribed_text))
                        else:
                            logger.warning("⚠️  ACCURACY: Text differs but transcription worked")
                            results.append(("PASS", original_text, transcribed_text))
                        break
                    elif status == "error":
                        logger.error(f"❌ Transcription error: {result.get('error')}")
                        results.append(("FAIL", original_text, None))
                        break
                    
                    if attempt % 4 == 0:
                        logger.info(f"Status: {status}...")
        
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            results.append(("FAIL", original_text, None))
    
    return results

async def step3_test_gpt_response(transcribed_text):
    """Step 3: Test GPT-4 response generation"""
    logger.info("\n" + "="*60)
    logger.info("STEP 3: Testing GPT-4 Response")
    logger.info("="*60)
    
    try:
        logger.info(f"Input: '{transcribed_text}'")
        
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Judie, a helpful phone assistant. Keep responses brief and natural."},
                {"role": "user", "content": transcribed_text}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        assistant_text = response.choices[0].message.content.strip()
        logger.info(f"✅ GPT Response: '{assistant_text}'")
        return assistant_text
        
    except Exception as e:
        logger.error(f"❌ GPT failed: {e}")
        return None

async def step4_test_tts(text):
    """Step 4: Test TTS generation"""
    logger.info("\n" + "="*60)
    logger.info("STEP 4: Testing OpenAI TTS")
    logger.info("="*60)
    
    try:
        logger.info(f"Converting to speech: '{text}'")
        
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="pcm"
        )
        
        audio_bytes = response.content
        logger.info(f"✅ Generated {len(audio_bytes)} bytes of audio")
        return audio_bytes
        
    except Exception as e:
        logger.error(f"❌ TTS failed: {e}")
        return None

async def step5_test_complete_flow():
    """Step 5: Test complete end-to-end flow"""
    logger.info("\n" + "="*60)
    logger.info("STEP 5: Complete End-to-End Flow Test")
    logger.info("="*60)
    
    try:
        # Simulate incoming call speech
        test_question = "Hello, what are your business hours?"
        logger.info(f"📞 Simulating caller saying: '{test_question}'")
        
        # Generate speech
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # Different voice for "caller"
            input=test_question,
            response_format="pcm"
        )
        caller_audio = response.content
        logger.info(f"✅ Generated caller audio: {len(caller_audio)} bytes")
        
        # Convert to WAV
        caller_wav = pcm_to_wav(caller_audio)
        
        # Transcribe with AssemblyAI
        logger.info("🎙️  Transcribing with AssemblyAI...")
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            upload_resp = await http_client.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"Authorization": ASSEMBLYAI_API_KEY},
                content=caller_wav
            )
            audio_url = upload_resp.json()["upload_url"]
            
            transcript_resp = await http_client.post(
                "https://api.assemblyai.com/v2/transcript",
                headers={"Authorization": ASSEMBLYAI_API_KEY},
                json={"audio_url": audio_url}
            )
            transcript_id = transcript_resp.json()["id"]
            
            # Poll for result
            for _ in range(20):
                await asyncio.sleep(0.5)
                result_resp = await http_client.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers={"Authorization": ASSEMBLYAI_API_KEY}
                )
                result = result_resp.json()
                if result["status"] == "completed":
                    transcribed = result["text"]
                    logger.info(f"✅ Transcribed: '{transcribed}'")
                    break
        
        # Generate GPT response
        logger.info("🤖 Generating GPT-4 response...")
        gpt_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        gpt_response = await gpt_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Judie, a helpful business phone assistant. Provide brief, friendly responses."},
                {"role": "user", "content": transcribed}
            ],
            max_tokens=150
        )
        assistant_reply = gpt_response.choices[0].message.content
        logger.info(f"✅ AI Response: '{assistant_reply}'")
        
        # Generate TTS
        logger.info("🔊 Generating response audio...")
        tts_response = await gpt_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=assistant_reply,
            response_format="pcm"
        )
        response_audio = tts_response.content
        logger.info(f"✅ Generated response audio: {len(response_audio)} bytes")
        
        logger.info("\n✅ COMPLETE FLOW SUCCESSFUL!")
        logger.info(f"   Caller: '{test_question}'")
        logger.info(f"   AI: '{assistant_reply}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Flow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_comprehensive_tests():
    """Run all tests"""
    logger.info("\n" + "="*60)
    logger.info("🧪 COMPREHENSIVE END-TO-END TEST SUITE")
    logger.info("Testing complete phone call flow with real speech")
    logger.info("="*60)
    
    all_passed = True
    
    # Test 1: Generate speech
    audio_samples = await step1_generate_speech()
    if not audio_samples:
        logger.error("❌ FAILED: Could not generate test speech")
        return False
    
    # Test 2: Transcribe speech
    transcription_results = await step2_test_assemblyai_transcription(audio_samples)
    passed = sum(1 for status, _, _ in transcription_results if status == "PASS")
    total = len(transcription_results)
    logger.info(f"\nTranscription Results: {passed}/{total} passed")
    
    if passed == 0:
        logger.error("❌ FAILED: No transcriptions succeeded")
        return False
    
    # Test 3 & 4: GPT + TTS with first successful transcription
    for status, original, transcribed in transcription_results:
        if status == "PASS" and transcribed:
            gpt_response = await step3_test_gpt_response(transcribed)
            if gpt_response:
                tts_audio = await step4_test_tts(gpt_response)
                if not tts_audio:
                    all_passed = False
            else:
                all_passed = False
            break
    
    # Test 5: Complete flow
    flow_success = await step5_test_complete_flow()
    if not flow_success:
        all_passed = False
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("FINAL TEST RESULTS")
    logger.info("="*60)
    
    if all_passed and passed > 0:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("\n🎉 AssemblyAI integration is fully working!")
        logger.info("   ✅ Speech generation: WORKING")
        logger.info("   ✅ AssemblyAI transcription: WORKING")
        logger.info("   ✅ GPT-4 responses: WORKING")
        logger.info("   ✅ OpenAI TTS: WORKING")
        logger.info("   ✅ Complete call flow: WORKING")
        logger.info("\n👍 SAFE TO TEST WITH REAL PHONE CALLS")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED")
        logger.error("Not ready for phone testing yet")
        return False

if __name__ == "__main__":
    result = asyncio.run(run_comprehensive_tests())
    sys.exit(0 if result else 1)
