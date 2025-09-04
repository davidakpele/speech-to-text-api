# app/utils/ollama_utils.py
import requests
from app.config import settings

def ensure_ollama_model_available():
    """Try to pull the model if not already available."""
    ollama_host = settings.OLLAMA_HOST
    if not ollama_host.startswith("http"):
        ollama_host = f"http://{ollama_host}"
    base_url = f"{ollama_host}/api"

    try:
        response = requests.post(
            f"{base_url}/pull",
            json={"name": settings.OLLAMA_MODEL},
            timeout=600
        )
        response.raise_for_status()
        print(f"✅ Model {settings.OLLAMA_MODEL} pulled successfully (or already available).")
    except Exception as e:
        print(f"❌ Failed to pull Ollama model: {e}")
