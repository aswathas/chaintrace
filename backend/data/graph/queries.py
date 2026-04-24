"""Cypher query templates as string constants."""

UPSERT_WALLET = """
MERGE (w:Wallet {address: $address, chain: $chain})
ON CREATE SET
  w.first_seen   = $first_seen,
  w.last_seen    = $last_seen,
  w.tx_count     = $tx_count,
  w.balance_usd  = $balance_usd,
  w.labels       = $labels,
  w.risk_score   = $risk_score,
  w.is_contract  = $is_contract,
  w.created_at_block = $created_at_block
ON MATCH SET
  w.last_seen    = $last_seen,
  w.tx_count     = $tx_count,
  w.balance_usd  = $balance_usd,
  w.labels       = $labels,
  w.risk_score   = COALESCE($risk_score, w.risk_score)
RETURN w
"""

UPSERT_TX_EDGE = """
MATCH (src:Wallet {address: $src, chain: $chain})
MATCH (dst:Wallet {address: $dst, chain: $chain})
MERGE (src)-[e:SENT {tx_hash: $tx_hash, chain: $chain}]->(dst)
ON CREATE SET
  e.block      = $block,
  e.timestamp  = $timestamp,
  e.value      = $value,
  e.value_usd  = $value_usd,
  e.token      = $token
RETURN e
"""

GET_OUTFLOWS = """
MATCH (src:Wallet {address: $address, chain: $chain})-[e:SENT]->(dst:Wallet)
RETURN dst.address AS dst_address, e.tx_hash AS tx_hash,
       e.block AS block, e.timestamp AS timestamp,
       e.value AS value, e.value_usd AS value_usd, e.token AS token
ORDER BY e.value_usd DESC NULLS LAST
LIMIT $limit
"""

GET_WALLET_NEIGHBORHOOD = """
MATCH (w:Wallet {address: $address, chain: $chain})
OPTIONAL MATCH (w)-[out:SENT]->(neighbor:Wallet)
OPTIONAL MATCH (incoming:Wallet)-[inc:SENT]->(w)
RETURN w,
       collect(DISTINCT {edge: out, wallet: neighbor}) AS outgoing,
       collect(DISTINCT {edge: inc, wallet: incoming}) AS incoming
"""
