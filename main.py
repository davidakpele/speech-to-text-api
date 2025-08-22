import uvicorn
import shutil
import uuid
import os
import json
import requests
import whisper
import subprocess
import re
try:
    import magic
except ImportError:
    # Fallback for systems where python-magic isn't available
    magic = None
from pathlib import Path
from fastapi import Form
from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
from typing import Dict, Any, Optional

# --- Configuration and Setup ---

# Initialize FastAPI app
app = FastAPI(title="Audio Analysis API", version="2.0.0")

# Mount the static directory for CSS and JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates to look in the 'templates' directory
templates = Jinja2Templates(directory="templates")

# Define directories for file storage and output
BASE_DIR = Path.cwd()
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
SUMMARY_DIR = BASE_DIR / "summaries"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
SUMMARY_DIR.mkdir(exist_ok=True)

# Global dictionary to store the status of each job
JOB_STATUS: Dict[str, Dict[str, Any]] = {}

# Load the Whisper model globally
try:
    # Using a smaller model for faster processing, but you can change to "base" or "small"
    WHISPER_MODEL = whisper.load_model("tiny")
    print("✅ Whisper model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Whisper model: {e}")
    WHISPER_MODEL = None

# Configuration - Use your OpenLlama model
# Corrected model name: Ollama references models by name, not file extension
OLLAMA_MODEL = "llama3"  # Updated to a more commonly available model

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

