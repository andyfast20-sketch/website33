"""Simple test to record audio and send to OpenAI Whisper."""
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import io
import requests
import os

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

# Record 4 seconds of audio
print("Recording for 4 seconds... Say 'What is the capital of Germany?'")
print("Using device 19 (WASAPI Jabra)")

# Record at native sample rate
duration = 4
sample_rate = 44100
audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32', device=19)
sd.wait()

print(f"Recorded {len(audio)} samples, max amplitude: {np.max(np.abs(audio)):.4f}")

# Resample to 16kHz for Whisper
from scipy import signal
audio_16k = signal.resample(audio.flatten(), int(len(audio) * 16000 / sample_rate))
print(f"Resampled to {len(audio_16k)} samples at 16kHz")

# Save to WAV
audio_int16 = (audio_16k * 32767).astype(np.int16)
wav_buffer = io.BytesIO()
wavfile.write(wav_buffer, 16000, audio_int16)
wav_buffer.seek(0)

# Also save to file for manual inspection
with open("test_recording.wav", "wb") as f:
    wav_buffer.seek(0)
    f.write(wav_buffer.read())
    wav_buffer.seek(0)
print("Saved to test_recording.wav - you can play this to check quality")

# Send to OpenAI
print("\nSending to OpenAI Whisper...")
response = requests.post(
    "https://api.openai.com/v1/audio/transcriptions",
    headers={"Authorization": f"Bearer {OPENAI_KEY}"},
    files={"file": ("audio.wav", wav_buffer, "audio/wav")},
    data={"model": "whisper-1", "language": "en"}
)

if response.status_code == 200:
    print(f"\n=== TRANSCRIPTION ===")
    print(response.text)
    print(f"=====================")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
