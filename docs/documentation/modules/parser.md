# Parser Module

**Location:** `backend/core/parser/`

## Purpose

Decode ERC-20/ERC-721 and common DeFi method calls from transaction input hex. Match against known selectors or provided ABI. Identify exploit patterns (reentrancy, flash loans, approval drains).

## Public API

### `abi.py`

**`decode_call(tx_input_hex: str, abi: Optional[list[dict]] = None) -> DecodedCall`**
Decode 4-byte selector and optional parameters. Falls back to eth-abi if ABI provided; otherwise uses hardcoded selector table + minimal manual decode.

**`DecodedCall`** (dataclass)
```python
selector: str               # first 8 hex chars (4 bytes)
method: Optional[str]       # e.g., "transfer", "swapExactTokensForTokens"
params: dict[str, Any]      # decoded parameters if possible
raw_input: str              # original tx_input_hex
decoded: bool               # True if params successfully decoded
```

**Module-level selector table `KNOWN_SELECTORS`:**
~40 common methods hardcoded:
- **ERC-20:** transfer (a9059cbb), transferFrom, approve, balanceOf, etc.
- **ERC-721:** safeTransferFrom, ownerOf, setApprovalForAll, etc.
- **Uniswap v2/v3:** swapExactTokensForTokens, exactInputSingle, etc.
- **Aave v2/v3:** flashLoan, flashLoanSimple
- **DyDx:** operate (flash loans)
- **Balancer:** flashLoan
- **WETH:** deposit, withdraw
- **Multicall:** multicall

**Decoding strategy:**
1. Extract selector (first 8 hex chars)
2. If in `KNOWN_SELECTORS`: try selector-based decode
3. If ABI provided and unknown selector: search ABI for method (structural match, no param decode without eth-abi)
4. Return `DecodedCall` with best-effort params

**Helper functions:**
- `_minimal_decode(calldata: str, param_names: list[str]) -> dict[str, Any]` — Manual decode of 32-byte ABI words. Heuristic: addresses identified by param name hints ("to", "from", "spender", etc.)
- `_abi_selector(entry: dict) -> str` — Compute 4-byte selector from ABI entry (keccak256 approximation using sha3_256; TODO: replace with proper keccak)

### `patterns.py`

**`match_reentrancy(tx: dict) -> bool`**
Detect reentrancy-vulnerable pattern: method call → external call → return to self.

**`match_flash_loan(tx: dict) -> bool`**
Detect flash loan attack signature: flashLoan call + large value transfer + repayment in same tx.

**`match_approval_drain(tx: dict) -> bool`**
Detect approval drain exploit: approve() call to suspicious contract + subsequent transferFrom().

## Algorithm & Data Flow

```
decode_call(tx_input_hex, abi)
├─ if len < 10: return empty DecodedCall
├─ extract selector = input[2:10] (skip 0x prefix)
├─ extract calldata = input[10:]
├─ if selector in KNOWN_SELECTORS:
│  ├─ method_name, param_names = lookup
│  ├─ if abi provided:
│  │  └─ try full decode via eth-abi (TODO: not yet implemented)
│  ├─ else: _minimal_decode(calldata, param_names)
│  └─ return DecodedCall(selector, method, params, decoded=True)
├─ elif abi provided:
│  ├─ search ABI for matching selector
│  └─ return DecodedCall(selector, method, params={}, decoded=False)
└─ else: return DecodedCall(selector, None, {}, decoded=False)

_minimal_decode(calldata, param_names)
├─ for each param in param_names:
│  ├─ extract 64-hex-char (32-byte) word
│  ├─ if param is address-like: extract last 40 chars (20 bytes)
│  └─ else: parse as uint256
└─ return params dict

_abi_selector(abi_entry)
├─ extract name + input types
├─ build signature: "name(type1,type2,...)"
├─ hash via sha3_256 (approximation; TODO: use keccak256)
└─ return first 8 chars
```

## Dependencies

**Imports:**
- `hashlib` — sha3_256 (TODO: replace with proper keccak256)
- Async data layer (TODO: eth-abi library when available)

**Imported by:**
- `backend.api.routes.report` — decode tx calldata for incident narrative
- Exploitation pattern detector (not yet implemented)

## Extension Points

1. **Add new selector:** Append entry to `KNOWN_SELECTORS` dict. Format: `"selector": ("method_name", ["param1", "param2"])`.
2. **Add new exploit pattern:** Implement `match_*_pattern()` function in `patterns.py`.
3. **Parameter type hints:** Enhance `_minimal_decode()` to handle dynamic arrays, tuples, etc.

## Testing Guidance

**Unit tests:**
- Test selector extraction for valid hex strings
- Test known selector lookup for ERC-20 transfer, Uniswap swap, etc.
- Test unknown selector fallback to ABI search
- Test `_minimal_decode()` with address params (last 40 chars) vs uint params
- Test edge cases: empty input, malformed hex, missing ABI

**Integration:**
- Decode real tx from etherscan for Uniswap swap
- Decode WETH deposit and withdraw
- Decode flash loan call
- Verify exploit pattern matchers detect known attack txs

## Known Gaps & TODOs

- `abi.py:82` — eth-abi library wiring TODO; full parameter decode not implemented
- `abi.py:150` — keccak256 replaced with sha3_256 approximation; TODO: use eth_hash.auto.keccak
- `patterns.py` — file exists but exploit matchers not yet implemented (match_reentrancy, match_flash_loan, match_approval_drain)
- No dynamic array/tuple decoding (only fixed-size 32-byte words)
- No support for function overloading (same name, different signatures)

## See Also

- `ai.md` — uses decoded calls in report generation
- `data-providers.md` — may fetch ABIs from Etherscan/Block Explorer
