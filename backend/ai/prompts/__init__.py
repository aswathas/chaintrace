"""Prompt templates. Returns (system, user) tuples."""
from backend.ai.prompts.trace_report import render_trace_report
from backend.ai.prompts.profile_summary import render_profile_summary
from backend.ai.prompts.cluster_explanation import render_cluster_explanation


def get_prompt_template(kind: str, context: dict) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the given kind."""
    if kind == "trace":
        return render_trace_report(context)
    elif kind == "profile":
        return render_profile_summary(context)
    elif kind == "cluster":
        return render_cluster_explanation(context)
    else:
        raise ValueError(f"Unknown prompt kind: {kind}")
