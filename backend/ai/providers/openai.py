"""OpenAI provider (optional)."""
from openai import OpenAI
from backend.ai.providers import AIError


class OpenAIProvider:
    """OpenAI API client."""

    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-4o-mini"

    async def generate(self, user_prompt: str, system_prompt: str, json_context: dict) -> str:
        """Call OpenAI and return prose."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise AIError(f"OpenAI API error: {e}")
