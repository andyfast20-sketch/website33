from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Settings:
    sample_rate: int = 44100  # Record at Jabra's native rate
    whisper_rate: int = 16000  # Whisper expects 16kHz - we resample
    frame_duration_ms: int = 30
    channels: int = 1
    block_size: int = 0

    stt_provider: str = "whisper_local"

    deepseek_api_key: str = "sk-0b54e89d08554cf8aff13b5d181ff5ad"
    deepseek_model: str = "deepseek-chat"
    
    openai_api_key: str = "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"

    use_mock_audio: bool = False
    use_mock_tts: bool = False
    use_mock_llm: bool = False

settings = Settings()
