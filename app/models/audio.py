from pydantic import BaseModel, Field

class AudioMetadata(BaseModel):
    """Pydantic model for audio file metadata."""
    filename: str = Field(..., description="Original filename of the audio file.")
    size: str = Field(..., description="Human-readable file size.")
    format: str = Field(..., description="Detected file format (e.g., 'audio/mpeg').")
    duration: str = Field(..., description="Human-readable duration (e.g., '05:30').")
    detected_language: str = Field(..., description="Language detected by the transcription model.")
    target_language: str = Field(..., description="The language requested for translation.")
