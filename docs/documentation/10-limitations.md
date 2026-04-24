# Limitations

This document describes the honest capability boundaries of ChainTrace. Each limitation is explained with: what it is, why it exists, how it is communicated in the UI, and what a future release might do to address it. Understanding these limitations is essential before drawing investigative conclusions.

---

## CEX deposits end the trail

**What it is.** When traced funds reach a centralized exchange (Coinbase, Binance, Kraken, etc.), ChainTrace reports the deposit transaction — including hash, block number, timestamp, and value — and marks that branch of the trace as `terminal: cex_deposit`. The investigation cannot proceed past this point.

**Why it exists.** Centralized exchanges assign deposit addresses dynamically to users. The on-chain address is a hot wallet shared across many users; the exchange's internal ledger maps that deposit to a specific account. That internal mapping is KYC-linked and held privately by the exchange. ChainTrace has no access to internal exchange ledgers.

**What the UI shows.** The terminal node is displayed as a red "CEX Deposit" endpoint with the exchange name (when labeled), the deposit tx hash, and a timestamp. A tooltip reads: *"Funds reached a centralized exchange. On-chain tracing ends here. The deposit hash and timestamp below can be included in a law enforcement referral to the exchange."*

**What a future release could do.** Nothing within the read-only model. The only path forward for investigators is a formal subpoena or voluntary disclosure request to the exchange. ChainTrace can generate a formatted referral document (planned for M7) containing all relevant hashes, timestamps, and chain of custody evidence to support that process.

---

## Mixer tracing is probabilistic only

**What it is.** When funds enter a Tornado Cash pool (or any other mixer using zero-knowledge proofs), the cryptographic link between deposit and withdrawal is broken by design. ChainTrace cannot definitively link a specific deposit to a specific withdrawal.

**What we do instead.** For Tornado Cash, we use denomination matching and timing heuristics: we scan for all withdrawals of the same denomination (0.1, 1, 10, or 100 ETH) within a 72-hour window after the deposit. We rank candidates by timing proximity and gas-price fingerprint similarity. All candidates are returned as a ranked list.

**Why this matters.** A "candidate withdrawal" is not a confirmed link. It is a probabilistic indicator. Drawing a definitive conclusion from mixer exit candidates without corroborating evidence is methodologically unsound and could harm innocent parties.

**What the UI shows.** Mixer exit candidates are displayed with a dashed-line edge (not a solid line) and labeled *"Unconfirmed mixer exit — probabilistic only."* The confidence percentage is shown alongside each candidate.

**What a future release could do.** On-chain Zero-Knowledge proof systems are not breakable by design. However, cross-referencing mixer exit candidates with post-exit behavior (same gas price pattern, same counterparties, same timing) can raise or lower confidence. Improved behavioral fingerprinting could improve the ranking quality without changing the fundamental probabilistic nature of the output.

---

## Label coverage starts thin

**What it is.** ChainTrace starts with a hardcoded set of high-confidence labels (Tornado Cash pools, major DEX routers, known CEX hot wallets, famous exploit addresses). Beyond that, labels come from community repos, Etherscan public tags, Arkham, and user submissions. The majority of addresses — especially newly created wallets — will appear as `unlabeled`.

**Why it exists.** There are hundreds of millions of active Ethereum addresses. No static label database covers more than a fraction of them. Closed tools like Chainalysis invest heavily in proprietary labeling pipelines; ChainTrace relies on public sources.

**The compounding effect.** Every investigation persists results in Neo4j. Over time, if a given address appears in multiple investigations and picks up a label in any of them, subsequent traces that encounter that address will show the label. The graph grows smarter with use.

**What the UI shows.** Unlabeled nodes are displayed as gray hexagons. The risk score for an unlabeled node is computed from behavioral signals alone (velocity, age, round amounts) rather than counterparty labels.

**What a future release could do.** Community label submissions with a review workflow (planned for M7), periodic ingestion of additional public label databases, and heuristic auto-labeling based on behavioral patterns. Integration with DeBank or Nansen public datasets is a possible future addition.

---

## Privacy coins are out of scope

**What it is.** Monero and Zcash shielded transactions are cryptographically private. Transaction amounts, sender, and receiver are hidden at the protocol level. ChainTrace cannot trace funds that have moved through Monero or Zcash shielded pools.

**Why it exists.** This is not a limitation of ChainTrace's implementation — it is a mathematical property of these protocols. No tool (including Chainalysis) can trace within Monero. Zcash transparent transactions can be traced; shielded ones cannot.

