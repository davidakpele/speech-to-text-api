# project/app/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Audio Analysis API"
    APP_VERSION: str = "2.0.0"

    SECRET_KEY: str = Field(..., description="Key for token encryption")
    DATABASE_URL: str
    debug: bool = False
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Directories
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    SUMMARY_DIR: Path = BASE_DIR / "summaries"

    # Model configuration
    OLLAMA_MODEL: str = "finalend/hermes-3-llama-3.1:8b"
    OLLAMA_HOST: str = Field("localhost:11434", description="Ollama server host and port")
    WHISPER_MODEL: Literal["tiny", "base", "small", "medium", "large"] = "tiny"

    # File limits
    MAX_FILE_SIZE: int = 104857600  # 100 MB

    # Redis and Rate Limiting
    REDIS_URL: str = "redis://redis:6379/0"
    
    RATE_LIMIT_PER_MINUTE: int = 10

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.OUTPUT_DIR.mkdir(exist_ok=True)
settings.SUMMARY_DIR.mkdir(exist_ok=True)

# Language code mapping for better translation
LANGUAGE_MAP = {
    "spanish": "es",
    "english": "en",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "chinese": "zh",
    "japanese": "ja",
    "korean": "ko",
    "russian": "ru",
    "arabic": "ar",
    "hindi": "hi"
}