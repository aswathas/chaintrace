"""Cluster explanation prompt template."""
import json


CLUSTER_EXPLANATION_SYSTEM = """You are a blockchain forensics analyst. Explain why wallets are clustered based on provided heuristic evidence.

GUARDRAILS:
- Do not speculate beyond provided JSON.
- Do not fabricate addresses or values.
- Every 0x-address you mention MUST appear in the JSON context.
- Explain the heuristic (common funder / behavioral fingerprint / nonce-linked / co-spend) and confidence.
"""


def render_cluster_explanation(cluster_json: dict) -> tuple[str, str]:
    """Render a cluster explanation prompt pair."""
    user_prompt = f"""Explain why these wallets are clustered based on this evidence:

{json.dumps(cluster_json, indent=2)}

Focus on:
1. The clustering heuristic applied.
2. Specific evidence (common funders, gas price patterns, nonce links, co-spending).
3. Confidence level and caveats."""

    return CLUSTER_EXPLANATION_SYSTEM, user_prompt