# --- Helper Functions ---
def format_duration(seconds):
    """Converts a duration in seconds to a human-readable mm:ss format."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes):
    """Convert file size to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def check_ollama_model_available(model_name):
    """Check if the specified Ollama model is available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(model_name) for m in models)
        return False
    except:
        return False

def extract_language_code(language_input: str) -> str:
    """Extract language code from user input"""
    language_input = language_input.lower().strip()
    
    # Check if it's already a language code
    if len(language_input) == 2 and language_input in LANGUAGE_MAP.values():
        return language_input
    
    # Map language name to code
    return LANGUAGE_MAP.get(language_input, "en")  # Default to English

def generate_comprehensive_summary(transcript: str, model: str = OLLAMA_MODEL):
    """
    Generates a comprehensive summary using Ollama with a structured prompt
    """
    # Check if the model is available, fall back to default if not
    if not check_ollama_model_available(model):
        print(f"Model {model} not available, trying default models")
        # Try some common fallback models
        for fallback_model in ["llama3", "phi3", "mistral", "gemma"]:
            if check_ollama_model_available(fallback_model):
                model = fallback_model
                print(f"Using fallback model: {model}")
                break
        else:
            return "Error: No suitable Ollama model found. Please install at least one model."
    
    try:
        # Create a structured prompt for better summarization
        prompt = f"""
        Please analyze this transcript and provide a comprehensive summary with the following sections:
        
        1. MAIN TOPIC: A one-sentence description of the main topic
        2. KEY POINTS: 3-5 bullet points of the most important information
        3. ACTION ITEMS: Any decisions, actions, or next steps mentioned
        4. PARTICIPANTS: Key people or roles mentioned (if any)
        5. CONTEXT: Additional context about the content
        6. OVERALL SENTIMENT: The general tone or sentiment of the content
        
        Transcript:
        {transcript[:6000]}  # Limit to avoid token limits
        
        Please format your response clearly with section headers.
        """
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model, 
                "prompt": prompt, 
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more focused responses
                    "top_p": 0.9,
                    "num_ctx": 4096  # Context window size
                }
            },
            timeout=300  # 5 minute timeout for longer processing
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        return f"Error: Failed to generate summary. Please ensure Ollama is running."

def generate_short_summary(transcript: str, model: str = OLLAMA_MODEL):
    """Generate a concise one-paragraph summary of the transcript"""
    if not check_ollama_model_available(model):
        for fallback_model in ["llama3", "phi3", "mistral", "gemma"]:
            if check_ollama_model_available(fallback_model):
                model = fallback_model
                break
        else:
            return "Could not generate short summary - no model available"
    
    try:
        prompt = f"Provide a concise one-paragraph summary of the main content from this text: {transcript[:3000]}"
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model, 
                "prompt": prompt, 
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "max_length": 200  # Limit response length
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API for short summary: {e}")
        return "Could not generate short summary"

def get_file_metadata(file_path):
    """Get comprehensive file metadata"""
    try:
        file_size = os.path.getsize(file_path)
        size_formatted = format_file_size(file_size)
        
        mime_type = "unknown"
        if magic:
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
            except Exception:
                pass
        
        # Try to get duration using ffprobe
        duration = "N/A"
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                str(file_path)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                duration_seconds = float(result.stdout.strip())
                duration = format_duration(duration_seconds)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
            pass
        
        return {
            "size": size_formatted,
            "format": mime_type,
            "duration": duration
        }
    except Exception as e:
        print(f"Error getting file metadata: {e}")
        return {
            "size": "unknown",
            "format": "unknown",
            "duration": "unknown"
        }

def convert_audio_to_wav(input_path: Path, output_path: Path):
    """Converts an audio file to WAV format using FFmpeg."""
    try:
        # Check if ffmpeg is available
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True, text=True)
        
        print(f"Converting '{input_path.name}' to WAV...")
        
        command = [
            'ffmpeg', '-i', str(input_path.resolve()),
            '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            '-y',  # Overwrite output file if it exists
            str(output_path.resolve())
        ]
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        print("✅ Conversion successful.")
        return True
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please ensure it's installed.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg conversion failed: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg conversion timed out.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during conversion: {e}")
        return False

def translate_text(text: str, target_language_code: str, model: str = OLLAMA_MODEL):
    """
    Translates text to a specified language using Ollama.
    """
    if not check_ollama_model_available(model):
        print(f"Model {model} not available for translation, trying fallback.")
        for fallback_model in ["llama3", "phi3", "mistral", "gemma"]:
            if check_ollama_model_available(fallback_model):
                model = fallback_model
                print(f"Using fallback model: {model} for translation.")
                break
        else:
            return "Error: No suitable Ollama model found for translation."

    # Use a clear, direct prompt for translation
    prompt = f"Translate the following text into {target_language_code}. Only provide the translated text and nothing else. \n\nText:\n{text[:6000]}"
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model, 
                "prompt": prompt, 
                "stream": False,
                "options": {
                    "temperature": 0.1  # Very low temperature for literal translation
                }
            },
            timeout=300
        )
        response.raise_for_status()
        translated_text = response.json()["response"].strip()
        
        # Clean up the response (sometimes models add explanations)
        if "Here is the translation" in translated_text:
            # Extract just the translated part
            lines = translated_text.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith("Here is"):
                    translated_text = '\n'.join(lines[i:])
                    break
        
        return translated_text
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API for translation: {e}")
        return f"Error: Failed to translate text. Please ensure Ollama is running and has a suitable model."

def extract_key_insights(transcript: str, model: str = OLLAMA_MODEL):
    """Extract key insights from the transcript"""
    if not check_ollama_model_available(model):
        for fallback_model in ["llama3", "phi3", "mistral", "gemma"]:
            if check_ollama_model_available(fallback_model):
                model = fallback_model
                break
        else:
            return ["No AI model available for insights extraction"]
    
    try:
        prompt = f"Extract 3-5 key insights or most important points from this text. Present each as a separate bullet point:\n\n{transcript[:4000]}"
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model, 
                "prompt": prompt, 
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_length": 300
                }
            },
            timeout=120
        )
        response.raise_for_status()
        insights_text = response.json()["response"].strip()
        
        # Parse bullet points from the response
        insights = []
        lines = insights_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Clean up the bullet point
                insight = re.sub(r'^[-•*]\s*', '', line)
                insights.append(insight)
            elif line and len(insights) < 5:  # Limit to 5 insights max
                insights.append(line)
        
        return insights if insights else ["No specific insights could be extracted"]
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API for insights: {e}")
        return ["Failed to extract insights"]

# --- Background Processing Task ---
def process_audio_file_task(file_id: str):
    """The main background task that handles all audio processing."""
    job_info = JOB_STATUS[file_id]
    audio_path = Path(job_info['audio_path'])
    wav_path = audio_path.parent / (audio_path.stem + ".wav")

    try:
        if not audio_path.exists():
            job_info['status'] = "error"
            job_info['error_message'] = f"Audio file not found at path: {audio_path}"
            print(f"❌ Error: Audio file not found for job {file_id}")
            return
        
        # Get file metadata
        file_metadata = get_file_metadata(audio_path)
        job_info['metadata'].update(file_metadata)
        
        # Convert to WAV if needed
        if not convert_audio_to_wav(audio_path, wav_path):
            job_info['status'] = "error"
            job_info['error_message'] = "Failed to convert audio file to WAV format."
            return

        # Transcribe audio
        print(f"Starting transcription for file: {audio_path.name}")
        if not WHISPER_MODEL:
            raise RuntimeError("Whisper model is not loaded. Cannot transcribe.")

        transcription_result = WHISPER_MODEL.transcribe(str(wav_path.resolve()))
        transcript = transcription_result["text"]
        detected_language = transcription_result.get("language", "en")
        
        # Save the ORIGINAL transcription first
        transcript_path = OUTPUT_DIR / f"{file_id}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        job_info['transcript_path'] = str(transcript_path)
        job_info['metadata']['detected_language'] = detected_language

        # Check if a target language was specified and perform translation
        target_lang = job_info['metadata'].get('target_language', 'none')
        if target_lang != "none":
            target_lang_code = extract_language_code(target_lang)
            print(f"Translating transcript to {target_lang} ({target_lang_code})...")
            
            # Only translate if the target language is different from detected language
            if target_lang_code != detected_language:
                translated_text = translate_text(transcript, target_lang_code)

                # Save the translated text to a new file
                translated_transcript_path = OUTPUT_DIR / f"{file_id}_{target_lang_code}.txt"
                with open(translated_transcript_path, "w", encoding="utf-8") as f:
                    f.write(translated_text)
            
                job_info['translated_transcript_path'] = str(translated_transcript_path)
                job_info['translated_language_code'] = target_lang_code
            else:
                print("Target language same as detected language, skipping translation")
                job_info['translated_transcript_path'] = str(transcript_path)
                job_info['translated_language_code'] = detected_language

        # Generate AI-Powered Summaries and Insights
        print("Generating AI insights...")
        job_info['insights'] = {}
        
        # Generate comprehensive summary
        comprehensive_summary = generate_comprehensive_summary(transcript)
        
        # Generate short summary
        short_summary = generate_short_summary(transcript)
        
        # Extract key insights
        key_insights = extract_key_insights(transcript)
        
        # Save summary
        summary_path = SUMMARY_DIR / f"{file_id}.json"
        summary_data = {
            "comprehensive_summary": comprehensive_summary,
            "short_summary": short_summary,
            "key_insights": key_insights,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_used": OLLAMA_MODEL
        }
        
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=4, ensure_ascii=False)
        
        job_info['summary_path'] = str(summary_path)
        job_info['insights'] = summary_data

        # Mark as completed
        job_info['status'] = "completed"
        job_info['completed_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"✅ Successfully processed file: {file_id}")

    except Exception as e:
        job_info['status'] = "error"
        job_info['error_message'] = str(e)
        print(f"❌ Error processing file {file_id}: {e}")
    finally:
        # Cleanup temporary files
        try:
            if wav_path.exists():
                os.remove(wav_path)
                print(f"Cleaned up converted file: {wav_path}")
        except Exception as e:
            print(f"Warning: Error cleaning up WAV file: {e}")

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serves the main file upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def create_upload_file(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    target_language: str = Form(default="none") 
):
    """Handles audio file upload and starts a background task."""
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        print(f"✅ Saved file to disk: {file_path.name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    JOB_STATUS[file_id] = {
        "status": "processing",
        "original_filename": file.filename,
        "audio_path": str(file_path),
        "metadata": {
            "filename": file.filename,
            "size": "Calculating...",
            "duration": "Calculating...",
            "format": "Detecting...",
            "detected_language": "Detecting...",
            "target_language": target_language  # Store the target language here
        },
        "insights": {
            "comprehensive_summary": "Generating...",
            "short_summary": "Processing audio and generating insights...",
            "key_insights": []
        },
        "transcript_path": None,
        "translated_transcript_path": None,  # Add a new path for the translated file
        "summary_path": None,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
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
    # Remove local paths for security
    response_data.pop("audio_path", None)
    response_data.pop("transcript_path", None)
    response_data.pop("translated_transcript_path", None)  # Remove the new path
    response_data.pop("summary_path", None)
    
    # Add download URLs
    if job_info.get("transcript_path"):
        response_data["transcript_download_url"] = f"/download/transcript/{file_id}"
        
    if job_info.get("translated_transcript_path"):
        response_data["translated_transcript_download_url"] = f"/download/translated_transcript/{file_id}"
        
    if job_info.get("summary_path"):
        response_data["summary_download_url"] = f"/download/summary/{file_id}"
        
    return response_data

@app.get("/download/transcript/{file_id}")
async def download_transcript(file_id: str):
    """Download the transcription text file."""
    transcript_path = OUTPUT_DIR / f"{file_id}.txt"
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return FileResponse(
        transcript_path,
        media_type="text/plain",
        filename=f"transcript_{file_id}.txt"
    )

@app.get("/download/summary/{file_id}")
async def download_summary(file_id: str):
    """Download the summary JSON file."""
    summary_path = SUMMARY_DIR / f"{file_id}.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return FileResponse(
        summary_path,
        media_type="application/json",
        filename=f"summary_{file_id}.json"
    )

@app.get("/download/translated_transcript/{file_id}")
async def download_translated_transcript(file_id: str):
    """Download the translated transcription text file."""
    job_info = JOB_STATUS.get(file_id)
    if not job_info or not job_info.get("translated_transcript_path"):
        raise HTTPException(status_code=404, detail="Translated transcript not found")

    translated_path = Path(job_info["translated_transcript_path"])
    
    return FileResponse(
        translated_path,
        media_type="text/plain",
        filename=f"translated_transcript_{file_id}.txt"
    )
    
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    ollama_available = False
    ollama_models = []
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_available = True
            ollama_models = [m["name"] for m in response.json().get("models", [])]
    except:
        pass
    
    return {
        "status": "healthy",
        "whisper_loaded": WHISPER_MODEL is not None,
        "ollama_available": ollama_available,
        "ollama_models": ollama_models,
        "preferred_model": OLLAMA_MODEL,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# Main entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)