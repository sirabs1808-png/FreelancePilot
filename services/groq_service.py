"""
Groq API integration service for FreelancePilot.
Supports ultra-fast inference on free developer tier models: LLaMA 3.3, Mixtral, Gemma.
"""

from typing import Tuple, List


class GroqService:
    DEFAULT_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    @staticmethod
    def test_connection(api_key: str) -> Tuple[bool, str]:
        """Tests the Groq API connection."""
        if not api_key or not api_key.strip():
            return False, "Groq API key is empty. Please enter your key from console.groq.com."

        try:
            from groq import Groq
            client = Groq(api_key=api_key.strip())
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": "Ping. Respond with 'Pong' only."}],
                model="llama-3.1-8b-instant",
                max_tokens=10
            )
            if completion and completion.choices:
                reply = completion.choices[0].message.content.strip()
                return True, f"Groq connection successful! (Model responded: {reply})"
            return False, "No response choices returned by Groq."
        except Exception as e:
            err_msg = str(e)
            if "invalid_api_key" in err_msg or "401" in err_msg:
                return False, "Invalid Groq API key. Check console.groq.com credentials."
            elif "rate_limit_exceeded" in err_msg or "429" in err_msg:
                return False, "Groq free rate limit reached. Please wait a minute or use Gemini/Ollama."
            return False, f"Groq connection failed: {err_msg}"

    @staticmethod
    def generate_text(
        prompt: str,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        system_instruction: str = None,
        temperature: float = 0.7
    ) -> str:
        """Generates text using Groq."""
        if not api_key or not api_key.strip():
            raise ValueError("Groq API key not configured. Please add it in Settings.")

        from groq import Groq
        client = Groq(api_key=api_key.strip())

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model=model or "llama-3.3-70b-versatile",
            messages=messages,
            temperature=temperature
        )

        if not completion.choices or not completion.choices[0].message.content:
            raise RuntimeError("Groq returned an empty response.")

        return completion.choices[0].message.content.strip()
