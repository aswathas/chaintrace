import { AddressChip } from '../shared/AddressChip';
import { ChainBadge } from '../shared/ChainBadge';
import { formatDate } from '@/lib/format';
import { Chain } from '@/lib/types';

interface TraceHeaderProps {
  seed: string;
  chain: Chain;
  hopsCount: number;
  createdAt: number;
  nodesCount: number;
}

export function TraceHeader({
  seed,
  chain,
  hopsCount,
  createdAt,
  nodesCount,
}: TraceHeaderProps) {
  return (
    <div className="bg-gradient-to-r from-slate-800 to-slate-900 border border-white/10 rounded-apple-md p-6 mb-6">
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-50 mb-2">Hack Trace</h1>
          <p className="text-sm text-ink-300">Fund flow analysis starting from seed address</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-ink-400 uppercase font-semibold mb-1">Seed Address</p>
            <AddressChip address={seed} chain={chain} copyable={false} />
          </div>
          <div>
            <p className="text-xs text-ink-400 uppercase font-semibold mb-1">Chain</p>
            <ChainBadge chain={chain} />
          </div>
          <div>
            <p className="text-xs text-ink-400 uppercase font-semibold mb-1">Hops</p>
            <span className="text-lg font-bold text-apple-blueBright">{hopsCount}</span>
          </div>
          <div>
            <p className="text-xs text-ink-400 uppercase font-semibold mb-1">Wallets</p>
            <span className="text-lg font-bold text-apple-blueBright">{nodesCount}</span>
          </div>
        </div>

        <div className="text-xs text-ink-300">
          Trace created: {formatDate(createdAt)}
        </div>
      </div>
    </div>
  );
}
