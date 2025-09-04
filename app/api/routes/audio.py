import shutil
import uuid
import os
import json
import time
from pathlib import Path
from fastapi import Form, UploadFile, File, Request, BackgroundTasks, HTTPException, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
import requests

# Import services, models, and utilities
from app.config import settings
from app.models.audio import AudioMetadata
from app.models.job import JobStatus
from app.services.transcription import transcription_service
from app.services.translation import translation_service
from app.services.analysis import analysis_service
from app.tasks.audio_processing import update_job_status_in_redis
from app.utils.redis_client import get_all_jobs, redis_client, get_job_status
from app.utils.file_handlers import get_file_metadata, convert_audio_to_wav
from app.utils.validators import extract_language_code

# Initialize the router and templates
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Global dictionary to store the status of each job
JOB_STATUS = {}

# project/app/api/routes/audio.py

def process_audio_file_task(file_id: str):
    """The main background task that handles all audio processing."""
    job_info = JOB_STATUS[file_id]
    audio_path = Path(job_info.audio_path)
    wav_path = audio_path.parent / (audio_path.stem + ".wav")

    try:
        if not audio_path.exists():
            job_info.status = "error"
            job_info.error_message = f"Audio file not found at path: {audio_path}"
            update_job_status_in_redis(
                job_info,
                job_info.metadata.dict() if job_info.metadata else {},
                job_info.metadata.target_language if job_info.metadata else "none"
            )

            print(f"❌ Error: Audio file not found for job {file_id}")
            return

        # --- Metadata ---
        job_info.status = "processing"
        file_metadata = get_file_metadata(audio_path)
        job_info.metadata = AudioMetadata(**{**job_info.metadata.dict(), **file_metadata})
        update_job_status_in_redis(
            job_info,
            job_info.metadata.dict() if job_info.metadata else {},
            job_info.metadata.target_language if job_info.metadata else "none"
        )


        # --- Convert to WAV ---
        job_info.status = "converting"
        update_job_status_in_redis(
            job_info,
            job_info.metadata.dict() if job_info.metadata else {},
            job_info.metadata.target_language if job_info.metadata else "none"
        )

        if not convert_audio_to_wav(audio_path, wav_path):
            job_info.status = "error"
            job_info.error_message = "Failed to convert audio file to WAV format."
            update_job_status_in_redis(
                job_info,
                job_info.metadata.dict() if job_info.metadata else {},
                job_info.metadata.target_language if job_info.metadata else "none"
            )

            return

        # --- Transcription ---
        job_info.status = "transcribing"
        update_job_status_in_redis(
            job_info,
            job_info.metadata.dict() if job_info.metadata else {},
            job_info.metadata.target_language if job_info.metadata else "none"
        )


        transcription_result = transcription_service.transcribe_audio(str(wav_path.resolve()))
        transcript = transcription_result["text"]
        detected_language = transcription_result.get("language", "en")

        transcript_path = settings.OUTPUT_DIR / f"{file_id}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        job_info.transcript_path = str(transcript_path)
        job_info.metadata.detected_language = detected_language
        update_job_status_in_redis(
            job_info,
            job_info.metadata.dict() if job_info.metadata else {},
            job_info.metadata.target_language if job_info.metadata else "none"
        )


        # --- Translation ---
        target_lang = job_info.metadata.target_language
        if target_lang != "none":
            job_info.status = "translating"
            update_job_status_in_redis(
                job_info,
                job_info.metadata.dict() if job_info.metadata else {},
                job_info.metadata.target_language if job_info.metadata else "none"
            )


            target_lang_code = extract_language_code(target_lang)
            print(f"Translating transcript to {target_lang} ({target_lang_code})...")

            if target_lang_code != detected_language:
                translated_text = translation_service.translate_text(transcript, target_lang_code)
                translated_transcript_path = settings.OUTPUT_DIR / f"{file_id}_{target_lang_code}.txt"
                with open(translated_transcript_path, "w", encoding="utf-8") as f:
                    f.write(translated_text)

                job_info.translated_transcript_path = str(translated_transcript_path)
                job_info.translated_language_code = target_lang_code
            else:
                print("Target language same as detected language, skipping translation")
                job_info.translated_transcript_path = str(transcript_path)
                job_info.translated_language_code = detected_language

            update_job_status_in_redis(
                job_info,
                job_info.metadata.dict() if job_info.metadata else {},
                job_info.metadata.target_language if job_info.metadata else "none"
            )


        # --- Analysis ---
        job_info.status = "analyzing"
        update_job_status_in_redis(
            job_info,
            job_info.metadata.dict() if job_info.metadata else {},
            job_info.metadata.target_language if job_info.metadata else "none"
        )


        print("Generating AI insights...")
        analysis_result = analysis_service.analyze_transcript(transcript)

        summary_path = settings.SUMMARY_DIR / f"{file_id}.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=4, ensure_ascii=False)

        job_info.summary_path = str(summary_path)
        job_info.insights = analysis_result

        # --- Completed ---
        job_info.status = "completed"
        job_info.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")
        update_job_status_in_redis(
            job_info,
            job_info.metadata.dict() if job_info.metadata else {},
            job_info.metadata.target_language if job_info.metadata else "none"
        )


        print(f"✅ Successfully processed file: {file_id}")

    except Exception as e:
        job_info.status = "error"
        job_info.error_message = str(e)
        update_job_status_in_redis(
            job_info,
            job_info.metadata.dict() if job_info.metadata else {},
            job_info.metadata.target_language if job_info.metadata else "none"
        )

        print(f"❌ Error processing file {file_id}: {e}")

    finally:
        try:
            if wav_path.exists():
                os.remove(wav_path)
                print(f"Cleaned up converted file: {wav_path}")
        except Exception as e:
            print(f"Warning: Error cleaning up WAV file: {e}")



