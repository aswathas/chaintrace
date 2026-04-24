import { AlertEvent } from '@/lib/types';
import { formatTimestamp, formatUsd } from '@/lib/format';
import { AddressChip } from '../shared/AddressChip';

interface AlertListProps {
  alerts: AlertEvent[];
}

export function AlertList({ alerts }: AlertListProps) {
  if (alerts.length === 0) {
    return (
      <div className="bg-ink-800 border border-white/10 rounded-apple-md p-8 text-center text-ink-300">
        <p className="mb-2">No alerts triggered</p>
        <p className="text-xs">Create alert rules to monitor wallet activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="bg-ink-800 border border-amber-700 rounded-apple-md p-4 hover:bg-white/5/50 transition-colors"
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <span className="inline-block bg-amber-600 text-white px-2 py-1 rounded-apple text-xs font-semibold">
                ALERT
              </span>
            </div>
            <span className="text-xs text-ink-300">
              {formatTimestamp(alert.timestamp)}
            </span>
          </div>

          <div className="space-y-2 text-sm">
            <div>
              <span className="text-ink-400">Address: </span>
              <AddressChip address={alert.address} chain={alert.chain} copyable={false} />
            </div>
            <div>
              <span className="text-ink-400">Transaction: </span>
              <code className="text-apple-blueBright font-mono text-xs">
                {alert.tx_hash.slice(0, 16)}...
              </code>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-400">Value: {formatUsd(alert.value_usd)}</span>
              <span className="text-ink-400">Rule: {alert.rule_id}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
