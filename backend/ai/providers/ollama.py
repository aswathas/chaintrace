"""Ollama provider (local, offline). Fallback for privacy or offline use."""
import os
import httpx
from backend.ai.providers import AIError


class OllamaProvider:
    """Ollama local inference client."""

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "gemma3:4b")

    async def generate(self, user_prompt: str, system_prompt: str, json_context: dict) -> str:
        """Call Ollama and return prose."""
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "stream": False,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
            except httpx.HTTPError as e:
                raise AIError(f"Ollama error: {e}")
            except KeyError as e:
                raise AIError(f"Unexpected Ollama response: {e}")
