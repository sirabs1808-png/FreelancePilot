"""
Unified AI Provider Manager and Qt Background Worker Thread for FreelancePilot.
Supports Google Gemini, Groq, and local Ollama with secure Windows Keyring storage,
graceful fallbacks, and non-blocking asynchronous execution.
"""

import keyring
from typing import Dict, Any, Optional
from PySide6.QtCore import QThread, Signal

from database.db import SessionLocal
from database.models import Setting
from services.gemini_service import GeminiService
from services.groq_service import GroqService
from services.ollama_service import OllamaService

KEYRING_SERVICE = "FreelancePilot_AI"
KEY_GEMINI = "gemini_api_key"
KEY_GROQ = "groq_api_key"


class AIProviderManager:
    """
    Central manager for AI API keys, provider routing, and fallbacks.
    """

    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Retrieves API key securely from Windows Credential Manager."""
        key_name = KEY_GEMINI if provider.lower() == "gemini" else KEY_GROQ
        try:
            return keyring.get_password(KEYRING_SERVICE, key_name) or ""
        except Exception as e:
            print(f"Keyring read error: {e}")
            return ""

    @staticmethod
    def set_api_key(provider: str, api_key: str):
        """Stores API key securely into Windows Credential Manager."""
        key_name = KEY_GEMINI if provider.lower() == "gemini" else KEY_GROQ
        try:
            if api_key and api_key.strip():
                keyring.set_password(KEYRING_SERVICE, key_name, api_key.strip())
            else:
                try:
                    keyring.delete_password(KEYRING_SERVICE, key_name)
                except Exception:
                    pass
        except Exception as e:
            print(f"Keyring write error: {e}")

    @staticmethod
    def get_setting(key: str, default: str = "") -> str:
        db = SessionLocal()
        try:
            s = db.query(Setting).filter(Setting.key == key).first()
            return s.value if s and s.value else default
        finally:
            db.close()

    @staticmethod
    def set_setting(key: str, value: str):
        db = SessionLocal()
        try:
            s = db.query(Setting).filter(Setting.key == key).first()
            if s:
                s.value = value
            else:
                db.add(Setting(key=key, value=value))
            db.commit()
        finally:
            db.close()

    @staticmethod
    def generate(
        prompt: str,
        provider: str = None,
        model: str = None,
        system_instruction: str = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Executes text generation using the chosen or default provider.
        Automatically handles provider fallback if configured.
        """
        if not provider:
            provider = AIProviderManager.get_setting("default_ai_provider", "gemini")

        provider = provider.lower()
        fallback_provider = AIProviderManager.get_setting("fallback_ai_provider", "groq").lower()

        # Primary attempt
        try:
            result = AIProviderManager._dispatch(provider, prompt, model, system_instruction, temperature)
            return {
                "success": True,
                "text": result,
                "provider_used": provider,
                "model_used": model or "default",
                "fallback_used": False,
                "error": None
            }
        except Exception as primary_error:
            # Check if fallback is viable and different from primary
            if fallback_provider and fallback_provider != provider:
                try:
                    print(f"Primary provider '{provider}' failed ({primary_error}). Attempting fallback to '{fallback_provider}'...")
                    fallback_result = AIProviderManager._dispatch(fallback_provider, prompt, None, system_instruction, temperature)
                    return {
                        "success": True,
                        "text": fallback_result,
                        "provider_used": fallback_provider,
                        "model_used": "default",
                        "fallback_used": True,
                        "error": None
                    }
                except Exception as fallback_error:
                    return {
                        "success": False,
                        "text": "",
                        "provider_used": provider,
                        "model_used": model or "default",
                        "fallback_used": True,
                        "error": f"Primary ({provider}) failed: {primary_error}\nFallback ({fallback_provider}) failed: {fallback_error}"
                    }

            return {
                "success": False,
                "text": "",
                "provider_used": provider,
                "model_used": model or "default",
                "fallback_used": False,
                "error": str(primary_error)
            }

    @staticmethod
    def _dispatch(provider: str, prompt: str, model: str, system_instruction: str, temperature: float) -> str:
        provider = provider.lower()
        if "gemini" in provider:
            key = AIProviderManager.get_api_key("gemini")
            if not key:
                raise ValueError("Google Gemini API key not found in Settings.")
            return GeminiService.generate_text(
                prompt=prompt,
                api_key=key,
                model=model or "gemini-2.5-flash",
                system_instruction=system_instruction,
                temperature=temperature
            )

        elif "groq" in provider:
            key = AIProviderManager.get_api_key("groq")
            if not key:
                raise ValueError("Groq API key not found in Settings.")
            return GroqService.generate_text(
                prompt=prompt,
                api_key=key,
                model=model or "llama-3.3-70b-versatile",
                system_instruction=system_instruction,
                temperature=temperature
            )

        elif "ollama" in provider:
            host = AIProviderManager.get_setting("ollama_host", OllamaService.DEFAULT_HOST)
            return OllamaService.generate_text(
                prompt=prompt,
                model=model or "llama3.2",
                host_url=host,
                system_instruction=system_instruction,
                temperature=temperature
            )

        else:
            raise ValueError(f"Unknown AI provider: '{provider}'")


# ============================================================================
# ASYNCHRONOUS QT WORKER THREAD
# ============================================================================
class AIWorkerThread(QThread):
    """
    QThread worker to run AI generation in the background without freezing the UI.
    """
    finished_result = Signal(dict)
    failed_error = Signal(str)

    def __init__(
        self,
        prompt: str,
        provider: str = None,
        model: str = None,
        system_instruction: str = None,
        temperature: float = 0.7,
        parent=None
    ):
        super().__init__(parent)
        self.prompt = prompt
        self.provider = provider
        self.model = model
        self.system_instruction = system_instruction
        self.temperature = temperature

    def run(self):
        try:
            result = AIProviderManager.generate(
                prompt=self.prompt,
                provider=self.provider,
                model=self.model,
                system_instruction=self.system_instruction,
                temperature=self.temperature
            )
            if result["success"]:
                self.finished_result.emit(result)
            else:
                self.failed_error.emit(result["error"])
        except Exception as e:
            self.failed_error.emit(str(e))
