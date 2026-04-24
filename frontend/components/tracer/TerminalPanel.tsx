import { terminalTypeColor } from '@/lib/format';
import { AddressChip } from '../shared/AddressChip';

interface Terminal {
  address: string;
  terminal_type: string;
  confidence: number;
}

interface TerminalPanelProps {
  terminals: Terminal[];
}

export function TerminalPanel({ terminals }: TerminalPanelProps) {
  if (terminals.length === 0) {
    return (
      <div className="bg-ink-800 border border-white/10 rounded-apple-md p-6 text-center text-ink-300">
        No terminals detected
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-ink-50">Terminals</h3>
      {terminals.map((term, idx) => (
        <div
          key={idx}
          className="bg-ink-800 border border-white/10 rounded-apple-md p-4"
        >
          <div className="flex items-start justify-between mb-3">
            <div
              className="px-3 py-1 rounded-apple text-xs font-semibold text-white"
              style={{ backgroundColor: terminalTypeColor(term.terminal_type) }}
            >
              {term.terminal_type.toUpperCase()}
            </div>
            <span className="text-xs bg-white/5 px-2 py-1 rounded-apple text-ink-200">
              {Math.round(term.confidence * 100)}% confidence
            </span>
          </div>
          <AddressChip address={term.address} chain="eth" />
        </div>
      ))}
    </div>
  );
}
