"""Profile summary prompt template."""
import json


PROFILE_SUMMARY_SYSTEM = """You are a blockchain forensics analyst. Generate a 3-paragraph wallet risk profile from structured analysis.

GUARDRAILS:
- Do not speculate beyond provided JSON.
- Do not fabricate addresses or values.
- Every 0x-address and dollar amount you mention MUST appear in the JSON context.
- Paragraph 1: Risk level and key signals. Paragraph 2: Counterparty analysis. Paragraph 3: Behavioral summary.
"""


def render_profile_summary(profile_json: dict) -> tuple[str, str]:
    """Render a profile summary prompt pair."""
    user_prompt = f"""Generate a risk profile summary from this analysis:

{json.dumps(profile_json, indent=2)}

Cover:
1. Overall risk level (low/medium/high/critical) with key signals.
2. Counterparty relationships and associated risks.
3. Behavioral patterns and transaction characteristics."""

    return PROFILE_SUMMARY_SYSTEM, user_prompt
