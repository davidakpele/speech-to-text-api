# Audio Analysis API with Whisper, Translation & AI-Powered Insights

A FastAPI application that transcribes audio files using OpenAI's Whisper model, translates content, and generates comprehensive AI-powered insights using locally-running Ollama models.

## 🎯 Project Goal

The primary goal of this project is to create a robust and user-friendly web service that can process audio files with advanced capabilities. It achieves this by performing several key tasks:

1. **Transcription:** Converting spoken words from audio files into accurate text transcripts.
2. **Language Detection:** Automatically identifying the language spoken in the audio.
3. **Translation:** Converting transcripts to different languages as requested.
4. **Metadata Extraction:** Pulling crucial information about audio files (duration, size, format).
5. **AI-Powered Analysis:** Generating comprehensive summaries, key insights, and detailed analysis using locally-hosted language models.

> This application offers a complete solution for users who need to process, understand, and translate audio content without relying on external cloud-based services.

## ✨ Key Features

- **Multi-format Audio Support**: Process MP3, WAV, FLAC, and other common audio formats
- **Automatic Language Detection**: Identifies the language spoken in audio files
- **Translation Capabilities**: Convert transcripts to multiple languages (English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Russian, Arabic, Hindi)
- **Comprehensive Metadata Extraction**: File size, duration, format, and technical details
- **AI-Powered Insights**: 
  - Short summaries for quick overviews
  - Detailed comprehensive analysis
  - Key insights extraction
  - Topic identification and sentiment analysis
- **Real-time Processing Status**: Live updates on transcription and analysis progress
- **Downloadable Results**: Export transcripts, translations, and analysis in various formats

## ⚙️ Implementation & Architecture

The application is built on a modern, asynchronous architecture to handle multiple file processing efficiently:

1. **Frontend (HTML/CSS/JS)**: A responsive user interface for uploading files and viewing results with real-time status updates.

2. **Backend (FastAPI)**: High-performance Python core handling file uploads, background tasks, and API endpoints.

3. **Background Processing**: Non-blocking processing of audio files using Starlette BackgroundTasks.

4. **AI Integration**:
   - **Whisper**: For accurate speech-to-text transcription and language detection
   - **Ollama**: For running large language models locally to generate insights and translations

5. **Audio Processing**: FFmpeg for format conversion and audio manipulation.

## 📦 Packages & AI Models Used

| Package / Tool       | Purpose |
|----------------------|---------|
| FastAPI | Web framework for building API endpoints |
| python-multipart | Handling file uploads (form-data) |
| python-magic | MIME type detection for uploaded files |
| uvicorn | ASGI server to run the FastAPI application |
| openai-whisper | AI model for high-quality audio transcription |
| ollama | Running large language models locally |
| ffmpeg | Audio processing and format conversion |
| requests | HTTP calls to the local Ollama API |

### Recommended AI Models

For optimal performance, we recommend these Ollama models:
- **Llama 3** (8B): Best balance of performance and accuracy
- **Gemma** (7B): Excellent for summarization tasks
- **Mistral** (7B): Strong all-around performer
- **Phi-3** (3.8B): Good for lower-resource systems

## 🚀 Setup & Running the Application

### Step 1: Install Prerequisites

You must have Python 3.8+ and FFmpeg installed on your system.

**FFmpeg Installation:**
- **Windows**: Download from [official FFmpeg website](https://ffmpeg.org/) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux (Debian/Ubuntu)**: `sudo apt install ffmpeg`
- **Linux (Fedora/CentOS)**: `sudo yum install ffmpeg`

### Step 2: Set up Ollama

1. Download and install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull a language model:
```bash
ollama pull llama3
# or
ollama pull gemma
# or
ollama pull mistral
# Currently using this below
ollama run finalend/hermes-3-llama-3.1:8b
```
### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```
### Step 4: Run the Application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

```
- The application will be accessible at http://localhost:8000.
### 📖 Usage Guide
- Web Interface
   - Open your browser and navigate to http://localhost:8000
   - Upload an audio file using the form
   - Select a target language for translation 
   - View real-time processing status
   - Access results including:
      - File metadata (size, duration, format, detected language)
      - AI-generated short summary
      - Key insights extracted from content
      - Comprehensive analysis with topic, participants, and sentiment
      - Original and translated transcripts (if requested)

### API Endpoints
- **GET /** - Main upload interface
- **POST /upload** - Upload audio file for processing
- **GET /status/{file_id}** - Check processing status
- **GET /api/status/{file_id}** - JSON API for status checking
- **GET /download/transcript/{file_id}** - Download original transcript
- **GET /download/translated_transcript/{file_id}** - Download translated transcript
- **GET /download/summary/{file_id}** - Download comprehensive analysis JSON
- **GET /health** - System health check

### Translation Support
- The application supports translation to these languages:
- English **(en)**
- Spanish **(es)**
- French **(fr)**
- German **(de)**
- Italian **(it)**
- Portuguese **(pt)**
- Chinese **(zh)**
- Japanese **(ja)**
- Korean **(ko)**
- Russian **(ru)**
- Arabic **(ar)**
- Hindi **(hi)**

> You can specify either the language name ("spanish") or code ("es").
### 🔧 Configuration
- Key configuration options in main.py:
    - UPLOAD_DIR, OUTPUT_DIR, SUMMARY_DIR: Storage directories
    - WHISPER_MODEL: Whisper model size ("tiny", "base", "small", "medium", "large")
    - OLLAMA_MODEL: Default model for summarization and translation
    - LANGUAGE_MAP: Mapping between language names and codes

### 🛠️ Development
- Project Structure

```bash
.
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── uploads/            # Uploaded audio files
├── outputs/            # Transcription results
├── summaries/          # AI analysis results
├── static/             # CSS, JS, and other static files
└── templates/          # HTML templates
```

### Adding New Features
- New AI Models: Update the OLLAMA_MODEL variable and fallback models list
- Additional Languages: Extend the LANGUAGE_MAP dictionary
- New Analysis Types: Modify the prompt templates in the summary generation functions

### 📄 License
- This project is open source and available under the MIT License.

### 🤝 Contributing
- Contributions, issues, and feature requests are welcome! Feel free to check the issues pag