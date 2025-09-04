FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    git \
    gcc \
    g++ \
    make \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and core build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with higher timeout and retries
RUN pip install --no-cache-dir --timeout=120 --retries=5 -r requirements.txt -i https://pypi.org/simple

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs summaries static/css static/js templates

# Expose the port
EXPOSE 8001

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

