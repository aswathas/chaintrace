import { RiskBadge } from '../shared/RiskBadge';
import { RiskScore } from '@/lib/types';

interface RiskCardProps {
  risk: RiskScore;
}

export function RiskCard({ risk }: RiskCardProps) {
  return (
    <div className="bg-ink-800 border border-white/10 rounded-apple-md p-6">
      <h3 className="text-lg font-semibold mb-4 text-ink-50">Risk Assessment</h3>
      <div className="mb-6">
        <RiskBadge level={risk.level} score={risk.score} size="lg" />
      </div>

      <div className="space-y-3">
        <h4 className="text-sm font-medium text-ink-200">Risk Signals</h4>
        {risk.signals.map((signal, idx) => (
          <div
            key={idx}
            className={`flex items-center justify-between p-2 rounded-apple bg-white/5 ${
              signal.category === 'positive' ? 'border-l-4 border-red-500' : 'border-l-4 border-green-500'
            }`}
          >
            <span className="text-sm text-ink-100">{signal.name}</span>
            <span
              className={`text-sm font-semibold ${
                signal.category === 'positive' ? 'text-red-400' : 'text-green-400'
              }`}
            >
              {signal.category === 'positive' ? '+' : '-'} {Math.abs(signal.weight)}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-white/10">
        <p className="text-xs text-ink-300">
          Risk score based on on-chain activity signals. Mixing indicators, known exploit wallets,
          and high-velocity transfers increase risk.
        </p>
      </div>
    </div>
  );
}
