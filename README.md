# Speech-to-Text API with Whisper, Metadata, and AI-Powered Abstracts

- A FastAPI application that transcribes audio files using OpenAI's Whisper model and generates AI-powered insights using a locally-running Ollama Large Language Model.
## 🎯 Project Goal
- The primary goal of this project is to create a robust and user-friendly web service that can process audio files. It achieves this by performing three key tasks:
1. **Transcription:** Converting spoken words from an audio file into a text document.
2. **Metadata Extraction:** Automatically pulling crucial information about the audio file, such as its duration, size, and format.
3. **AI-Powered Summarization:** Generating concise summaries, key points, and a descriptive title for the transcribed text using a powerful, locally-hosted language model.

> This application offers a comprehensive solution for users who need to quickly process and understand the content of audio recordings without relying on external, cloud-based AI services.

## ⚙️ Implementation & Architecture
- The application is built on a modern, asynchronous architecture to handle multiple file uploads efficiently.
1. **Frontend (HTML/CSS/JS):** A simple, responsive user interface is provided to allow users to upload audio files. It uses JavaScript to poll a backend API endpoint for real-time updates on the processing status, creating a dynamic and engaging experience.

2. **Backend (FastAPI):** Written in Python, FastAPI serves as the high-performance core of the application. It handles file uploads, manages background tasks, and provides the API endpoints for status checks and data retrieval. It's chosen for its speed and native support for asynchronous programming.

3. **Background Processing (Starlette BackgroundTasks):** To prevent the web server from being blocked by long-running transcription jobs, each file is processed as a background task. This allows the server to immediately return a status page to the user while the heavy lifting happens in the background.

4. **Local AI Integration (Ollama):** Instead of using a paid cloud API, the application integrates with Ollama, a powerful tool that runs large language models (LLMs) locally on your system. This makes the service private and cost-effective. The LLM is given a structured prompt to generate a comprehensive summary, including key points, action items, and context.

## 📦 Packages & AI Models Used
> This project relies on several key Python libraries and external tools to function. All Python packages can be installed from the requirements.txt file.

| Package / Tool       | Purpose              |
|----------------------|----------------------|
| FastAPI	           | The web framework for building the API endpoints.                 |
| python-multipart     | Required by FastAPI to handle file uploads (form-data).                |
| python-magic         | Detects the MIME type of uploaded files for accurate metadata.                |
| uvicorn              | An ASGI server to run the FastAPI application.                |
| openai-whisper       | The core AI model for high-quality audio transcription.                |
| ollama               | External software for running large language models locally. We use it to host models like openllama3b.bin or llama3 for summarization.               |
| ffmpeg       | An essential command-line tool for audio processing. It's used to convert any uploaded audio format to a standard WAV format that the Whisper model can process reliably.                |
| requests       | Used to make HTTP calls to the local Ollama API to request summaries..                |

## 🚀 Setup & Running the Application
- Follow these steps to get the application running on your local machine.
**Step 1:** Install Prerequisites
  > You must have Python 3.8+ and FFmpeg installed on your system.
  - FFmpeg Installation:
     - Windows: Download the executable from the official FFmpeg website and add it to your system's PATH.
     - macOS: Install via Homebrew: brew install ffmpeg
     - Linux: Install via package manager: sudo apt install ffmpeg (Debian/Ubuntu) or sudo yum install ffmpeg (Fedora/CentOS).
**Step 2:**  Set up Ollama
- Download and install Ollama from its official website. The application will run as a service on your machine, accessible at http://localhost:11434.
- Pull a language model to run locally. The code is configured to look for openllama3b.bin, but you can use llama3 or another small, fast model.

```bash
ollama pull openllama3b.bin
````
- If you choose a different model, update the OLLAMA_MODEL variable in main.py.

**Step 3:** Install Python Dependencies
- Clone or download this repository.
- Navigate to the project directory in your terminal.
- Install all required Python packages using the provided requirements.txt file.

```bash
 pip install -r requirements.txt
````
**Step 4:** Run the Application
- From the project's root directory, start the server using Uvicorn. The --reload flag is useful during development as it automatically restarts the server when you make changes.

```bash
 uvicorn main:app --host 127.0.0.1 --port 8000 --reload
````
- The application will be accessible in your web browser at http://127.0.0.1:8000.

**Step 5:**  Using the API
- Open a browser and navigate to http://127.0.0.1:8000.
   - Upload an audio file.
   - You will be redirected to a status page that shows the live progress of the transcription and summarization.
   - Once completed, you can view the full transcript and the AI-generated insights directly on the page.

  
## Features

- Audio file upload (MP3, WAV, FLAC, etc.)
- Automatic language detection (English and Spanish)
- Audio metadata extraction (duration, format, size, etc.)
- Transcription using Whisper
- AI-generated summaries and key information extraction using Ollama
- Real-time processing status updates
- Downloadable transcripts

## Prerequisites

- Python 3.8+
- FFmpeg (for audio processing)
- Ollama (for AI summaries)