@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serves the main file upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload", response_class=HTMLResponse)
async def create_upload_file(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    target_language: str = Form(default="none") 
):
    """Handles audio file upload and starts a background task."""
    file_id = str(uuid.uuid4())
    file_path = settings.UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        print(f"✅ Saved file to disk: {file_path.name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    job_metadata = AudioMetadata(
        filename=file.filename,
        size="Calculating...",
        format="Detecting...",
        duration="Calculating...",
        detected_language="Detecting...",
        target_language=target_language
    )
    
    JOB_STATUS[file_id] = JobStatus(
        status="processing",
        original_filename=file.filename,
        audio_path=str(file_path),
        metadata=job_metadata,
        insights={
            "comprehensive_summary": "Generating...",
            "short_summary": "Processing audio and generating insights...",
            "key_insights": []
        },
        started_at=time.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    background_tasks.add_task(process_audio_file_task, file_id)
    return RedirectResponse(url=f"/status/{file_id}", status_code=303)

@router.get("/status/{file_id}", response_class=HTMLResponse)
async def get_status(request: Request, file_id: str):
    """Displays the status of a specific transcription job."""
    job_info = JOB_STATUS.get(file_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job ID not found")

    return templates.TemplateResponse(
        "status.html",
        {"request": request, "job_info": job_info.dict(), "file_id": file_id}
    )

@router.get("/api/status/{file_id}")
async def api_get_status(file_id: str):
    """API endpoint for client-side polling."""
    job_info = JOB_STATUS.get(file_id)
    if not job_info:
        return {"status": "not_found"}

    response_data = job_info.dict()
    response_data.pop("audio_path", None)
    response_data.pop("transcript_path", None)
    response_data.pop("translated_transcript_path", None)
    response_data.pop("summary_path", None)
    
    if job_info.transcript_path:
        response_data["transcript_download_url"] = f"/download/transcript/{file_id}"
        
    if job_info.translated_transcript_path:
        response_data["translated_transcript_download_url"] = f"/download/translated_transcript/{file_id}"
        
    if job_info.summary_path:
        response_data["summary_download_url"] = f"/download/summary/{file_id}"
        
    return response_data

@router.get("/download/transcript/{file_id}")
async def download_transcript(file_id: str):
    """Download the transcription text file."""
    transcript_path = settings.OUTPUT_DIR / f"{file_id}.txt"
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return FileResponse(
        transcript_path,
        media_type="text/plain",
        filename=f"transcript_{file_id}.txt"
    )

@router.get("/download/summary/{file_id}")
async def download_summary(file_id: str):
    """Download the summary JSON file."""
    summary_path = settings.SUMMARY_DIR / f"{file_id}.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return FileResponse(
        summary_path,
        media_type="application/json",
        filename=f"summary_{file_id}.json"
    )

@router.get("/download/translated_transcript/{file_id}")
async def download_translated_transcript(file_id: str):
    """Download the translated transcription text file."""
    job_info = JOB_STATUS.get(file_id)
    if not job_info or not job_info.translated_transcript_path:
        raise HTTPException(status_code=404, detail="Translated transcript not found")

    translated_path = Path(job_info.translated_transcript_path)
    
    return FileResponse(
        translated_path,
        media_type="text/plain",
        filename=f"translated_transcript_{file_id}.txt"
    )
    
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    ollama_available = False
    ollama_models = []
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_available = True
            ollama_models = [m["name"] for m in response.json().get("models", [])]
    except:
        pass
    
    # UPDATED: Check if Whisper model is loaded correctly
    from app.services.transcription import WHISPER_MODEL
    
    return {
        "status": "healthy",
        "whisper_loaded": WHISPER_MODEL is not None,
        "ollama_available": ollama_available,
        "ollama_models": ollama_models,
        "preferred_model": settings.OLLAMA_MODEL,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@router.get("/jobs/{job_id}", response_model=JobStatus)
def read_job(job_id: str):
    job_json = get_job_status(job_id)
    if not job_json:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(**json.loads(job_json))

@router.get("/jobs", response_model=list[JobStatus])
def list_jobs():
    """
    List all jobs currently saved in Redis.
    """
    job_ids = get_all_jobs() 
    jobs = []

    for job_id in job_ids:
        job_json = get_job_status(job_id)
        if job_json:
            try:
                job_data = json.loads(job_json)
                jobs.append(JobStatus(**job_data))
            except json.JSONDecodeError:
                continue  # Skip corrupted jobs

    return jobs
