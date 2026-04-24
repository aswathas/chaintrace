"""Smoke tests for prompt templates."""
import pytest


def test_trace_report_prompt():
    """Verify trace_report prompt returns (system, user) and includes guardrail."""
    from backend.ai.prompts.trace_report import render_trace_report

    context = {
        "seed": "0x123...",
        "hops": [
            {"from": "0x123...", "to": "0x456...", "value": 100},
        ],
        "terminals": [],
    }
    system, user = render_trace_report(context)

    assert isinstance(system, str)
    assert isinstance(user, str)
    assert "Do not speculate" in system or "Do not fabricate" in system


def test_profile_summary_prompt():
    """Verify profile_summary prompt returns (system, user) and includes guardrail."""
    from backend.ai.prompts.profile_summary import render_profile_summary

    context = {
        "address": "0x789...",
        "risk_score": 65,
        "counterparties": [],
    }
    system, user = render_profile_summary(context)

    assert isinstance(system, str)
    assert isinstance(user, str)
    assert "Do not speculate" in system or "Do not fabricate" in system


def test_cluster_explanation_prompt():
    """Verify cluster_explanation prompt returns (system, user) and includes guardrail."""
    from backend.ai.prompts.cluster_explanation import render_cluster_explanation

    context = {
        "cluster_id": "cluster-1",
        "wallets": ["0x111...", "0x222..."],
        "heuristic": "common_funder",
    }
    system, user = render_cluster_explanation(context)

    assert isinstance(system, str)
    assert isinstance(user, str)
    assert "Do not speculate" in system or "Do not fabricate" in system
