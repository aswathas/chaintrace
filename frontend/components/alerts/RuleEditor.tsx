'use client';

import { useState } from 'react';
import { Chain } from '@/lib/types';

interface RuleEditorProps {
  onSubmit?: (data: {
    address: string;
    chain: Chain;
    rule_type: 'address' | 'value' | 'label';
    rule_value: string;
    min_value_usd?: number;
  }) => void;
  isLoading?: boolean;
}

export function RuleEditor({ onSubmit, isLoading = false }: RuleEditorProps) {
  const [address, setAddress] = useState('');
  const [chain, setChain] = useState<Chain>('eth');
  const [ruleType, setRuleType] = useState<'address' | 'value' | 'label'>('value');
  const [ruleValue, setRuleValue] = useState('');
  const [minValue, setMinValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.({
      address,
      chain,
      rule_type: ruleType,
      rule_value: ruleValue,
      min_value_usd: minValue ? parseInt(minValue) : undefined,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-ink-800 border border-white/10 rounded-apple-md p-6 space-y-4"
    >
      <div>
        <label className="block text-sm font-medium text-ink-100 mb-2">
          Watch Address
        </label>
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="0x..."
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-apple text-ink-50 placeholder-ink-300 focus:border-apple-blue outline-none"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-ink-100 mb-2">
          Chain
        </label>
        <select
          value={chain}
          onChange={(e) => setChain(e.target.value as Chain)}
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-apple text-ink-50 focus:border-apple-blue outline-none"
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
          Rule Type
        </label>
        <select
          value={ruleType}
          onChange={(e) => setRuleType(e.target.value as 'address' | 'value' | 'label')}
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-apple text-ink-50 focus:border-apple-blue outline-none"
        >
          <option value="value">Value Threshold</option>
          <option value="address">Counterparty Address</option>
          <option value="label">Label Match</option>
        </select>
      </div>

      {ruleType === 'value' && (
        <div>
          <label className="block text-sm font-medium text-ink-100 mb-2">
            Alert if value exceeds (USD)
          </label>
          <input
            type="number"
            value={minValue}
            onChange={(e) => setMinValue(e.target.value)}
            placeholder="1000"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-apple text-ink-50 placeholder-ink-300 focus:border-apple-blue outline-none"
          />
        </div>
      )}

      {ruleType !== 'value' && (
        <div>
          <label className="block text-sm font-medium text-ink-100 mb-2">
            {ruleType === 'address' ? 'Counterparty Address' : 'Label Pattern'}
          </label>
          <input
            type="text"
            value={ruleValue}
            onChange={(e) => setRuleValue(e.target.value)}
            placeholder={ruleType === 'address' ? '0x...' : 'mixer, cex, exploit...'}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-apple text-ink-50 placeholder-ink-300 focus:border-apple-blue outline-none"
          />
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading || !address}
        className="w-full px-4 py-2 bg-apple-blue hover:bg-apple-blueDark disabled:bg-white/5 text-white font-semibold rounded-apple transition-colors"
      >
        {isLoading ? 'Creating...' : 'Create Alert Rule'}
      </button>
    </form>
  );
}
