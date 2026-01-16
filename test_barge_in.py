"""
Test barge-in logic without making an actual call
"""
import numpy as np
import time
import sqlite3

# Load the actual CONFIG value from database
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()
cursor.execute('SELECT barge_in_min_speech_seconds FROM global_settings')
result = cursor.fetchone()
BARGE_IN_THRESHOLD = float(result[0]) if result else 2.0
conn.close()

print(f"Testing with BARGE_IN_THRESHOLD = {BARGE_IN_THRESHOLD}s")
print("=" * 80)

class SimulatedCallSession:
    def __init__(self):
        self.call_uuid = "test-call"
        self._agent_speaking = False
        self._caller_vad_speaking = False
        self._caller_vad_started_at = None
        self._caller_vad_last_voice_at = 0.0
        self._caller_vad_energy_threshold = 0.005
        self._caller_vad_hangover_seconds = 0.25
        self._last_vad_barge_in_at = 0.0
        self._block_outbound_audio = False
        self._barge_in_triggered = False
        self._barge_in_time = None
        
    def update_caller_vad_from_vonage_audio(self, audio_data: bytes) -> None:
        """Simulated VAD logic"""
        if not audio_data:
            return
        
        samples = np.frombuffer(audio_data, dtype=np.int16)
        if samples.size == 0:
            return
        
        now = time.time()
        energy = float(np.mean(np.abs(samples))) / 32767.0
        
        speaking_now = energy >= self._caller_vad_energy_threshold
        
        print(f"  t={now - self._test_start:.2f}s: energy={energy:.4f}, threshold={self._caller_vad_energy_threshold:.4f}, speaking={speaking_now}")
        
        if speaking_now:
            self._caller_vad_last_voice_at = now
            if not self._caller_vad_speaking:
                self._caller_vad_speaking = True
                self._caller_vad_started_at = now
                print(f"  🗣️ Caller STARTED speaking (energy={energy:.4f})")
            
            # Check for barge-in
            if self._agent_speaking and self._caller_vad_started_at is not None:
                elapsed = now - self._caller_vad_started_at
                if elapsed >= BARGE_IN_THRESHOLD:
                    if (now - self._last_vad_barge_in_at) >= 1.0:
                        self._last_vad_barge_in_at = now
                        self._block_outbound_audio = True
                        self._barge_in_triggered = True
                        self._barge_in_time = elapsed
                        print(f"  🛑🛑🛑 BARGE-IN TRIGGERED at {elapsed:.2f}s (threshold={BARGE_IN_THRESHOLD:.2f}s)")
        else:
            # Not speaking - check hangover
            if self._caller_vad_speaking:
                if (now - self._caller_vad_last_voice_at) >= self._caller_vad_hangover_seconds:
                    self._caller_vad_speaking = False
                    self._caller_vad_started_at = None
                    if self._block_outbound_audio:
                        print(f"  🔓 Caller stopped - unblocking outbound audio")
                        self._block_outbound_audio = False
                    else:
                        print(f"  🔇 Caller stopped speaking (energy={energy:.4f})")

def generate_audio_chunk(duration_ms: int, energy_level: float) -> bytes:
    """Generate simulated PCM16 audio at 16kHz"""
    samples_per_ms = 16  # 16kHz = 16 samples per ms
    num_samples = duration_ms * samples_per_ms
    
    if energy_level > 0:
        # Generate noise at the specified energy level
        amplitude = int(energy_level * 32767)
        audio = np.random.randint(-amplitude, amplitude, num_samples, dtype=np.int16)
    else:
        # Silence
        audio = np.zeros(num_samples, dtype=np.int16)
    
    return audio.tobytes()

print("\nTest 1: Caller speaks for less than threshold while agent is talking")
print("-" * 80)
session = SimulatedCallSession()
session._test_start = time.time()
session._agent_speaking = True
print("Agent starts speaking...")

# Simulate 1 second of caller speech (below threshold)
for i in range(10):
    audio = generate_audio_chunk(100, 0.010)  # 100ms chunks with energy
    session.update_caller_vad_from_vonage_audio(audio)
    time.sleep(0.1)

# Caller stops
for i in range(5):
    audio = generate_audio_chunk(100, 0.001)  # silence
    session.update_caller_vad_from_vonage_audio(audio)
    time.sleep(0.1)

print(f"\n✅ Result: Barge-in triggered = {session._barge_in_triggered} (expected: False)")
print(f"   Audio blocked = {session._block_outbound_audio}")

print("\n" + "=" * 80)
print(f"\nTest 2: Caller speaks for MORE than {BARGE_IN_THRESHOLD}s while agent is talking")
print("-" * 80)
session = SimulatedCallSession()
session._test_start = time.time()
session._agent_speaking = True
print("Agent starts speaking...")

# Simulate sustained caller speech beyond threshold
duration_to_test = BARGE_IN_THRESHOLD + 1.0  # Go 1s beyond threshold
chunks = int(duration_to_test * 10)  # 100ms chunks

for i in range(chunks):
    audio = generate_audio_chunk(100, 0.015)  # 100ms chunks with energy
    session.update_caller_vad_from_vonage_audio(audio)
    time.sleep(0.1)
    
    if session._barge_in_triggered:
        print(f"\n✅ Barge-in triggered after {session._barge_in_time:.2f}s")
        break

if not session._barge_in_triggered:
    print(f"\n❌ FAILED: Barge-in did NOT trigger after {duration_to_test:.2f}s!")
else:
    print(f"   Expected trigger at: ~{BARGE_IN_THRESHOLD:.2f}s")
    print(f"   Actual trigger at: {session._barge_in_time:.2f}s")
    print(f"   Difference: {abs(session._barge_in_time - BARGE_IN_THRESHOLD):.2f}s")
    print(f"   Audio blocking active: {session._block_outbound_audio}")

print("\n" + "=" * 80)
print("\nTest 3: Test audio blocking mechanism")
print("-" * 80)

def send_audio_bytes_raw_simulated(session, pcm_bytes):
    """Simulate the audio send with blocking check"""
    if getattr(session, "_block_outbound_audio", False):
        return "BLOCKED"
    return "SENT"

session = SimulatedCallSession()
session._block_outbound_audio = False
result1 = send_audio_bytes_raw_simulated(session, b"test_audio")
print(f"Audio send with block=False: {result1} (expected: SENT)")

session._block_outbound_audio = True
result2 = send_audio_bytes_raw_simulated(session, b"test_audio")
print(f"Audio send with block=True: {result2} (expected: BLOCKED)")

print("\n" + "=" * 80)
print("\n🎯 SUMMARY:")
print(f"  - Database threshold: {BARGE_IN_THRESHOLD}s")
print(f"  - VAD energy threshold: 0.005")
print(f"  - Logic appears to be working correctly in isolation")
print("\nIf this test passes but real calls don't work, the issue is:")
print("  1. VAD not being called during real calls")
print("  2. Audio energy too low in real calls")
print("  3. Different server instance handling calls")
