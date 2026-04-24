'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { AlertRule, AlertEvent } from '@/lib/types';
import { RuleEditor } from '@/components/alerts/RuleEditor';
import { AlertRow } from '@/components/alerts/AlertRow';
import { AlertList } from '@/components/alerts/AlertList';

export default function MonitorPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'rules' | 'alerts'>('rules');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const alertsData = await apiClient.listAlerts();
        setAlerts(alertsData);
        setLoading(false);
      } catch (err) {
        setError(`Failed to load data: ${String(err)}`);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleCreateRule = async (data: any) => {
    setCreating(true);
    setError('');

    try {
      const rule = await apiClient.createAlert(data);
      setRules((prev) => [rule, ...prev]);
      setCreating(false);
    } catch (err) {
      setError(`Failed to create rule: ${String(err)}`);
      setCreating(false);
    }
  };

  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      const updated = await apiClient.updateAlert(ruleId, enabled);
      setRules((prev) =>
        prev.map((r) => (r.id === ruleId ? updated : r))
      );
    } catch (err) {
      setError(`Failed to update rule: ${String(err)}`);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Delete this alert rule?')) return;

    try {
      await apiClient.deleteAlert(ruleId);
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
    } catch (err) {
      setError(`Failed to delete rule: ${String(err)}`);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-96 bg-ink-800 rounded-apple" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <Link href="/" className="text-apple-blueBright hover:text-emerald-300 text-sm mb-8 inline-block">
        ← Back to Home
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-ink-50 mb-2">Real-Time Monitoring</h1>
        <p className="text-ink-300">
          Set up alert rules and monitor wallet activity as it happens
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-apple-md text-rose-300 text-sm">
          {error}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-8">
        {/* New Rule Form */}
        <div className="lg:col-span-1">
          <RuleEditor onSubmit={handleCreateRule} isLoading={creating} />
        </div>

        {/* Alerts & Rules */}
        <div className="lg:col-span-2">
          <div className="bg-ink-800 border border-white/10 rounded-apple-md overflow-hidden">
            <div className="border-b border-white/10 flex">
              <button
                onClick={() => setActiveTab('rules')}
                className={`flex-1 px-6 py-3 font-semibold transition-colors ${
                  activeTab === 'rules'
                    ? 'bg-white/5 text-apple-blueBright border-b-2 border-emerald-400'
                    : 'text-ink-300 hover:text-ink-50'
                }`}
              >
                Active Rules ({rules.length})
              </button>
              <button
                onClick={() => setActiveTab('alerts')}
                className={`flex-1 px-6 py-3 font-semibold transition-colors ${
                  activeTab === 'alerts'
                    ? 'bg-white/5 text-apple-blueBright border-b-2 border-emerald-400'
                    : 'text-ink-300 hover:text-ink-50'
                }`}
              >
                Triggered Alerts ({alerts.length})
              </button>
            </div>

            <div className="p-6">
              {activeTab === 'rules' && (
                <div>
                  {rules.length === 0 ? (
                    <p className="text-ink-300 text-center py-8">No alert rules created yet</p>
                  ) : (
                    <div className="space-y-3">
                      {rules.map((rule) => (
                        <AlertRow
                          key={rule.id}
                          rule={rule}
                          onToggle={handleToggleRule}
                          onDelete={handleDeleteRule}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'alerts' && (
                <AlertList alerts={alerts} />
              )}
            </div>
          </div>

          {/* Info Panel */}
          <div className="mt-6 bg-ink-800 border border-white/10 rounded-apple-md p-6">
            <h3 className="font-semibold text-ink-50 mb-3">How Monitoring Works</h3>
            <ul className="space-y-2 text-sm text-ink-300">
              <li>
                <span className="font-semibold text-ink-100">Value Threshold:</span> Alert when a
                specified wallet receives transfers above a USD value
              </li>
              <li>
                <span className="font-semibold text-ink-100">Counterparty:</span> Alert when a
                wallet interacts with a specific address
              </li>
              <li>
                <span className="font-semibold text-ink-100">Label Match:</span> Alert when a
                wallet interacts with any address carrying a specific label (mixer, cex, etc.)
              </li>
              <li className="pt-2 border-t border-white/10">
                Alerts are triggered via Alchemy Webhooks and streamed in real-time. Integrates
                with Discord and Telegram for notifications.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
