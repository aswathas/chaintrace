# Profiler Module

**Location:** `backend/core/profiler/`

## Purpose

Computes a 0–100 risk score for any wallet and aggregates behavioral signals, counterparty relationships, and frequency patterns. Inputs: wallet metadata, inflows, outflows, labels. Outputs: risk score with per-signal evidence, behavior tags (airdrop farmer, MEV bot, etc.), and top counterparties.

## Public API

### `scorer.py`

**`score(wallet: dict, counterparties: list[dict], labels: dict[str, str], behavior: dict) -> RiskScore`**
Compute risk score by evaluating eight weighted signals. Returns `RiskScore` with breakdown and evidence per signal.

**`RiskScore`** (dataclass)
```python
score: int                  # 0–100 clamped
level: RiskLevel            # "low" | "medium" | "high" | "critical"
signals: list[RiskSignal]   # per-signal breakdown
```

**`RiskSignal`** (dataclass)
```python
name: str                   # signal identifier
weight: int                 # contribution to raw score
triggered: bool
evidence: str               # human-readable reason
```

**Signal weights (from spec §7.2):**
- `mixer_interaction` → +40
- `darknet_counterparty` → +35
- `exploit_wallet_interaction` → +30
- `high_velocity` → +15
- `round_amounts` → +10
- `young_wallet` → +5
- `verified_protocol` → -10
- `cex_counterparty` → -5

**Thresholds:** 0–24 low · 25–49 medium · 50–74 high · 75–100 critical.

### `summary.py`

**`summarize(wallet: dict, outflows: list[dict], inflows: list[dict], labels: dict[str, str]) -> ProfileResult`**
Aggregate wallet profile: counterparties, transaction stats, behavior tags, gas fingerprint.

**`ProfileResult`** (dataclass)
```python
address: str
chain: str
wallet_age_days: int
tx_count: int
total_inflow_usd: float
total_outflow_usd: float
top_counterparties: list[CounterpartyEntry]  # top 10 by value
behavior_tags: list[str]                     # inferred patterns
mixer_interactions: int
has_high_velocity: bool
has_round_amounts: bool
gas_fingerprint: list[float]                 # price histogram
unique_tokens: list[str]
notes: list[str]
```

**`CounterpartyEntry`** (dataclass)
```python
address: str
label: Optional[str]
total_value_usd: float
tx_count: int
direction: str              # "in" | "out" | "both"
```

**Behavior tag inference:**
- `airdrop_farmer` — ≥50 equal-amount outflows
- `mev_bot` — high velocity + low value variation + self-funded
- `binance_user` — receives from Binance hot + distributes
- `exchange_user` — any CEX inflow/outflow
- `high_frequency_trader` — high velocity (non-bot)
- `contract_deployer` — creation txs detected
- `nft_trader` — ≥5 ERC-721 transfers

### `behavior.py`

**`is_high_velocity(txs: list[dict]) -> bool`**
≥20 txs in 24h window with average gap <10 minutes.

**`has_round_amounts(txs: list[dict]) -> bool`**
≥30% of tx amounts are round USD values (heuristic for automated laundering).

**`wallet_age_days(wallet: dict) -> int`**
Days since wallet creation block timestamp.

**`gas_price_fingerprint(txs: list[dict]) -> list[float]`**
Return histogram of gas prices (5-bucket distribution) used in fingerprinting.

## Algorithm & Data Flow

```
score(wallet, counterparties, labels, behavior)
├─ evaluate each of 8 signals:
│  ├─ mixer_interaction: scan counterparty labels for "tornado" or "mixer"
│  ├─ darknet_counterparty: scan labels for "darknet" or "scam"
│  ├─ exploit_wallet_interaction: scan labels for "exploit" or "hack"
│  ├─ high_velocity: call is_high_velocity(behavior.txs)
│  ├─ round_amounts: call has_round_amounts(behavior.txs)
│  ├─ young_wallet: wallet_age_days(wallet) < 30
│  ├─ verified_protocol: check for known protocol labels (uniswap, aave, curve, compound)
│  └─ cex_counterparty: scan for CEX labels
├─ sum triggered weights
├─ clamp to [0, 100]
└─ return RiskScore with signals

summarize(wallet, outflows, inflows, labels)
├─ compute totals: total_in, total_out
├─ count mixer interactions
├─ build counterparty graph: aggregate by (src, dst) with direction
├─ extract top 10 by value
├─ infer behavior tags (airdrop_farmer, mev_bot, etc.)
├─ compute gas fingerprint histogram
└─ return ProfileResult
```

## Dependencies

**Imports:**
- `.behavior` — helper functions for pattern detection
- `..tracer.terminals` — CEX_HOT_WALLETS, TORNADO_POOLS registries

**Imported by:**
- `backend.api.routes.profile` — HTTP endpoint
- `backend.workers.profile_job` — RQ wrapper

## Extension Points

1. **New risk signals:** Add signal to `_WEIGHTS` dict and implement detection logic in `score()`.
2. **Behavior tag heuristics:** Add new pattern detector in `_infer_behavior_tags()`.
3. **Thresholds:** Adjust risk level breakpoints in `_risk_level()`.
4. **Counterparty filtering:** Change `TOP_COUNTERPARTY_COUNT` constant or add exclusion list.

## Testing Guidance

**Unit tests:**
- Mock wallet/counterparties/labels and verify score computation
- Verify each signal triggers correctly (e.g., mixer_interaction on "tornado" label)
- Verify signals below threshold don't contribute to raw score
- Verify clamping to [0, 100]
- Verify risk level categorization (low/medium/high/critical)

**Behavior detection:**
- Test `is_high_velocity()` with sparse and dense tx lists
- Test `has_round_amounts()` with integer and fractional values
- Test `wallet_age_days()` with old and young wallets

**Integration:**
- Profile known laundering wallets (should score high)
- Profile known CEX-affiliated wallets (should score low/medium with cex_counterparty reduction)
- Verify counterparty aggregation handles bidirectional edges correctly

## Known Gaps & TODOs

No explicit TODOs in scorer.py or summary.py. Implicit assumptions:
- Behavior dict must include `txs` array with standard structure
- Labels dict is pre-populated by labeler.merge
- Counterparties list pre-filtered by tracer/graph layer

## See Also

- `tracer.md` — produces counterparty maps
- `labeler.md` — supplies merged labels
- `clustering.md` — may group wallets before profiling
