import { RiskScore } from './types';

export function shortAddress(addr: string): string {
  if (!addr) return '';
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export function formatUsd(amount: number): string {
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(2)}M`;
  }
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(2)}K`;
  }
  return `$${amount.toFixed(2)}`;
}

export function formatTimestamp(ts: number): string {
  const date = new Date(ts * 1000);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDate(ts: number): string {
  const date = new Date(ts * 1000);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function riskLevelColor(level: string): string {
  const colors: Record<string, string> = {
    low: 'bg-emerald-600 text-white',
    medium: 'bg-amber-600 text-white',
    high: 'bg-red-600 text-white',
    critical: 'bg-red-700 text-white',
  };
  return colors[level] || 'bg-slate-700 text-white';
}

export function riskLevelBg(level: string): string {
  const colors: Record<string, string> = {
    low: 'bg-emerald-50 border-emerald-300',
    medium: 'bg-amber-50 border-amber-300',
    high: 'bg-red-50 border-red-300',
    critical: 'bg-red-100 border-red-400',
  };
  return colors[level] || 'bg-slate-100 border-slate-300';
}

export function terminalTypeColor(type: string): string {
  const colors: Record<string, string> = {
    cex: '#10b981',
    mixer: '#ef4444',
    bridge: '#a855f7',
    cold: '#94a3b8',
    unknown: '#64748b',
  };
  return colors[type] || '#64748b';
}

export function chainLabel(chain: string): string {
  const labels: Record<string, string> = {
    eth: 'Ethereum',
    polygon: 'Polygon',
    arbitrum: 'Arbitrum',
    base: 'Base',
    bsc: 'BNB Chain',
    solana: 'Solana',
  };
  return labels[chain] || chain.toUpperCase();
}

export function chainColor(chain: string): string {
  const colors: Record<string, string> = {
    eth: 'bg-blue-600',
    polygon: 'bg-purple-600',
    arbitrum: 'bg-blue-500',
    base: 'bg-sky-600',
    bsc: 'bg-yellow-600',
    solana: 'bg-green-600',
  };
  return colors[chain] || 'bg-slate-600';
}

export function labelSourceColor(source: string): string {
  const colors: Record<string, string> = {
    hardcoded: 'bg-red-100 text-red-900 border-red-300',
    community: 'bg-purple-100 text-purple-900 border-purple-300',
    etherscan: 'bg-blue-100 text-blue-900 border-blue-300',
    arkham: 'bg-yellow-100 text-yellow-900 border-yellow-300',
    user: 'bg-green-100 text-green-900 border-green-300',
    heuristic: 'bg-indigo-100 text-indigo-900 border-indigo-300',
  };
  return colors[source] || 'bg-slate-100 text-slate-900 border-slate-300';
}

export function confidencePercent(conf: number): string {
  return `${Math.round(conf * 100)}%`;
}
