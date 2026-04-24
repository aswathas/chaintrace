import { RiskSignal } from '@/lib/types';

interface SignalListProps {
  signals: RiskSignal[];
  title?: string;
}

export function SignalList({ signals, title = 'Risk Signals' }: SignalListProps) {
  if (signals.length === 0) {
    return (
      <div className="text-ink-300 text-sm">No signals detected</div>
    );
  }

  const positive = signals.filter((s) => s.category === 'positive');
  const negative = signals.filter((s) => s.category === 'negative');

  return (
    <div className="space-y-4">
      {positive.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-red-400 mb-2 uppercase">
            Risk Factors
          </h4>
          <div className="space-y-1">
            {positive.map((signal, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <span className="text-ink-200">{signal.name}</span>
                <span className="text-red-400 font-semibold">+{signal.weight}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {negative.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-green-400 mb-2 uppercase">
            Mitigating Factors
          </h4>
          <div className="space-y-1">
            {negative.map((signal, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <span className="text-ink-200">{signal.name}</span>
                <span className="text-green-400 font-semibold">-{Math.abs(signal.weight)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
