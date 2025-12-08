# Local Telephone AI Agent

A fully local, full-duplex voice agent that feels like a real phone call without telephony. It streams microphone audio to speech-to-text, feeds transcripts to a streaming LLM, and speaks responses through your speakers with barge-in support.

## Features
- Microphone input and speaker output with low-latency streaming
- Whisper (local) or Deepgram streaming STT with partial and final transcripts
- DeepSeek streaming LLM responses with immediate token emission
- Streaming TTS via ElevenLabs or a mock/local generator
- Barge-in: user speech during playback instantly halts LLM + TTS
- Simple LISTENING → THINKING → SPEAKING state machine
- Optional FastAPI dependency for future telephony integration

## Setup
1. **Install system audio dependencies** (PulseAudio/CoreAudio/etc.) and a working microphone + speakers.
2. Create and activate a virtual environment.
3. Install requirements:
   ```bash
   pip install -r agent/requirements.txt
   ```

## Configuration
Environment variables drive external services:
- `DEEPGRAM_API_KEY` – enable Deepgram live transcription (otherwise Whisper or mock input).
- `DEEPSEEK_API_KEY` – DeepSeek chat completion streaming.
- `DEEPSEEK_MODEL` – optional, defaults to `deepseek-chat`.
- `ELEVENLABS_API_KEY` – ElevenLabs streaming TTS key.
- `ELEVENLABS_VOICE` – voice ID or name, defaults to `Bella`.
- `WHISPER_MODEL` – local Whisper model name (e.g., `tiny`, `base`).
- `USE_MOCK_AUDIO` – set to `true` to disable hardware audio (helpful in CI/containers).
- `USE_MOCK_LLM` – set to `true` to use a lightweight mock LLM streamer.
- `USE_MOCK_TTS` – set to `true` to use a simple silent TTS.

## Running the Agent
```bash
python -m agent.app
```
Speak into your microphone. When you talk, the agent will transcribe, think, and respond audibly. If you start speaking while it talks, it should immediately stop and listen again.

## Local “Phone Call” Test
A helper script starts the agent for local experimentation:
```bash
python test_local_call.py
```

## Notes
- Telephony (e.g., Vonage) is intentionally excluded for now; the code is ready for later integration.
- Whisper and ElevenLabs dependencies are optional but recommended for realistic performance.
- In environments without audio hardware (like some containers), enable the mock flags to exercise the pipeline without sound.
