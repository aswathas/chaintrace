"""AI provider abstraction. Factory picks best available."""
import os
from typing import Protocol

from backend.config import settings


class AIProvider(Protocol):
    """Async AI provider that generates prose from structured context."""

    async def generate(self, user_prompt: str, system_prompt: str, json_context: dict) -> str:
        """Generate prose response. user_prompt and system_prompt are strings."""
        ...


async def get_ai_provider() -> AIProvider:
    """Factory: return best available provider."""
    if settings.groq_api_key:
        from backend.ai.providers.groq import GroqProvider
        return GroqProvider()
    elif os.getenv("OLLAMA_BASE_URL"):
        from backend.ai.providers.ollama import OllamaProvider
        return OllamaProvider()
    elif os.getenv("ANTHROPIC_API_KEY"):
        from backend.ai.providers.claude import ClaudeProvider
        return ClaudeProvider()
    elif os.getenv("OPENAI_API_KEY"):
        from backend.ai.providers.openai import OpenAIProvider
        return OpenAIProvider()
    else:
        from backend.ai.providers.ollama import OllamaProvider
        return OllamaProvider()


class AIError(Exception):
    """AI provider error."""
    pass
