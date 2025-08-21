#
# Final Fixed main.py with FFmpeg Pre-processing
# This version adds a robust audio conversion step using ffmpeg
# to ensure the Whisper model always receives a compatible file.
#

import uvicorn
import shutil
import uuid
import os
import json
import requests
import whisper
import subprocess
try:
    import magic
except ImportError:
    # Fallback for systems where python-magic isn't available
    magic = None
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# --- Configuration and Setup ---

# Initialize FastAPI app
app = FastAPI()

# Mount the static directory for CSS and JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates to look in the 'templates' directory
templates = Jinja2Templates(directory="templates")

# Define directories for file storage and output
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
SUMMARY_DIR = Path("summaries")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
SUMMARY_DIR.mkdir(exist_ok=True)

# Global dictionary to store the status of each job
JOB_STATUS = {}

# Load the Whisper model globally
try:
    WHISPER_MODEL = whisper.load_model("small")
except Exception as e:
    print(f"Failed to load Whisper model: {e}")
    WHISPER_MODEL = None

# --- Helper Functions ---

def format_duration(seconds):
    """Converts a duration in seconds to a human-readable mm:ss format."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def generate_ollama_response(prompt: str, model: str = "llama3"):
    """
    Sends a request to the local Ollama API and returns the generated text.
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        return f"Error: Failed to connect to Ollama. Is the server running? Details: {e}"

def get_file_metadata(file_path):
    """Get basic file metadata without pydub"""
    try:
        file_size = os.path.getsize(file_path)
        size_mb = round(file_size / 1024 / 1024, 2)
        
        mime_type = "unknown"
        if magic:
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
            except Exception:
                pass
        
        return {
            "size": f"{size_mb} MB",
            "format": mime_type
        }
    except Exception:
        return {
            "size": "unknown",
            "format": "unknown"
        }

def convert_audio_to_wav(input_path: Path, output_path: Path):
    """
    Converts an audio file to WAV format using FFmpeg.
    
    This is a critical step to ensure Whisper's compatibility, as it
    avoids potential issues with different audio codecs and formats.
    """
    try:
        # Check if ffmpeg is in the system's PATH
        subprocess.run(
            ['ffmpeg', '-version'], 
            check=True, 
            capture_output=True, 
            text=True
        )
        
        print(f"Converting '{input_path.name}' to WAV...")
        
        # Use subprocess to run the ffmpeg command
        command = [
            'ffmpeg',
            '-i', str(input_path.resolve()),  # Input file
            '-acodec', 'pcm_s16le',           # PCM 16-bit signed little-endian audio codec
            '-ar', '16000',                   # 16 kHz sample rate (optimal for Whisper)
            '-ac', '1',                       # Mono channel
            str(output_path.resolve())        # Output file
        ]
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print("Conversion successful.")
        return True
    except FileNotFoundError:
        print("FFmpeg not found. Please ensure it's installed and in your system's PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg conversion failed with error: {e.stderr}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during FFmpeg conversion: {e}")
        return False

# --- Background Processing Task ---

