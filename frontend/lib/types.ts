// Backend uses `arb` (not `arbitrum`) — see backend/models/wallet.py:Chain
export type Chain = 'eth' | 'polygon' | 'arb' | 'base' | 'bsc' | 'solana';

export interface TraceNode {
  address: string;
  chain: Chain;
  balance_usd: number;
  label?: string;
  terminal_type?: 'cex' | 'mixer' | 'bridge' | 'cold' | 'unknown';
  depth: number;
  tx_count: number;
}

export interface TraceEdge {
  from: string;
  to: string;
  tx_hash: string;
  block: number;
  timestamp: number;
  value: string;
  value_usd: number;
  token: string;
  chain: Chain;
}

export interface TraceResult {
  id: string;
  seed: string;
  chain: Chain;
  nodes: TraceNode[];
  edges: TraceEdge[];
  terminals: Array<{
    address: string;
    terminal_type: string;
    confidence: number;
  }>;
  created_at: number;
  hops_count: number;
}

export interface RiskScore {
  score: number;
  level: 'low' | 'medium' | 'high' | 'critical';
  signals: RiskSignal[];
}

export interface RiskSignal {
  name: string;
  weight: number;
  category: 'positive' | 'negative';
}

export interface Label {
  name: string;
  source: 'hardcoded' | 'community' | 'etherscan' | 'arkham' | 'user' | 'heuristic';
  confidence: number;
}

export interface CounterpartyInfo {
  address: string;
  label?: string;
  interaction_count: number;
  total_value_usd: number;
  last_interaction: number;
}

export interface BehaviorTag {
  tag: string;
  score: number;
  description: string;
}

export interface ProfileResult {
  address: string;
  chain: Chain;
  risk: RiskScore;
  labels: Label[];
  counterparties: CounterpartyInfo[];
  behavior_tags: BehaviorTag[];
  first_seen: number;
  last_seen: number;
  tx_count: number;
  balance_usd: number;
}

export interface AlertRule {
  id: string;
  address: string;
  rule_type: 'address' | 'value' | 'label';
  rule_value: string;
  min_value_usd?: number;
  enabled: boolean;
  created_at: number;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  address: string;
  tx_hash: string;
  value_usd: number;
  timestamp: number;
  chain: Chain;
}

export interface ReportData {
  id: string;
  title: string;
  summary: string;
  trace_id?: string;
  address?: string;
  created_at: number;
  content: string;
}
