import { terminalTypeColor } from '@/lib/format';

export function GraphLegend() {
  const types = [
    { type: 'cex', label: 'Exchange' },
    { type: 'mixer', label: 'Mixer' },
    { type: 'bridge', label: 'Bridge' },
    { type: 'cold', label: 'Cold Storage' },
    { type: 'unknown', label: 'Unknown' },
  ];

  return (
    <div className="bg-ink-800 border border-white/10 rounded-apple-md p-4">
      <h3 className="text-sm font-semibold mb-3 text-ink-50">Legend</h3>
      <div className="space-y-2">
        {types.map((item) => (
          <div key={item.type} className="flex items-center gap-2">
            <div
              className="w-5 h-5 rounded-apple border border-white/10"
              style={{ backgroundColor: terminalTypeColor(item.type) }}
            />
            <span className="text-xs text-ink-200">{item.label}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 pt-4 border-t border-white/10">
        <p className="text-xs text-ink-300">
          Edge thickness represents transaction value
        </p>
      </div>
    </div>
  );
}
