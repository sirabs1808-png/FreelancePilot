"""
Google Gemini API integration service for FreelancePilot.
Supports free-tier text generation, email drafting, proposals, and summaries.
"""

from typing import Tuple, Optional


class GeminiService:
    DEFAULT_MODELS = [
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
    ]

    @staticmethod
    def test_connection(api_key: str) -> Tuple[bool, str]:
        """Tests the Gemini API connection with a minimal prompt."""
        if not api_key or not api_key.strip():
            return False, "Gemini API key is empty. Please enter your key from Google AI Studio."

        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Ping. Respond with 'Pong' only."
            )
            if response and response.text:
                return True, f"Connection successful! (Model responded: {response.text.strip()[:30]})"
            return False, "No text returned from Gemini API."
        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "400" in err_msg:
                return False, "Invalid API key. Please check your Google AI Studio credentials."
            elif "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                return False, "Free tier rate limit reached. Please wait a minute or use Groq/Ollama."
            return False, f"Connection failed: {err_msg}"

    @staticmethod
    def generate_text(
        prompt: str,
        api_key: str,
        model: str = "gemini-2.5-flash",
        system_instruction: str = None,
        temperature: float = 0.7
    ) -> str:
        """Generates text using Google Gemini."""
        if not api_key or not api_key.strip():
            raise ValueError("Gemini API key not configured. Please add it in Settings.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key.strip())

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction if system_instruction else None
        )

        response = client.models.generate_content(
            model=model or "gemini-2.5-flash",
            contents=prompt,
            config=config
        )

        if not response or not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text.strip()
