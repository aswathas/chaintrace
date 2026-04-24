'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { ProfileResult, Chain } from '@/lib/types';
import { RiskCard } from '@/components/profiler/RiskCard';
import { CounterpartyTable } from '@/components/profiler/CounterpartyTable';
import { BehaviorTags } from '@/components/profiler/BehaviorTags';
import { AddressChip } from '@/components/shared/AddressChip';
import { LabelPill } from '@/components/shared/LabelPill';
import { formatUsd, formatDate } from '@/lib/format';

export default function ProfilePage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const address = params.addr as string;
  const chain = (searchParams.get('chain') || 'eth') as Chain;

  const [profile, setProfile] = useState<ProfileResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const result = await apiClient.getProfile(address, chain);
        setProfile(result);
        setLoading(false);
      } catch (err) {
        setError(`Failed to load profile: ${String(err)}`);
        setLoading(false);
      }
    };

    fetchProfile();
  }, [address, chain]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-ink-800 rounded-apple" />
          <div className="h-96 bg-ink-800 rounded-apple" />
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <Link href="/" className="text-apple-blueBright hover:text-emerald-300 text-sm mb-8 inline-block">
          ← Back to Home
        </Link>
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-apple-md p-8 text-rose-300 text-center">
          <p className="font-semibold mb-2">Failed to Load Profile</p>
          <p className="text-sm">{error || 'Profile not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <Link href="/" className="text-apple-blueBright hover:text-emerald-300 text-sm mb-8 inline-block">
        ← Back to Home
      </Link>

      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 border border-white/10 rounded-apple-md p-8 mb-8">
        <h1 className="text-3xl font-bold text-ink-50 mb-4">Wallet Profile</h1>
        <div className="mb-4">
          <AddressChip address={profile.address} chain={profile.chain} />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-ink-400 uppercase font-semibold text-xs mb-1">Balance</p>
            <p className="text-lg font-bold text-ink-50">{formatUsd(profile.balance_usd)}</p>
          </div>
          <div>
            <p className="text-ink-400 uppercase font-semibold text-xs mb-1">Transactions</p>
            <p className="text-lg font-bold text-ink-50">{profile.tx_count}</p>
          </div>
          <div>
            <p className="text-ink-400 uppercase font-semibold text-xs mb-1">First Seen</p>
            <p className="text-sm text-ink-200">{formatDate(profile.first_seen)}</p>
          </div>
          <div>
            <p className="text-ink-400 uppercase font-semibold text-xs mb-1">Last Seen</p>
            <p className="text-sm text-ink-200">{formatDate(profile.last_seen)}</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-3 gap-8 mb-8">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Labels */}
          {profile.labels.length > 0 && (
            <div className="bg-ink-800 border border-white/10 rounded-apple-md p-6">
              <h2 className="text-lg font-semibold text-ink-50 mb-4">Labels</h2>
              <div className="flex flex-wrap gap-2">
                {profile.labels.map((label, idx) => (
                  <LabelPill key={idx} label={label} />
                ))}
              </div>
            </div>
          )}

          {/* Behavior Tags */}
          <div className="bg-ink-800 border border-white/10 rounded-apple-md p-6">
            <h2 className="text-lg font-semibold text-ink-50 mb-4">Behavior Patterns</h2>
            <BehaviorTags tags={profile.behavior_tags} />
          </div>

          {/* Counterparties */}
          <div>
            <h2 className="text-lg font-semibold text-ink-50 mb-4">Counterparties</h2>
            <CounterpartyTable counterparties={profile.counterparties} />
          </div>
        </div>

        {/* Right Column */}
        <div>
          <RiskCard risk={profile.risk} />
        </div>
      </div>

      {/* Raw Signal Breakdown */}
      <div className="bg-ink-800 border border-white/10 rounded-apple-md p-6">
        <h2 className="text-lg font-semibold text-ink-50 mb-4">Signal Breakdown</h2>
        <div className="space-y-2">
          {profile.risk.signals.map((signal, idx) => (
            <div key={idx} className="flex items-center justify-between text-sm p-2 rounded-apple bg-white/5/50">
              <span className="text-ink-100">{signal.name}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-ink-300">({signal.category})</span>
                <span
                  className={`font-semibold ${
                    signal.category === 'positive' ? 'text-red-400' : 'text-green-400'
                  }`}
                >
                  {signal.category === 'positive' ? '+' : '-'} {Math.abs(signal.weight)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
