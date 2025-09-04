import requests
from typing import Dict
from app.config import LANGUAGE_MAP, settings

def check_ollama_model_available(model: str) -> bool:
    """Check if a model is available in Ollama."""
    ollama_host = settings.OLLAMA_HOST
    if not ollama_host.startswith("http"):
        ollama_host = f"http://{ollama_host}"
    base_url = f"{ollama_host}/api"

    try:
        response = requests.get(f"{base_url}/tags", timeout=10)
        response.raise_for_status()
        models = response.json().get("models", [])
        return any(m.get("name") == model for m in models)
    except Exception as e:
        print(f"Error checking Ollama model availability: {e}")
        return False

def extract_language_code(language_input: str) -> str:
    """Extract language code from user input, defaulting to English."""
    language_input = language_input.lower().strip()
    
    # Check if it's already a language code
    if len(language_input) == 2 and language_input in LANGUAGE_MAP.values():
        return language_input
    
    # Map language name to code & Default to English
    return LANGUAGE_MAP.get(language_input, "en")