**What the UI shows.** If a trace reaches a known Monero bridge or Zcash shielded deposit, ChainTrace marks the branch as `terminal: privacy_coin` with a note: *"Funds moved into a privacy-preserving system. On-chain tracing is not possible from this point. This is a fundamental cryptographic limitation."*

**What a future release could do.** Nothing within the on-chain read model. Some researchers have proposed statistical timing attacks on privacy coin networks, but these are academic and not reliable in practice. ChainTrace will not implement or claim any Monero de-anonymization capability.

---

## No subpoena power

**What it is.** ChainTrace is a research tool, not a law enforcement instrument. It cannot compel exchanges, custodians, or protocol operators to disclose user information.

**Why it matters for investigations.** In most practical hack recovery cases, the on-chain trail terminates at a CEX deposit or a mixer. Recovering the stolen funds requires the exchange to freeze the account and cooperate with law enforcement. ChainTrace can provide the evidence package to support that request — it cannot force the outcome.

**What the UI shows.** The investigation summary includes a "Law Enforcement Referral" section for any traces with CEX terminal destinations, pre-formatted with: deposit address, tx hash, block number, timestamp, estimated value, and chain.

**What a future release could do.** Formatted referral documents tailored to specific jurisdiction requirements (e.g., US FinCEN SAR format, Europol request templates) are planned for M7. These would make it easier to hand off ChainTrace findings to legal teams or law enforcement.

---

## Rate limits constrain investigation speed

**What it is.** ChainTrace relies on free-tier API keys from Covalent, Alchemy, and the Etherscan family. These have hard rate limits: Etherscan allows 5 requests/second per key; Alchemy's free tier has 300M compute units/month. A heavy investigation can exhaust a key pool quickly.

**Why it exists.** Commercial APIs charge for high-rate access. ChainTrace is designed to be free — the tradeoff is speed for investigations that exceed free-tier limits.

**What the UI shows.** When a trace is slowing down due to provider throttling, the backend logs include provider headroom information exposed via `/health`. A future UI indicator (planned for M7) will show current provider pool status in the investigation header.

**What a future release could do.** Key pool expansion (supporting more free accounts), better cache hit rates (Neo4j re-use reduces provider calls over time), and optional paid-tier provider configuration for teams that need higher throughput.

---

## Solana account model impedance

**What it is.** Solana's account model differs fundamentally from EVM's transaction model. Solana transactions can involve multiple accounts, programs (smart contracts), and instruction sets in ways that do not map cleanly to the simple `wallet → tx → wallet` edge model ChainTrace uses for EVM chains.

**Why it exists.** The ChainTrace graph model was designed for EVM chains first. Adapting it to Solana requires a normalization layer (`data/graph/` Solana adapter) that translates Solana's (program, account, instruction) model into the same edge shape. This is a planned piece of work, not a fundamental impossibility.

**What the UI shows.** Solana traces are supported with a caveat banner: *"Solana tracing is in beta. Complex multi-instruction transactions may appear simplified in the graph view."*

**What a future release could do.** A full Solana-native adapter that correctly models SPL token transfers, program invocations, and cross-program interactions. Community contributions to this adapter are welcome — see [08-contributing.md](08-contributing.md).

---

## Cross-chain hops require known bridge registry

**What it is.** Cross-chain bridge detection works by matching inbound and outbound events on known bridge contract addresses (Stargate, Wormhole, LayerZero, Synapse, Across, Hop). If a bridge is not in the registry, ChainTrace cannot follow funds across it.

**Why it exists.** The bridge registry is maintained manually. New bridges launch regularly, and each requires verification of their specific deposit/withdrawal event signatures.

**What the UI shows.** When a trace encounters an unknown contract that appears to be bridge-like behavior (large value transfer to contract, followed by similar outflow on another chain near the same time), ChainTrace flags it as *"Possible bridge — unverified. Manual review recommended."*

**What a future release could do.** Auto-detection of bridge contracts from on-chain event signature patterns. Community contributions to the bridge registry are accepted via pull request to `backend/core/tracer/terminals.py`.

---

## See also

- [04-api-reference.md](04-api-reference.md) — how terminal types appear in trace responses
- [07-security.md](07-security.md) — what ChainTrace does and does not claim to prove
- [09-operations.md](09-operations.md) — what to do when rate limits constrain an investigation
