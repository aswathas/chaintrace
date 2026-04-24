import { TraceEdge } from '@/lib/types';
import { formatTimestamp, formatUsd } from '@/lib/format';
import { AddressChip } from '../shared/AddressChip';

interface HopTimelineProps {
  edges: TraceEdge[];
}

export function HopTimeline({ edges }: HopTimelineProps) {
  if (edges.length === 0) {
    return (
      <div className="text-ink-300 text-sm">No hops recorded</div>
    );
  }

  const sorted = [...edges].sort((a, b) => a.timestamp - b.timestamp);

  return (
    <div className="space-y-4">
      {sorted.map((edge, idx) => (
        <div key={idx} className="border-l-2 border-emerald-600 pl-4 pb-4">
          <div className="flex items-start justify-between mb-2">
            <div>
              <p className="text-xs text-ink-300">Hop {idx + 1}</p>
              <p className="text-xs text-ink-400 font-mono">{edge.tx_hash.slice(0, 16)}...</p>
            </div>
            <span className="text-sm font-semibold text-apple-blueBright">
              {formatUsd(edge.value_usd)}
            </span>
          </div>
          <div className="text-xs text-ink-300 mb-2">
            {formatTimestamp(edge.timestamp)}
          </div>
          <div className="space-y-1 text-xs">
            <div>
              <span className="text-ink-400">From: </span>
              <AddressChip address={edge.from} chain={edge.chain} copyable={false} />
            </div>
            <div>
              <span className="text-ink-400">To: </span>
              <AddressChip address={edge.to} chain={edge.chain} copyable={false} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
