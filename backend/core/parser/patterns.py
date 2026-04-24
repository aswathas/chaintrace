"""Exploit pattern matchers — reentrancy, flash-loan drain, approval-drain."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Flash-loan initiator selectors (from abi.py KNOWN_SELECTORS)
FLASH_LOAN_SELECTORS = {
    "ab9c4b5d",  # Aave v2/v3 flashLoan
    "1b11d0ef",  # Aave flashLoanSimple
    "1cff79cd",  # DyDx operate
    "5c38449e",  # Balancer flashLoan
}

# ERC-20 transfer/approve selectors
TRANSFER_SELECTOR = "a9059cbb"
TRANSFER_FROM_SELECTOR = "23b872dd"
APPROVE_SELECTOR = "095ea7b3"


@dataclass
class PatternMatch:
    name: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    unconfirmed: bool = False


def _detect_reentrancy(trace_calls: list[dict[str, Any]]) -> PatternMatch | None:
    """Reentrancy: a contract calls the same target recursively within one tx.

    trace_calls: list of {from, to, value, selector, depth} from a debug_traceTransaction.
    """
    # Build call signature: (from, to, selector) at each depth
    # Reentrancy = same (caller, callee) pair appearing at depth n and depth n+2+ in same stack
    call_stack: list[tuple[str, str, str]] = []
    seen_at_depth: dict[int, tuple[str, str, str]] = {}
    evidence: list[str] = []

    for call in trace_calls:
        depth = call.get("depth", 0)
        caller = call.get("from", "").lower()
        callee = call.get("to", "").lower()
        selector = call.get("selector", "")
        frame = (caller, callee, selector)

        # Check if the same (caller, callee) appears at a lower depth (recursive)
        for prev_depth, prev_frame in seen_at_depth.items():
            if prev_depth < depth and prev_frame[:2] == frame[:2]:
                evidence.append(
                    f"recursive call: {caller} → {callee} at depth {prev_depth} and {depth}"
                )

        seen_at_depth[depth] = frame

    if evidence:
        # Confidence scales with recursion depth
        confidence = min(0.95, 0.6 + len(evidence) * 0.1)
        return PatternMatch(name="reentrancy", confidence=round(confidence, 3), evidence=evidence)
    return None


def _detect_flash_loan_drain(
    trace_calls: list[dict[str, Any]],
    tx_value_usd: float = 0.0,
) -> PatternMatch | None:
    """Flash-loan + large drain: flash-loan selector followed by significant outflows."""
    has_flash = False
    flash_provider = ""
    drain_calls: list[dict] = []
    evidence: list[str] = []

    for call in trace_calls:
        selector = call.get("selector", "")
        callee = call.get("to", "").lower()

        if selector in FLASH_LOAN_SELECTORS:
            has_flash = True
            flash_provider = callee
            evidence.append(f"flash-loan initiated via {callee} (selector {selector})")
            continue

        if has_flash and selector in (TRANSFER_FROM_SELECTOR, TRANSFER_SELECTOR):
            value_usd = call.get("value_usd", 0)
            if value_usd > 10_000:  # drain threshold: >$10k
                drain_calls.append(call)
                evidence.append(
                    f"large transfer after flash-loan: {value_usd:,.0f} USD from {callee}"
                )

    if has_flash and drain_calls:
        total_drained = sum(c.get("value_usd", 0) for c in drain_calls)
        confidence = 0.75 if total_drained > 100_000 else 0.60
        return PatternMatch(
            name="flash_loan_drain",
            confidence=confidence,
            evidence=evidence,
        )
    return None


def _detect_approval_drain(
    events: list[dict[str, Any]],
    window_seconds: int = 3600,
) -> PatternMatch | None:
    """Approval-drain: approve(attacker, maxUint256) followed by transferFrom within 1h.

    events: list of {name, args, timestamp, block} — decoded ERC-20 events.
    """
    MAX_UINT256 = 2**256 - 1
    approvals: list[dict] = []
    evidence: list[str] = []

    for ev in events:
        if ev.get("name") == "Approval":
            args = ev.get("args", {})
            value = args.get("value", 0)
            if isinstance(value, int) and value >= MAX_UINT256 // 2:
                approvals.append(ev)

    if not approvals:
        return None

    transfer_from_events = [e for e in events if e.get("name") == "Transfer"]

    drains: list[dict] = []
    for approval in approvals:
        approval_ts = approval.get("timestamp", 0)
        spender = (approval.get("args") or {}).get("spender", "").lower()
        for tf in transfer_from_events:
            tf_ts = tf.get("timestamp", 0)
            tf_to = (tf.get("args") or {}).get("to", "").lower()
            if (
                0 <= (tf_ts - approval_ts) <= window_seconds
                and tf_to == spender
            ):
                drains.append(tf)
                evidence.append(
                    f"infinite approve → transferFrom by {spender} within "
                    f"{(tf_ts - approval_ts)//60}min"
                )

    if drains:
        confidence = min(0.90, 0.65 + len(drains) * 0.05)
        return PatternMatch(name="approval_drain", confidence=round(confidence, 3), evidence=evidence)
    return None


def match_exploit_patterns(
    trace_calls: list[dict[str, Any]],
    events: list[dict[str, Any]] | None = None,
    tx_value_usd: float = 0.0,
) -> list[PatternMatch]:
    """Run all exploit pattern detectors and return non-None matches."""
    matches: list[PatternMatch] = []

    r = _detect_reentrancy(trace_calls)
    if r:
        matches.append(r)

    fl = _detect_flash_loan_drain(trace_calls, tx_value_usd)
    if fl:
        matches.append(fl)

    if events:
        ad = _detect_approval_drain(events)
        if ad:
            matches.append(ad)

    return matches
