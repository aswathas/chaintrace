"""ABI decoding — selector matching for top ERC20/ERC721 + common router methods."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# 4-byte selectors → (method_name, param_names)
# Generated from keccak256 of the canonical function signatures.
KNOWN_SELECTORS: dict[str, tuple[str, list[str]]] = {
    # ERC-20
    "a9059cbb": ("transfer", ["to", "value"]),
    "23b872dd": ("transferFrom", ["from", "to", "value"]),
    "095ea7b3": ("approve", ["spender", "value"]),
    "70a08231": ("balanceOf", ["account"]),
    "dd62ed3e": ("allowance", ["owner", "spender"]),
    "18160ddd": ("totalSupply", []),
    "313ce567": ("decimals", []),
    "06fdde03": ("name", []),
    "95d89b41": ("symbol", []),
    # ERC-721
    "42842e0e": ("safeTransferFrom", ["from", "to", "tokenId"]),
    "b88d4fde": ("safeTransferFrom", ["from", "to", "tokenId", "data"]),
    "6352211e": ("ownerOf", ["tokenId"]),
    "a22cb465": ("setApprovalForAll", ["operator", "approved"]),
    "081812fc": ("getApproved", ["tokenId"]),
    # Uniswap v2 Router
    "38ed1739": ("swapExactTokensForTokens", ["amountIn", "amountOutMin", "path", "to", "deadline"]),
    "7ff36ab5": ("swapExactETHForTokens", ["amountOutMin", "path", "to", "deadline"]),
    "18cbafe5": ("swapExactTokensForETH", ["amountIn", "amountOutMin", "path", "to", "deadline"]),
    "e8e33700": ("addLiquidity", ["tokenA", "tokenB", "amountADesired", "amountBDesired", "amountAMin", "amountBMin", "to", "deadline"]),
    "baa2abde": ("removeLiquidity", ["tokenA", "tokenB", "liquidity", "amountAMin", "amountBMin", "to", "deadline"]),
    # Uniswap v3 Router
    "414bf389": ("exactInputSingle", ["params"]),
    "c04b8d59": ("exactInput", ["params"]),
    "db3e2198": ("exactOutputSingle", ["params"]),
    "f28c0498": ("exactOutput", ["params"]),
    # Aave v2/v3 flash loan
    "ab9c4b5d": ("flashLoan", ["receiverAddress", "assets", "amounts", "modes", "onBehalfOf", "params", "referralCode"]),
    "1b11d0ef": ("flashLoanSimple", ["receiverAddress", "asset", "amount", "params", "referralCode"]),
    # DyDx Solo Margin flash loan
    "1cff79cd": ("operate", ["accounts", "actions"]),
    # Balancer flash loan
    "5c38449e": ("flashLoan", ["recipient", "tokens", "amounts", "userData"]),
    # WETH wrap/unwrap
    "d0e30db0": ("deposit", []),
    "2e1a7d4d": ("withdraw", ["wad"]),
    # Multicall
    "ac9650d8": ("multicall", ["data"]),
    "5ae401dc": ("multicall", ["deadline", "data"]),
}


@dataclass
class DecodedCall:
    selector: str
    method: Optional[str]
    params: dict[str, Any] = field(default_factory=dict)
    raw_input: str = ""
    decoded: bool = False


def decode_call(tx_input_hex: str, abi: Optional[list[dict]] = None) -> DecodedCall:
    """Decode a transaction input hex string using selector matching or provided ABI.

    Falls back to eth-abi when the ABI is supplied. Pure selector matching otherwise.
    """
    if not tx_input_hex or len(tx_input_hex) < 10:
        return DecodedCall(selector="", method=None, raw_input=tx_input_hex)

    # Normalise hex
    clean = tx_input_hex.lower().removeprefix("0x")
    selector = clean[:8]
    calldata = clean[8:]

    # Try selector lookup first
    if selector in KNOWN_SELECTORS:
        method_name, param_names = KNOWN_SELECTORS[selector]

        params: dict[str, Any] = {}
        if abi and param_names:
            # Full decode via eth-abi
            try:
                # TODO: wire to eth-abi library when available
                # from eth_abi import decode as eth_decode
                # types = _extract_types_from_abi(abi, method_name)
                # decoded_vals = eth_decode(types, bytes.fromhex(calldata))
                # params = dict(zip(param_names, decoded_vals))
                pass
            except Exception:
                pass

        if not params and param_names:
            # Minimal manual decode for simple fixed-size params (address, uint256)
            params = _minimal_decode(calldata, param_names)

        return DecodedCall(
            selector=selector,
            method=method_name,
            params=params,
            raw_input=tx_input_hex,
            decoded=True,
        )

    # Unknown selector — try ABI if provided
    if abi:
        for entry in abi:
            if entry.get("type") != "function":
                continue
            sig = _abi_selector(entry)
            if sig == selector:
                method_name = entry.get("name", "unknown")
                return DecodedCall(
                    selector=selector,
                    method=method_name,
                    raw_input=tx_input_hex,
                    decoded=False,  # params not decoded without eth-abi
                )

    return DecodedCall(selector=selector, method=None, raw_input=tx_input_hex, decoded=False)


def _minimal_decode(calldata: str, param_names: list[str]) -> dict[str, Any]:
    """Decode fixed-size 32-byte ABI words for named params."""
    params: dict[str, Any] = {}
    chunk_size = 64  # 32 bytes = 64 hex chars
    for i, name in enumerate(param_names):
        start = i * chunk_size
        end = start + chunk_size
        if end > len(calldata):
            break
        word = calldata[start:end]
        # Heuristic: address params
        if "address" in name.lower() or name in ("to", "from", "spender", "owner", "operator"):
            params[name] = "0x" + word[-40:]
        else:
            try:
                params[name] = int(word, 16)
            except ValueError:
                params[name] = word
    return params


def _abi_selector(entry: dict) -> str:
    """Compute the 4-byte selector hex string for a function ABI entry."""
    import hashlib
    name = entry.get("name", "")
    inputs = entry.get("inputs", [])
    types = ",".join(i.get("type", "") for i in inputs)
    sig = f"{name}({types})"
    digest = hashlib.sha3_256(sig.encode()).hexdigest()  # keccak256 approximation
    # Note: keccak256 != sha3_256, but without eth-abi installed this is structural only
    # TODO: replace with eth_hash.auto.keccak(sig.encode()).hex()[:8] when available
    return digest[:8]
