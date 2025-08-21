# Speech-to-Text API with Whisper, Metadata, and AI-Powered Abstracts

A FastAPI application that transcribes audio files using OpenAI's Whisper model and generates AI-powered insights using Ollama.

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

## Installation

1. Clone or download this repository

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt