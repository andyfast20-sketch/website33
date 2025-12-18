from __future__ import annotations
from dataclasses import dataclass
import os

@dataclass
class Settings:
    sample_rate: int = 44100  # Record at Jabra's native rate
    whisper_rate: int = 16000  # Whisper expects 16kHz - we resample
    frame_duration_ms: int = 30
    channels: int = 1
    block_size: int = 0

    stt_provider: str = "whisper_local"

    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_model: str = "deepseek-chat"
    
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    use_mock_audio: bool = False
    use_mock_tts: bool = False
    use_mock_llm: bool = False

settings = Settings()
