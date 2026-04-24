import { labelSourceColor, confidencePercent } from '@/lib/format';
import { Label } from '@/lib/types';

interface LabelPillProps {
  label: Label;
  showSource?: boolean;
  showConfidence?: boolean;
}

export function LabelPill({
  label,
  showSource = true,
  showConfidence = true,
}: LabelPillProps) {
  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-sm ${labelSourceColor(
        label.source
      )}`}
    >
      <span className="font-medium">{label.name}</span>
      {showSource && <span className="opacity-70 text-xs">({label.source})</span>}
      {showConfidence && (
        <span className="opacity-70 text-xs">{confidencePercent(label.confidence)}</span>
      )}
    </div>
  );
}
