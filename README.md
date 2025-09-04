# Audio Analysis API with Whisper, Translation & AI-Powered Insights

A **FastAPI** application that transcribes audio files using Whisper, translates content, and generates AI-powered insights using **locally-running Ollama models**. Built with **Docker, Redis, Celery, and Nginx** for production-ready deployment.

---

## 🎯 Project Goal

The goal of this project is to create a robust, asynchronous web service capable of:

1. **Transcribing audio** into text using Whisper.
2. **Detecting spoken language** automatically.
3. **Translating transcripts** into requested target languages.
4. **Extracting metadata**: file size, duration, format.
5. **Generating AI-powered insights**: comprehensive summaries, short summaries, key insights.
6. **Processing files asynchronously** with Celery + Redis, ensuring the UI is non-blocking.
7. **Providing RESTful APIs** and a responsive web interface.

> This application offers a complete solution for users who want to process, understand, and translate audio content **without relying on external cloud services**.

---

## ✨ Key Features

- **Multi-format Audio Support:** MP3, WAV, FLAC, etc.
- **Automatic Language Detection**
- **Translation Capabilities**: English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Russian, Arabic, Hindi.
- **Comprehensive Metadata Extraction**
- **AI Insights:**
  - Short summaries
  - Comprehensive analysis
  - Key insights
  - Topic identification & sentiment
- **Real-time Processing Status** via polling
- **Downloadable Results:** Transcripts, translations, and analysis JSON.

---

## ⚙️ Implementation & Architecture

### Modern Asynchronous Design

- **Separation of Responsibilities:**

```python
def convert_audio_to_wav()          # Audio processing
def translate_text()                # Translation
def generate_comprehensive_summary() # AI analysis
def extract_key_insights()          # Extract key insights
```

### Background Tasks Pattern (Celery + Redis)
```code
background_tasks.add_task(process_audio_file_task, job_id)
```
### RESTful API Endpoints
| Method | Endpoint                                      | Description                               |
|--------|-----------------------------------------------|-------------------------------------------|
| GET    | /jobs/{job_id}                                | Fetch job by ID                            |
| GET    | /jobs                                         | List all jobs                              |
| POST   | /upload                                       | Upload audio                               |
| GET    | /download/transcript/{job_id}                | Download original transcript               |
| GET    | /download/translated_transcript/{job_id}    | Download translated transcript             |
| GET    | /download/summary/{job_id}                   | Download comprehensive analysis JSON      |
| GET    | /health                                       | System health check                        |

### Integration of Modern Technologies
- FastAPI: High-performance Python web framework
- Whisper: Speech-to-text transcription & language detection
- Ollama: Local AI models for summarization & translation
- Tailwind CSS: Responsive modern UI
- Redis & Celery: Asynchronous job queue & caching
- Nginx: Reverse proxy and static file serving

### 🧩 Data Management
```json
{
  "status": "completed",
  "original_filename": "example.mp3",
  "audio_path": "uploads/<uuid>_example.mp3",
  "metadata": {
    "filename": "example.mp3",
    "size": "2.1 MB",
    "format": "audio/mpeg",
    "duration": "01:57",
    "detected_language": "en",
    "target_language": "none"
  },
  "insights": {
    "comprehensive_summary": "...",
    "short_summary": "...",
    "key_insights": [...]
  },
  "transcript_path": "...",
  "translated_transcript_path": "...",
  "summary_path": "...",
  "started_at": "...",
  "completed_at": "...",
  "error_message": null
}
```
> Job ID usage: Each job is stored with UUID as the Redis key.
### 🛡️ Security
- MIME type validation using python-magic.
- UUID-based filenames to prevent collisions.
- Basic file integrity checks.

### 🏗️ Project Structure
```
project/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── job.py
│   │   └── audio.py
│   ├── services/
│   │   ├── transcription.py
│   │   ├── translation.py
│   │   └── analysis.py
│   ├── api/
│   │   ├── routes/
│   │   └── dependencies.py
│   └── utils/
│       ├── redis_client.py
│       ├── file_handlers.py
│       └── validators.py
├── uploads/
├── outputs/
├── summaries/
├── static/
├── templates/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
### 🧪 Testing & Observability
- Unit Tests: Using pytest and mocks
- Integration Tests: End-to-end API validation
- Metrics & Health Checks: Optional Prometheus integration
- Structured Logging: structlog for contextual logs

### CI/CD HELP

## 🚀 Deployment & Docker Commands

- These commands provide guidance for deploying and managing the application using Docker, Docker Compose, and server services like Apache.

### Start & Build Containers
```bash
docker-compose up -d                     # Start containers in detached mode
docker-compose up --build -d             # Build and start containers
docker-compose up --build -d --remove-orphans  # Build, start, and remove orphaned containers
docker-compose build --no-cache          # Build containers without cache
```

### Stop & Clean Up Containers
```bash
docker-compose down -v                   # Stop and remove containers and volumes
docker-compose down -v --rmi all         # Stop containers, remove volumes, remove images
docker system prune -a --volumes         # Clean all unused Docker objects including volumes
docker system prune -a                    # Clean all unused Docker objects excluding volumes
docker-compose down && docker-compose up -d --build  # Rebuild and restart containers
```

### Service Management

```bash
sudo systemctl restart apache2           # Restart Apache server
docker-compose up -d db                  # Start only the database container
docker-compose ps                        # List running containers
docker-compose restart web               # Restart the web container
```

### Logs & Debugging
```bash
docker logs httpdocs-web-1               # View container logs
docker logs httpdocs-web-1 2>&1 | grep -i error  # Filter logs for errors
```
### Docker Cleanup & Inspection
```bash
docker network prune                      # Remove unused Docker networks
docker volume ls                          # List Docker volumes
docker exec -it nginx nginx -t           # Test Nginx configuration inside container
````