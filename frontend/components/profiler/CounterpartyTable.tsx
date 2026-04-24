import { AddressChip } from '../shared/AddressChip';
import { CounterpartyInfo } from '@/lib/types';
import { formatUsd, formatDate } from '@/lib/format';

interface CounterpartyTableProps {
  counterparties: CounterpartyInfo[];
}

export function CounterpartyTable({ counterparties }: CounterpartyTableProps) {
  if (counterparties.length === 0) {
    return (
      <div className="bg-ink-800 border border-white/10 rounded-apple-md p-6 text-center text-ink-300">
        No counterparties recorded
      </div>
    );
  }

  return (
    <div className="bg-ink-800 border border-white/10 rounded-apple-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 bg-ink-900">
              <th className="text-left p-4 text-ink-200 font-semibold">Address</th>
              <th className="text-right p-4 text-ink-200 font-semibold">Interactions</th>
              <th className="text-right p-4 text-ink-200 font-semibold">Total Value</th>
              <th className="text-right p-4 text-ink-200 font-semibold">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {counterparties.map((cp, idx) => (
              <tr
                key={idx}
                className="border-b border-white/10 hover:bg-white/5/50 transition-colors"
              >
                <td className="p-4">
                  <AddressChip address={cp.address} chain="eth" label={cp.label} />
                </td>
                <td className="p-4 text-right text-ink-100">{cp.interaction_count}</td>
                <td className="p-4 text-right text-ink-100">
                  {formatUsd(cp.total_value_usd)}
                </td>
                <td className="p-4 text-right text-ink-300 text-xs">
                  {formatDate(cp.last_interaction)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
