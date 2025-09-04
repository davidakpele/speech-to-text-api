# project/app/services/transcription.py
import whisper
from app.config import settings

# Load the Whisper model globally
try:
    WHISPER_MODEL = whisper.load_model(settings.WHISPER_MODEL)
    print("✅ Whisper model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Whisper model: {e}")
    WHISPER_MODEL = None

class TranscriptionService:
    def transcribe_audio(self, file_path: str) -> dict:
        """Transcribes an audio file using the pre-loaded Whisper model."""
        if not WHISPER_MODEL:
            raise RuntimeError("Whisper model is not loaded. Cannot transcribe.")
        
        print(f"Starting transcription for file: {file_path}")
        transcription_result = WHISPER_MODEL.transcribe(file_path)
        print("✅ Transcription successful.")
        return transcription_result

# Create a singleton instance
transcription_service = TranscriptionService()