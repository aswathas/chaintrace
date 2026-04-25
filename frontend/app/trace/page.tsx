'use client';

import { useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { Chain } from '@/lib/types';

export default function TracePage() {
  const [input, setInput] = useState('');
  const [chain, setChain] = useState<Chain>('eth');
  const [maxHops, setMaxHops] = useState('10');
  const [minValue, setMinValue] = useState('100');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await apiClient.startTrace({
        input,
        chain,
        max_hops: parseInt(maxHops),
        min_value_usd: parseInt(minValue),
      });
      window.location.href = `/trace/${result.job_id}`;
    } catch (err) {
      setError(`Failed to start trace: ${String(err)}`);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <Link href="/" className="text-apple-blueBright hover:text-emerald-300 text-sm mb-8 inline-block">
        ← Back to Home
      </Link>

      <div className="bg-ink-800 border border-white/10 rounded-apple-md p-8">
        <h1 className="text-3xl font-bold text-ink-50 mb-2">Hack Tracer</h1>
        <p className="text-ink-300 mb-8">
          Start a multi-hop fund flow investigation from an address or transaction
        </p>

        {error && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-apple-md text-rose-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-ink-100 mb-2">
              Starting Address or Transaction Hash
            </label>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="0x... or 0x...tx"
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-apple text-ink-50 placeholder-ink-300 focus:border-apple-blue outline-none"
              required
              disabled={loading}
            />
            <p className="mt-2 text-xs text-ink-300">
              Paste a wallet address or transaction hash to trace fund flows
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ink-100 mb-2">
                Chain
              </label>
              <select
                value={chain}
                onChange={(e) => setChain(e.target.value as Chain)}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-apple text-ink-50 focus:border-apple-blue outline-none"
                disabled={loading}
              >
                <option value="eth">Ethereum</option>
                <option value="polygon">Polygon</option>
                <option value="arb">Arbitrum</option>
                <option value="base">Base</option>
                <option value="bsc">BNB Chain</option>
                <option value="solana">Solana</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-100 mb-2">
                Max Hops
              </label>
              <input
                type="number"
                value={maxHops}
                onChange={(e) => setMaxHops(e.target.value)}
                min="1"
                max="20"
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-apple text-ink-50 focus:border-apple-blue outline-none"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-ink-300">Recommended: 10 (prevents explosion)</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-100 mb-2">
              Minimum Value (USD)
            </label>
            <input
              type="number"
              value={minValue}
              onChange={(e) => setMinValue(e.target.value)}
              min="0"
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-apple text-ink-50 focus:border-apple-blue outline-none"
              disabled={loading}
            />
            <p className="mt-1 text-xs text-ink-300">
              Filter hops below this threshold (helps reduce noise)
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !input}
            className="w-full px-6 py-3 bg-apple-blue hover:bg-apple-blueDark disabled:bg-white/5 text-white font-semibold rounded-apple transition-colors"
          >
            {loading ? 'Starting Investigation...' : 'Start Trace'}
          </button>
        </form>

        <div className="mt-8 pt-8 border-t border-white/10">
          <h3 className="text-sm font-semibold text-ink-100 mb-3">How it works</h3>
          <ol className="space-y-2 text-sm text-ink-300">
            <li>1. Provide a starting wallet or transaction hash</li>
            <li>2. Select the blockchain where the investigation starts</li>
            <li>3. ChainTrace will fetch all outflows and detect terminals (CEX, mixer, bridge, cold)</li>
            <li>
              4. For bridge transfers, the investigation will automatically cross chains and continue
            </li>
            <li>5. View an interactive graph with hop timeline and terminal analysis</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
