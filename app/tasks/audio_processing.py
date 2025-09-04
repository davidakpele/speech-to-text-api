import subprocess
import json
from pathlib import Path
import time
import structlog
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import settings
from app.models.audio import AudioMetadata
from app.services.transcription import transcription_service
from app.services.translation import translation_service
from app.services.analysis import analysis_service
from app.utils.file_handlers import get_file_metadata
from app.database import get_db
from app.models.job import Job, JobStatus
from app.utils.redis_client import save_job_status

logger = structlog.get_logger()

def convert_audio_to_wav(input_path: Path, output_path: Path) -> bool:
    """Convert audio file to WAV format using FFmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True, text=True)
        
        logger.info("Converting audio to WAV", input_path=str(input_path))
        
        command = [
            'ffmpeg', '-i', str(input_path.resolve()),
            '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            '-y',
            str(output_path.resolve())
        ]
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        logger.info("Audio conversion successful", output_path=str(output_path))
        return True
        
    except FileNotFoundError:
        logger.error("FFmpeg not found")
        return False
    except subprocess.CalledProcessError as e:
        logger.error("FFmpeg conversion failed", error=e.stderr)
        return False
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timed out")
        return False
    except Exception as e:
        logger.error("Unexpected error during conversion", error=str(e))
        return False

def process_audio_file_task(job_id: str, target_language: str):
    """Background task to process audio file"""
    db_gen = get_db()
    db: Session = next(db_gen)

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error("Job not found", job_id=job_id)
        return

    audio_file = Path(job.audio_path)
    wav_path = audio_file.parent / (audio_file.stem + ".wav")

    try:
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        # Update job status and metadata
        job.status = "processing"
        job.metadata = get_file_metadata(audio_file)
        job.insights = {
            "comprehensive_summary": "Generating...",
            "short_summary": "Processing audio and generating insights...",
            "key_insights": []
        }
        job.started_at = datetime.utcnow()
        db.commit()

        # Convert to WAV if needed
        if not convert_audio_to_wav(audio_file, wav_path):
            raise RuntimeError("Failed to convert audio file to WAV format")
        
        # Transcribe audio
        transcription_result = transcription_service.transcribe_audio(wav_path)
        transcript = transcription_result["text"]
        detected_language = transcription_result["language"]
        
        # Save transcript
        transcript_path = Path(settings.output_dir) / f"{job_id}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        job.transcript_path = str(transcript_path)
        if job.metadata is None:
            job.metadata = {}
        job.metadata["detected_language"] = detected_language
        db.commit()

        # Translate if requested and needed
        if target_language != "none" and target_language != detected_language:
            logger.info("Translating transcript", 
                       source_language=detected_language,
                       target_language=target_language)
            
            translated_text = translation_service.translate_text(transcript, target_language)
            
            translated_path = Path(settings.output_dir) / f"{job_id}_{target_language}.txt"
            with open(translated_path, "w", encoding="utf-8") as f:
                f.write(translated_text)
            
            job.translated_transcript_path = str(translated_path)
        else:
            job.translated_transcript_path = str(transcript_path)
        db.commit()

        # Generate analysis and insights
        analysis_result = analysis_service.analyze_transcript(transcript)
        
        # Save summary
        summary_path = Path(settings.summary_dir) / f"{job_id}.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=4, ensure_ascii=False)
        
        job.summary_path = str(summary_path)
        job.insights = analysis_result
        
        # Mark as completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info("Audio processing completed", job_id=job_id)
        
    except Exception as e:
        job.status = "error"
        job.error_message = str(e)
        db.commit()

        logger.error("Audio processing failed", 
                    job_id=job_id,
                    error=str(e))
    
    finally:
        # Cleanup temporary files
        try:
            if wav_path.exists():
                wav_path.unlink()
                logger.info("Cleaned up temporary WAV file", path=str(wav_path))
        except Exception as e:
            logger.warning("Failed to clean up temporary file", 
                          path=str(wav_path),
                          error=str(e))
        db.close()

def update_job_status_in_redis(job_status: JobStatus, metadata: dict, target_language: str):
    """Serialize JobStatus → Redis using job UUID as key."""
    try:
        audio_metadata = AudioMetadata(**metadata)

        job_data = {
            "status": job_status.status,
            "original_filename": metadata.get("filename"),
            "audio_path": job_status.audio_path,
            "metadata": audio_metadata.dict(),
            "insights": job_status.insights,
            "transcript_path": job_status.transcript_path,
            "translated_transcript_path": job_status.translated_transcript_path,
            "translated_language_code": target_language,
            "summary_path": job_status.summary_path,
            "started_at": job_status.started_at,
            "completed_at": job_status.completed_at,
            "error_message": job_status.error_message,
        }

        # 🔹 Print for debugging
        print(f"📌 Preparing to save job to Redis:\n{json.dumps(job_data, indent=4)}")

        # Extract UUID from the audio filename
        job_id = Path(job_status.audio_path).stem.split("_")[0]

        # Save using UUID as Redis key
        save_job_status(job_id, job_data)

        print(f"✅ Saved job to Redis with key: {job_id}")

    except Exception as e:
        print(f"❌ Failed to update Redis for job: {e}")
        raise
