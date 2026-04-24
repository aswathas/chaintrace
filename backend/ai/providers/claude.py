"""Anthropic Claude provider (optional)."""
from anthropic import Anthropic
from backend.ai.providers import AIError


class ClaudeProvider:
    """Claude API via Anthropic SDK."""

    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-sonnet-4-6"

    async def generate(self, user_prompt: str, system_prompt: str, json_context: dict) -> str:
        """Call Claude and return prose."""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text
        except Exception as e:
            raise AIError(f"Claude API error: {e}")
