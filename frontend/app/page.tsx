'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { Chain } from '@/lib/types';

const chains: { value: Chain; label: string }[] = [
  { value: 'eth', label: 'Ethereum' },
  { value: 'polygon', label: 'Polygon' },
  { value: 'arbitrum', label: 'Arbitrum' },
  { value: 'base', label: 'Base' },
  { value: 'bsc', label: 'BNB Chain' },
  { value: 'solana', label: 'Solana' },
];

export default function Home() {
  const router = useRouter();
  const [traceInput, setTraceInput] = useState('');
  const [traceChain, setTraceChain] = useState<Chain>('eth');
  const [profileInput, setProfileInput] = useState('');
  const [profileChain, setProfileChain] = useState<Chain>('eth');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleStartTrace = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await apiClient.startTrace({ input: traceInput, chain: traceChain });
      router.push(`/trace/${result.job_id}`);
    } catch (err) {
      setError(`Failed to start trace: ${String(err)}`);
      setLoading(false);
    }
  };

  const handleStartProfile = (e: React.FormEvent) => {
    e.preventDefault();
    router.push(`/profile/${profileInput}?chain=${profileChain}`);
  };

  return (
    <>
      {/* ——— Hero ——— */}
      <section className="ambient-bg">
        <div className="max-w-7xl mx-auto px-6 pt-24 pb-16 text-center animate-fade-up">
          <p className="apple-eyebrow">Open source. Self-hostable. Multi-chain.</p>
          <h1 className="apple-h1 mt-4 mb-6">
            <span className="hero-gradient">Follow the money.</span>
            <br />
            <span className="text-white/90">Across every chain.</span>
          </h1>
          <p className="apple-body max-w-2xl mx-auto text-ink-200">
            ChainTrace traces stolen funds hop by hop and profiles any wallet — risk score,
            labels, counterparties, behavior — across Ethereum, Polygon, Arbitrum, Base,
            BNB Chain, and Solana.
          </p>
          <div className="mt-10 flex items-center justify-center gap-3 flex-wrap">
            <Link href="/trace" className="apple-btn-primary">
              Start a trace →
            </Link>
            <Link href="/profile/0x" className="apple-btn-secondary">
              Profile a wallet
            </Link>
            <a
              href="https://github.com/"
              className="apple-btn-ghost"
              target="_blank"
              rel="noreferrer"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </section>

      {/* ——— Quickstart forms ——— */}
      <section className="max-w-7xl mx-auto px-6">
        {error && (
          <div className="mb-8 rounded-apple-md border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-300">
            {error}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          <form onSubmit={handleStartTrace} className="chain-card">
            <div className="apple-eyebrow mb-3">Hack Tracer</div>
            <h2 className="apple-h3">Trace an exploit</h2>
            <p className="apple-sub mt-2 mb-6">
              Start from a theft transaction or suspect wallet. We walk the graph until funds
              land at an exchange, mixer, or bridge.
            </p>

            <div className="space-y-4">
              <div>
                <label className="apple-label">Transaction hash or address</label>
                <input
                  type="text"
                  value={traceInput}
                  onChange={(e) => setTraceInput(e.target.value)}
                  placeholder="0x… or tx hash"
                  className="apple-input font-mono"
                  required
                  disabled={loading}
                />
              </div>
              <div>
                <label className="apple-label">Starting chain</label>
                <select
                  value={traceChain}
                  onChange={(e) => setTraceChain(e.target.value as Chain)}
                  className="apple-input"
                  disabled={loading}
                >
                  {chains.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="submit"
                disabled={loading || !traceInput}
                className="apple-btn-primary w-full mt-2"
              >
                {loading ? 'Starting trace…' : 'Start trace →'}
              </button>
            </div>
          </form>

          <form onSubmit={handleStartProfile} className="chain-card">
            <div className="apple-eyebrow mb-3">Wallet Profiler</div>
            <h2 className="apple-h3">Risk-score any wallet</h2>
            <p className="apple-sub mt-2 mb-6">
              Weighted signals: mixer interactions, darknet counterparties, exploit history,
              velocity, and protocol usage — tuned for incident response.
            </p>

            <div className="space-y-4">
              <div>
                <label className="apple-label">Wallet address</label>
                <input
                  type="text"
                  value={profileInput}
                  onChange={(e) => setProfileInput(e.target.value)}
                  placeholder="0x…"
                  className="apple-input font-mono"
                  required
                />
              </div>
              <div>
                <label className="apple-label">Chain</label>
                <select
                  value={profileChain}
                  onChange={(e) => setProfileChain(e.target.value as Chain)}
                  className="apple-input"
                >
                  {chains.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="submit"
                disabled={!profileInput}
                className="apple-btn-primary w-full mt-2"
              >
                Profile wallet →
              </button>
            </div>
          </form>
        </div>
      </section>

      {/* ——— Features ——— */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-14">
          <p className="apple-eyebrow">Why ChainTrace</p>
          <h2 className="apple-h2 mt-3">Chainalysis-grade investigation, without the invoice.</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            {
              title: 'AI is a formatter, not an analyst',
              body: 'Deterministic Python drives every traversal, score, and cluster. The LLM just writes readable prose from pre-analyzed JSON.',
            },
            {
              title: 'Neo4j is database and cache',
              body: 'Investigate once, keep forever. Repeat traces of the same wallet hit zero external APIs.',
            },
            {
              title: 'Free-tier by design',
              body: 'Covalent → Alchemy → Etherscan family → public RPC. Keys round-robin with 429-aware cooldown.',
            },
            {
              title: 'Six chains out of the box',
              body: 'Ethereum, Polygon, Arbitrum, Base, BNB Chain, Solana — with cross-chain bridge matching.',
            },
            {
              title: 'Real-time monitor',
              body: 'Alchemy Webhooks and Moralis Streams push wallet activity straight to Discord, Telegram, or your dashboard.',
            },
            {
              title: 'Truly self-hostable',
              body: 'One docker-compose command spins up Neo4j, Redis, Postgres, the API, and the UI on your own hardware.',
            },
          ].map((f) => (
            <div key={f.title} className="chain-card">
              <h3 className="font-display text-[19px] font-semibold text-white tracking-apple-display">
                {f.title}
              </h3>
              <p className="apple-sub mt-2">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ——— Limitations ——— */}
      <section id="limitations" className="max-w-4xl mx-auto px-6 py-16 text-center">
        <p className="apple-eyebrow">Honest limits</p>
        <h2 className="apple-h3 mt-3 mb-6">What this tool does not do</h2>
        <ul className="space-y-3 text-ink-200 text-[15px] leading-relaxed">
          <li>CEX deposits end the trail — we flag the block & timestamp for law enforcement.</li>
          <li>Mixer tracing is probabilistic only, and every candidate is labeled unconfirmed.</li>
          <li>Privacy coins (Monero, shielded Zcash) are outside the supported surface.</li>
          <li>Label coverage starts thin and grows with every investigation.</li>
        </ul>
      </section>
    </>
  );
}