def process_audio_file_task(file_id: str):
    """
    The main background task that handles all audio processing.
    """
    job_info = JOB_STATUS[file_id]
    audio_path = Path(job_info['audio_path'])
    wav_path = audio_path.parent / (audio_path.stem + ".wav")

    try:
        # Check if file exists before processing
        if not audio_path.exists():
            job_info['status'] = "error"
            job_info['error_message'] = f"Audio file not found at path: {audio_path}"
            print(f"Error: Audio file not found for job {file_id}. Path: {audio_path}")
            return
        
        # --- NEW: Convert to WAV first ---
        if not convert_audio_to_wav(audio_path, wav_path):
            job_info['status'] = "error"
            job_info['error_message'] = "Failed to convert audio file to WAV format."
            return

        # 1. Extract basic file metadata
        file_metadata = get_file_metadata(audio_path)
        job_info['metadata']['size'] = file_metadata['size']
        job_info['metadata']['format'] = file_metadata['format']

        # 2. Transcribe with Whisper using the new WAV file
        transcribe_path_str = str(wav_path.resolve())
        print(f"Starting transcription for file: {transcribe_path_str}")
        if not WHISPER_MODEL:
            raise RuntimeError("Whisper model is not loaded. Cannot transcribe.")

        transcription_result = WHISPER_MODEL.transcribe(transcribe_path_str)
        transcript = transcription_result["text"]
        detected_language = transcription_result["language"]
        
        if "segments" in transcription_result and transcription_result["segments"]:
            duration = transcription_result["segments"][-1]["end"]
            job_info['metadata']['duration'] = format_duration(duration)
        else:
            job_info['metadata']['duration'] = "N/A"
        
        transcript_path = OUTPUT_DIR / f"{file_id}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        job_info['transcript_path'] = str(transcript_path)
        job_info['metadata']['language'] = detected_language

        # 3. Generate AI-Powered Summaries via Ollama
        try:
            descriptive_prompt = f"In one sentence, describe the main topic of this transcription: '{transcript}'"
            descriptive_line = generate_ollama_response(descriptive_prompt)

            abstract_prompt = f"Extract the most important facts from this transcription: names, dates, decisions, locations, or actions. Present as 3-5 concise bullet points. Respond in the same language as the input. Transcription: '{transcript}'"
            abstract_text = generate_ollama_response(abstract_prompt)

            summary_path = SUMMARY_DIR / f"{file_id}.json"
            summary_data = {
                "descriptive_line": descriptive_line,
                "abstract": abstract_text
            }
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=4)
            
            job_info['summary_path'] = str(summary_path)
            job_info['insights'] = summary_data
        except Exception as e:
            print(f"Ollama summarization failed: {e}")
            job_info['insights'] = {
                "descriptive_line": "Summarization service unavailable",
                "abstract": "Please check if Ollama is running on localhost:11434"
            }

        # 4. Mark as completed
        job_info['status'] = "completed"
        print(f"Successfully processed file: {file_id}")

    except Exception as e:
        job_info['status'] = "error"
        job_info['error_message'] = str(e)
        print(f"Error processing file {file_id}: {e}")
    finally:
        # Clean up both the original and converted files
        try:
            if audio_path.exists():
                os.remove(audio_path)
                print(f"Cleaned up uploaded file: {audio_path}")
            if wav_path.exists():
                os.remove(wav_path)
                print(f"Cleaned up converted file: {wav_path}")
        except Exception as e:
            print(f"Error cleaning up files for {file_id}: {e}")

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serves the main file upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def create_upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Handles audio file upload and starts a background task."""
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / file_id
    
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        print(f"[INFO] Saved file to disk: {file_path.resolve()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    finally:
        pass

    JOB_STATUS[file_id] = {
        "status": "processing",
        "original_filename": file.filename,
        "audio_path": str(file_path),
        "metadata": {
            "filename": file.filename,
            "size": "N/A",
            "duration": "N/A",
            "format": "N/A",
            "language": "N/A"
        },
        "insights": {},
        "transcript_path": None,
        "summary_path": None
    }
    background_tasks.add_task(process_audio_file_task, file_id)
    
    return RedirectResponse(url=f"/status/{file_id}", status_code=303)

@app.get("/status/{file_id}", response_class=HTMLResponse)
async def get_status(request: Request, file_id: str):
    """Displays the status of a specific transcription job."""
    job_info = JOB_STATUS.get(file_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job ID not found")

    return templates.TemplateResponse(
        "status.html",
        {"request": request, "job_info": job_info, "file_id": file_id}
    )

@app.get("/api/status/{file_id}")
async def api_get_status(file_id: str):
    """API endpoint for client-side polling."""
    job_info = JOB_STATUS.get(file_id)
    if not job_info:
        return {"status": "not_found"}

    response_data = job_info.copy()
    response_data.pop("audio_path", None)
    response_data.pop("transcript_path", None)
    response_data.pop("summary_path", None)
    
    return response_data

@app.get("/download/{file_id}")
async def download_transcript(file_id: str):
    """Provides a downloadable link to the transcription text file."""
    transcript_path = OUTPUT_DIR / f"{file_id}.txt"
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return HTMLResponse(content, media_type="text/plain")

# Main entry point for uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

