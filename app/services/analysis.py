import requests
import json
import re
import time
from typing import List, Dict, Any
from app.utils.validators import check_ollama_model_available
from app.config import settings
from app.utils.ollama_utils import ensure_ollama_model_available

class AnalysisService:
    def __init__(self):
        self.model = settings.OLLAMA_MODEL

        # Normalize OLLAMA_HOST into a usable base_url
        ollama_host = settings.OLLAMA_HOST
        if not ollama_host.startswith("http://") and not ollama_host.startswith("https://"):
            ollama_host = f"http://{ollama_host}"
        self.base_url = f"{ollama_host}/api"

        self._ensure_model_available()
    
    def _ensure_model_available(self):
        """Ensure the model is available, try to pull if not"""
        try:
            if not check_ollama_model_available(self.model):
                print(f"Model {self.model} not available, attempting to pull...")
                ensure_ollama_model_available()
        except requests.exceptions.ConnectionError:
            print("Ollama is not running. Analysis will not be available.")
    
    def _get_available_model(self):
        """Get an available model, trying fallbacks if needed"""
        try:
            if check_ollama_model_available(self.model):
                return self.model
            
            # Try fallback models
            for fallback_model in ["llama3", "phi3", "mistral", "gemma", "llama2"]:
                if check_ollama_model_available(fallback_model):
                    print(f"Using fallback model: {fallback_model}")
                    return fallback_model
            
            return None
        except requests.exceptions.ConnectionError:
            print("Ollama is not running. Cannot get available models.")
            return None
    
    def generate_comprehensive_summary(self, transcript: str) -> str:
        """Generates a comprehensive summary using Ollama with a structured prompt."""
        model = self._get_available_model()
        if not model:
            return "Error: No suitable Ollama model found. Please install at least one model."
        
        try:
            prompt = f"""
            Please analyze this transcript and provide a comprehensive summary with the following sections:
            
            1. MAIN TOPIC: A one-sentence description of the main topic
            2. KEY POINTS: 3-5 bullet points of the most important information
            3. ACTION ITEMS: Any decisions, actions, or next steps mentioned
            4. PARTICIPANTS: Key people or roles mentioned (if any)
            5. CONTEXT: Additional context about the content
            6. OVERALL SENTIMENT: The general tone or sentiment of the content
            
            Transcript:
            {transcript[:6000]}
            
            Please format your response clearly with section headers.
            """
            
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": model, 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_ctx": 4096
                    }
                },
                timeout=300 
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API: {e}")
            return f"Error: Failed to generate summary. Please ensure Ollama is running."
        except Exception as e:
            print(f"Unexpected error: {e}")
            return f"Error: Failed to generate summary."

    def generate_short_summary(self, transcript: str) -> str:
        """Generate a concise one-paragraph summary of the transcript."""
        model = self._get_available_model()
        if not model:
            return "Could not generate short summary - no model available"
        
        try:
            prompt = f"Provide a concise one-paragraph summary of the main content from this text: {transcript[:3000]}"
            
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": model, 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "max_length": 200
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API for short summary: {e}")
            return "Could not generate short summary"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "Could not generate short summary"

    def extract_key_insights(self, transcript: str) -> List[str]:
        """Extract key insights from the transcript."""
        model = self._get_available_model()
        if not model:
            return ["No AI model available for insights extraction"]
        
        try:
            prompt = f"Extract 3-5 key insights or most important points from this text. Present each as a separate bullet point:\n\n{transcript[:4000]}"
            
            response = requests.post(
                f"{self.base_url}/generate",
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
            
            insights = []
            lines = insights_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    insight = re.sub(r'^[-•*]\s*', '', line)
                    insights.append(insight)
                elif line and len(insights) < 5:
                    insights.append(line)
            
            return insights if insights else ["No specific insights could be extracted"]
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API for insights: {e}")
            return ["Failed to extract insights"]
        except Exception as e:
            print(f"Unexpected error: {e}")
            return ["Failed to extract insights"]
    
    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """Perform all analysis on a transcript and return results."""
        return {
            "comprehensive_summary": self.generate_comprehensive_summary(transcript),
            "short_summary": self.generate_short_summary(transcript),
            "key_insights": self.extract_key_insights(transcript),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_used": self.model
        }

# Create a singleton instance
analysis_service = AnalysisService()
