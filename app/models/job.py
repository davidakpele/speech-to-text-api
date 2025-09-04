# app/models/job.py
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.models.audio import AudioMetadata

Base = declarative_base()

class Job(Base):
    """SQLAlchemy model representing an audio processing job."""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    audio_path = Column(String, nullable=False)
    transcript_path = Column(String, nullable=True)
    translated_transcript_path = Column(String, nullable=True)
    audio_metadata = Column(JSON, nullable=True)  # renamed from metadata
    insights = Column(JSON, nullable=True)
    summary_path = Column(String, nullable=True)
    status = Column(String, default="pending")
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

# Pydantic model for Redis/API
class JobStatus(BaseModel):
    status: str
    original_filename: Optional[str] = None
    audio_path: str
    metadata: AudioMetadata  # keep as Pydantic field
    insights: Dict[str, Any]
    transcript_path: Optional[str] = None
    translated_transcript_path: Optional[str] = None
    translated_language_code: Optional[str] = None
    summary_path: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
