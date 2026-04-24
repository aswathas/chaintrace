"""Hardcoded high-confidence address labels — source 1 of the label pipeline."""
from __future__ import annotations

# Re-use canonical registries from the tracer to avoid duplication
from ..tracer.terminals import (
    TORNADO_POOLS,
    BRIDGE_CONTRACTS,
    CEX_HOT_WALLETS,
    EXPLOIT_WALLETS,
)

# DEX router addresses (Ethereum mainnet unless noted)
DEX_ROUTERS: dict[str, str] = {
    # Uniswap v2
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "uniswap_v2_router",
    # Uniswap v3
    "0xe592427a0aece92de3edee1f18e0157c05861564": "uniswap_v3_router",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "uniswap_v3_router2",
    # Uniswap Universal Router
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b": "uniswap_universal_router",
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "uniswap_universal_router2",
    # SushiSwap
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "sushiswap_router",
    # 1inch v5 aggregation router
    "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch_v5_router",
    # 1inch v4
    "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch_v4_router",
    # 0x Exchange Proxy
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff": "0x_exchange_proxy",
    # Curve Router
    "0xf18056bbd320e96a48e3fbf8bc061322531aac99": "curve_router",
    # Balancer Vault
    "0xba12222222228d8ba445958a75a0704d566bf2c8": "balancer_vault",
    # Paraswap
    "0xdef171fe48cf0115b1d80b88dc8eab59176fee57": "paraswap_v5",
}

# Known exploit wallet → incident mapping
# (a subset of EXPLOIT_WALLETS from terminals.py with richer metadata)
EXPLOIT_REGISTRY: dict[str, dict] = {
    "0x098b716b8aaf21512996dc57eb0615e2383e2f96": {
        "label": "ronin_hack_2022",
        "incident": "Ronin Bridge Hack",
        "date": "2022-03-23",
        "stolen_usd": 625_000_000,
    },
    "0x0d043128146654c7683fbf30ac98d7b2285ded00": {
        "label": "harmony_hack_2022",
        "incident": "Harmony Horizon Bridge Hack",
        "date": "2022-06-23",
        "stolen_usd": 100_000_000,
    },
    "0xb5d1f10c8d9716f4cbc71f39c4f83fada9aa0a11": {
        "label": "nomad_hack_2022",
        "incident": "Nomad Bridge Hack",
        "date": "2022-08-01",
        "stolen_usd": 190_000_000,
    },
    "0x629e7da20197a5429d30da36e77d06cdf796b71a": {
        "label": "wormhole_hack_2022",
        "incident": "Wormhole Bridge Hack",
        "date": "2022-02-02",
        "stolen_usd": 320_000_000,
    },
}

# Build unified lookup: lowercase address → label string
HARDCODED_LABELS: dict[str, str] = {}

for addr, denom in TORNADO_POOLS.items():
    HARDCODED_LABELS[addr.lower()] = f"tornado_cash_{denom}eth"

for addr, name in BRIDGE_CONTRACTS.items():
    HARDCODED_LABELS[addr.lower()] = name

for addr, exchange in CEX_HOT_WALLETS.items():
    HARDCODED_LABELS[addr.lower()] = exchange

for addr, info in EXPLOIT_REGISTRY.items():
    HARDCODED_LABELS[addr.lower()] = info["label"]

for addr, name in DEX_ROUTERS.items():
    HARDCODED_LABELS[addr.lower()] = name
