"""
Ollama local offline AI integration service for FreelancePilot.
Communicates with locally running Ollama instances (default http://localhost:11434)
for 100% private, offline AI text generation.
"""

import requests
from typing import Tuple, List


class OllamaService:
    DEFAULT_HOST = "http://localhost:11434"

    @staticmethod
    def test_connection(host_url: str = DEFAULT_HOST) -> Tuple[bool, str, List[str]]:
        """
        Pings Ollama and returns available local models.
        Returns: (success, message, list_of_models)
        """
        url = (host_url or OllamaService.DEFAULT_HOST).rstrip("/")
        try:
            resp = requests.get(f"{url}/api/tags", timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    return True, f"Connected to Ollama! Found {len(models)} installed model(s).", models
                else:
                    return True, "Connected to Ollama, but no models are installed yet. Run 'ollama run llama3.2' in terminal.", []
            return False, f"Ollama returned HTTP status {resp.status_code}", []
        except requests.exceptions.ConnectionError:
            return False, "Could not connect to Ollama. Ensure Ollama is installed and running on your PC (ollama serve).", []
        except Exception as e:
            return False, f"Ollama connection error: {e}", []

    @staticmethod
    def generate_text(
        prompt: str,
        model: str = "llama3.2",
        host_url: str = DEFAULT_HOST,
        system_instruction: str = None,
        temperature: float = 0.7
    ) -> str:
        """
        Sends generation request to local Ollama.
        """
        url = (host_url or OllamaService.DEFAULT_HOST).rstrip("/")
        payload = {
            "model": model or "llama3.2",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if system_instruction:
            payload["system"] = system_instruction

        try:
            resp = requests.post(f"{url}/api/generate", json=payload, timeout=120)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
            else:
                raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Ollama is not running. Start Ollama and try again.")
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama generation timed out. Try a smaller local model.")
