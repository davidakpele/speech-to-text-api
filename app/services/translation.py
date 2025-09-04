# project/app/services/translation.py
import requests
from app.utils.validators import check_ollama_model_available
from app.config import settings
from app.utils.ollama_utils import ensure_ollama_model_available


class TranslationService:
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self._ensure_model_available()
    
    def _ensure_model_available(self):
        """Ensure the model is available, try to pull if not"""
        if not check_ollama_model_available(self.model):
            print(f"Model {self.model} not available, attempting to pull...")
            ensure_ollama_model_available()
    
    def _get_available_model(self):
        """Get an available model, trying fallbacks if needed"""
        if check_ollama_model_available(self.model):
            return self.model
        
        # Try fallback models
        for fallback_model in ["llama3", "phi3", "mistral", "gemma", "llama2"]:
            if check_ollama_model_available(fallback_model):
                print(f"Using fallback model for translation: {fallback_model}")
                return fallback_model
        
        # If no models are available, try to pull the default one
        ensure_ollama_model_available()
        if check_ollama_model_available(self.model):
            return self.model
        
        return None

    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text into a target language using Ollama."""
        ollama_host = settings.OLLAMA_HOST
        if not ollama_host.startswith("http"):
            ollama_host = f"http://{ollama_host}"
        base_url = f"{ollama_host}/api"

        try:
            model_to_use = self._get_available_model()
            if not model_to_use:
                return "Error: No available model for translation."

            prompt = f"Translate the following text into {target_language}:\n\n{text}"
            
            response = requests.post(
                f"{base_url}/generate",
                json={
                    "model": model_to_use,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "max_length": 1000
                    }
                },
                timeout=300
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API for translation: {e}")
            return "Error: Failed to translate text. Please ensure Ollama is running."


# Create a singleton instance
translation_service = TranslationService()
