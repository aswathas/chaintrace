"""AI layer for report generation. Pluggable provider abstraction."""
import re
from backend.ai.providers import get_ai_provider
from backend.ai.prompts import get_prompt_template


async def generate_report(kind: str, context: dict) -> str:
    """Generate an AI-formatted report for the given context kind (trace|profile|cluster)."""
    provider = get_ai_provider()
    system, user = get_prompt_template(kind, context)

    try:
        # Generate prose
        prose = await provider.generate(user, system, context)

        # Post-check: verify all addresses and values mentioned are in context
        if _post_check_passes(prose, context):
            return prose

        # First retry
        prose = await provider.generate(user, system, context)
        if _post_check_passes(prose, context):
            return prose

        # Second failure: fall back to templated report
        return _templated_fallback(kind, context)
    except Exception as e:
        # Provider error: return templated
        return _templated_fallback(kind, context)


def _post_check_passes(prose: str, context: dict) -> bool:
    """Verify every 0x-address and dollar value in prose appears in JSON context."""
    # Extract all 0x-addresses from prose
    prose_addresses = set(re.findall(r'0x[a-fA-F0-9]{40}', prose))
    # Extract all addresses from context (recursively)
    context_str = str(context).lower()
    context_addresses = set(re.findall(r'0x[a-fA-F0-9]{40}', context_str))

    # Every prose address must be in context
    for addr in prose_addresses:
        if addr.lower() not in context_addresses:
            return False

    # Extract dollar values from prose (e.g., $123.45, $1M, $50k)
    prose_values = set(re.findall(r'\$[\d,.MKB]+', prose))
    context_str = str(context)
    for val in prose_values:
        # Loose check: at least the base number appears
        num = re.sub(r'[^\d.]', '', val)
        if num and num not in context_str:
            return False

    return True


def _templated_fallback(kind: str, context: dict) -> str:
    """Return a minimal templated report when LLM fails."""
    if kind == "trace":
        terminals = context.get("terminals", [])
        return f"Trace found {len(terminals)} terminal(s). See data for details."
    elif kind == "profile":
        risk_score = context.get("risk_score", "unknown")
        return f"Risk profile: {risk_score}. See data for details."
    elif kind == "cluster":
        size = context.get("cluster_size", 0)
        return f"Cluster of {size} wallets linked by heuristics. See data for details."
    else:
        return "Report generation failed. See structured data."
