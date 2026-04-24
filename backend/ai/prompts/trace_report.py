"""Trace report prompt template."""
import json


TRACE_REPORT_SYSTEM = """You are a blockchain forensics analyst. Generate a concise, clear incident narrative from structured trace data.

GUARDRAILS:
- Do not speculate beyond provided JSON.
- Do not fabricate addresses or values.
- Every 0x-address and dollar amount you mention MUST appear in the JSON context.
- Write 2-3 paragraphs covering: incident origin, fund flow hops, terminal classification, and law enforcement referral (if applicable).
"""


def render_trace_report(trace_json: dict) -> tuple[str, str]:
    """Render a trace report prompt pair."""
    user_prompt = f"""Generate an incident narrative from this trace:

{json.dumps(trace_json, indent=2)}

Focus on:
1. Origin of funds (seed address).
2. Major hops and value changes.
3. Terminal classification (CEX, mixer, bridge, cold storage).
4. Any law enforcement referral points."""

    return TRACE_REPORT_SYSTEM, user_prompt
