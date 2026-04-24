"""Groq API provider (Llama 3.3 70B). Primary AI backend."""
import httpx
from backend.ai.providers import AIError
from backend.config import settings


class GroqProvider:
    """Groq API client via httpx."""

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama-3.3-70b-versatile"

    async def generate(self, user_prompt: str, system_prompt: str, json_context: dict) -> str:
        """Call Groq API and return prose."""
        if not self.api_key:
            raise AIError("GROQ_API_KEY not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1024,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                raise AIError(f"Groq API error: {e}")
            except KeyError as e:
                raise AIError(f"Unexpected Groq response: {e}")
