"""Classify a destination address as a known terminal type."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Hardcoded address registries
# ---------------------------------------------------------------------------

# Tornado Cash pool contracts — Ethereum mainnet
TORNADO_POOLS: dict[str, float] = {
    # 0.1 ETH pools
    "0x12d66f87a04a9e220c9d9bf7bc4ecf3a92c6b4b": 0.1,
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": 0.1,
    # 1 ETH pools
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": 1.0,
    "0xa160cdab225685da1d56aa342ad8841c3b53f291": 1.0,
    # 10 ETH pools
    "0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3": 10.0,
    "0xfd8610d20aa15b7b2e3be39b396a1bc3516c7144": 10.0,
    # 100 ETH pools
    "0x07687e702b410fa43f4cb4af7fa097918ffd2730": 100.0,
    "0x23773e65ed146a459667dd6e2af2b2a69cd0d796": 100.0,
    # DAI pools
    "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d": 100.0,
    "0xd96f2b1c14db8458374d9aca76e26c3950113464": 1000.0,
}

# Major bridge contracts (Ethereum mainnet unless noted)
BRIDGE_CONTRACTS: dict[str, str] = {
    # Stargate Finance
    "0x8731d54e9d02c286767d56ac03e8037c07e01e98": "stargate",
    "0x296f55f8fb28e498b858d0bcda06d955b2cb3f97": "stargate",
    # Wormhole Token Bridge
    "0x3ee18b2214aff97000d974cf647e7c347e8fa585": "wormhole",
    "0x98f3c9e6e3face36baad05fe09d375ef1464288b": "wormhole",
    # LayerZero endpoints
    "0x66a71dcef29a0ffbdbe3c6a460a3b5bc225cd675": "layerzero",
    "0x3c2269811836af69497e5f486a85d7316753cf62": "layerzero",
    # Synapse Protocol
    "0x2796317b0ff8538f253012862c06787adfb8ceb6": "synapse",
    "0x6571d6be3d8460cf5f7d6711cd9961860029d85f": "synapse",
    # Across Protocol
    "0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5": "across",
    "0x4d9079bb4165aeb4084c526a32695dcfd2f77381": "across",
    # Hop Protocol
    "0xb8901acb165ed027e32754e0ffe830802919727f": "hop",
    "0x3666f603cc164936c1b87e207f36beba4ac5f18a": "hop",
    "0x22b1cbb8d98a01a3b71d034bb899775a76eb1cc2": "hop",
    # Arbitrum canonical bridge
    "0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a": "arbitrum_bridge",
    # Optimism canonical bridge
    "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1": "optimism_bridge",
    # Polygon PoS bridge
    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": "polygon_bridge",
    # Base canonical bridge
    "0x49048044d57e1c92a77f79988d21fa8faf74e97e": "base_bridge",
}

# Known CEX hot wallets — top-5 per exchange (Ethereum mainnet)
CEX_HOT_WALLETS: dict[str, str] = {
    # Binance
    "0x28c6c06298d514db089934071355e5743bf21d60": "binance",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "binance",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "binance",
    "0xb38e8c17e38363af6ebdcb3dae12e0243582891d": "binance",
    "0xf977814e90da44bfa03b6295a0616a897441acec": "binance",
    # Coinbase
    "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43": "coinbase",
    "0x77696bb39917c91a0c3908d577d5e322095425ca": "coinbase",
    "0x503828976d22510aad0201ac7ec88293211d23da": "coinbase",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "coinbase",
    "0x95a9bd206ae52c4ba8eecfc93d18ebc2af8af0b6": "coinbase",
    # Kraken
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "kraken",
    "0xae2d4617c862309a3d75a0ffb358c7a5009c673f": "kraken",
    "0x43984d578803891dfa9706bdeee6078d80cfc79e": "kraken",
    "0x66c57bf505a85a74609d2c83e7f8b4664d5b4832": "kraken",
    "0xda9dfa130df4de4673b89022ee50ff26f6ea73cf": "kraken",
    # Bitfinex
    "0x742d35cc6634c0532925a3b844bc454e4438f44e": "bitfinex",
    "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa": "bitfinex",
    "0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98": "bitfinex",
    "0x77eb5b25b02e7281b2ea46eeb7af300e4c7b6e9b": "bitfinex",
    "0x1151314c646ce4e0efd76d1af4760ae66a9fe30f": "bitfinex",
    # OKX
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "okx",
    "0x98ec059dc3adfbdd63429454aeb0c990fba4a128": "okx",
    "0x236f9f97e0e62388479bf9e5ba4889e46b0273c3": "okx",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "okx",
    "0x5041ed759dd4afc3a72b8192c143f72f4724081e": "okx",
    # Bybit
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "bybit",
    "0xe79eef9b9388a4ff70ed7ec5bccd5b928ebb2bd1": "bybit",
    "0x0639556f03714a74a5fecab7be0ef0113e908cee": "bybit",
    "0x931b8f17764362a3f1f2b01b26e0d8bf3f5bf3d7": "bybit",
    "0x5d22045daceab03b158031ecb7d9d06fad24609b": "bybit",
}

# Known exploit wallets (addresses that received stolen funds)
EXPLOIT_WALLETS: dict[str, str] = {
    # Ronin / Axie Infinity hack 2022 (~$625M)
    "0x098b716b8aaf21512996dc57eb0615e2383e2f96": "ronin_hack_2022",
    "0xa16081f360e3847006db660bae1c6d1b2e17ec2a": "ronin_hack_2022",
    # Harmony Horizon bridge hack 2022 (~$100M)
    "0x0d043128146654c7683fbf30ac98d7b2285ded00": "harmony_hack_2022",
    "0x58f56615180a8eea4c462235d9e215f72484b4a3": "harmony_hack_2022",
    # Nomad bridge hack 2022 (~$190M)
    "0xb5d1f10c8d9716f4cbc71f39c4f83fada9aa0a11": "nomad_hack_2022",
    # Wormhole hack 2022 (~$320M)
    "0x629e7da20197a5429d30da36e77d06cdf796b71a": "wormhole_hack_2022",
}

TORNADO_DENOMINATIONS = [0.1, 1.0, 10.0, 100.0]

COLD_STORAGE_INACTIVE_DAYS = 180


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class Terminal:
    kind: str          # "cex" | "mixer" | "bridge" | "cold_storage"
    label: str         # human-readable name
    address: str
    denomination: Optional[float] = None  # for mixer


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def classify_terminal(address: str, labels: dict[str, str] | None = None) -> Optional[Terminal]:
    """Return a Terminal if address is a known CEX, mixer, bridge, or cold-storage; else None."""
    addr_lower = address.lower()

    if addr_lower in TORNADO_POOLS:
        denom = TORNADO_POOLS[addr_lower]
        return Terminal(kind="mixer", label=f"tornado_cash_{denom}eth", address=addr_lower, denomination=denom)

    if addr_lower in BRIDGE_CONTRACTS:
        return Terminal(kind="bridge", label=BRIDGE_CONTRACTS[addr_lower], address=addr_lower)

    if addr_lower in CEX_HOT_WALLETS:
        return Terminal(kind="cex", label=CEX_HOT_WALLETS[addr_lower], address=addr_lower)

    if addr_lower in EXPLOIT_WALLETS:
        # Exploit wallets aren't terminals in the traversal sense — caller decides
        return None

    # Check caller-supplied label map (populated by the labeler pipeline)
    if labels:
        lbl = labels.get(addr_lower) or labels.get(address)
        if lbl:
            if "cex" in lbl or any(ex in lbl for ex in ("binance", "coinbase", "kraken", "bitfinex", "okx", "bybit")):
                return Terminal(kind="cex", label=lbl, address=addr_lower)
            if "tornado" in lbl or "mixer" in lbl:
                return Terminal(kind="mixer", label=lbl, address=addr_lower)
            if "bridge" in lbl:
                return Terminal(kind="bridge", label=lbl, address=addr_lower)

    return None


def is_cold_storage(address: str, last_outflow_ts: Optional[datetime], balance_usd: float) -> bool:
    """Heuristic: no outflows in 180 days and non-trivial balance."""
    if last_outflow_ts is None:
        return balance_usd > 0
    days_inactive = (datetime.now(timezone.utc) - last_outflow_ts).days
    return days_inactive >= COLD_STORAGE_INACTIVE_DAYS and balance_usd > 0
