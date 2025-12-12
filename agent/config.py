"""Configuration management for the local telephone agent."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Environment-driven settings with sensible defaults."""

    sample_rate: int = 16000
    frame_duration_ms: int = 30  # ~33 fps
    channels: int = 1
    block_size: int = 0  # Let sounddevice choose optimal block size

    deepgram_api_key: str | None = os.getenv("DEEPGRAM_API_KEY")
    deepseek_api_key: str | None = os.getenv("DEEPSEEK_API_KEY")
    elevenlabs_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")

    use_mock_audio: bool = os.getenv("USE_MOCK_AUDIO", "false").lower() == "true"
    use_mock_llm: bool = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    use_mock_tts: bool = os.getenv("USE_MOCK_TTS", "false").lower() == "true"

    whisper_model: str = os.getenv("WHISPER_MODEL", "base")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    elevenlabs_voice: str = os.getenv("ELEVENLABS_VOICE", "Bella")

    # Billing values that mirror the Vonage Agent server control page.
    vonage_per_minute_charge: float = float(os.getenv("VONAGE_PER_MINUTE_CHARGE", "0.05"))
    vonage_connection_charge: float = float(os.getenv("VONAGE_CONNECTION_CHARGE", "0.0"))
    vonage_rounding_increment_seconds: int = int(os.getenv("VONAGE_ROUNDING_INCREMENT_SECONDS", "60"))


settings = Settings()
