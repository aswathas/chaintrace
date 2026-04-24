import { AlertRule } from '@/lib/types';
import { formatDate } from '@/lib/format';

interface AlertRowProps {
  rule: AlertRule;
  onToggle?: (ruleId: string, enabled: boolean) => void;
  onDelete?: (ruleId: string) => void;
}

export function AlertRow({ rule, onToggle, onDelete }: AlertRowProps) {
  return (
    <div className="bg-ink-800 border border-white/10 rounded-apple-md p-4 flex items-center justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-3 mb-2">
          <input
            type="checkbox"
            checked={rule.enabled}
            onChange={(e) => onToggle?.(rule.id, e.target.checked)}
            className="w-4 h-4 rounded-apple border-white/10 bg-white/5 cursor-pointer"
          />
          <span className="text-xs font-semibold bg-white/5 px-2 py-1 rounded-apple text-ink-200">
            {rule.rule_type.toUpperCase()}
          </span>
          <code className="text-sm text-ink-100 font-mono">{rule.address.slice(0, 10)}...</code>
        </div>
        <p className="text-xs text-ink-300 ml-7">
          {rule.rule_type === 'value' && rule.min_value_usd
            ? `Alert when value > $${rule.min_value_usd.toLocaleString()}`
            : rule.rule_value}
        </p>
        <p className="text-xs text-ink-400 ml-7">Created: {formatDate(rule.created_at)}</p>
      </div>
      <button
        onClick={() => onDelete?.(rule.id)}
        className="p-2 hover:bg-red-600 rounded-apple transition-colors text-ink-300 hover:text-white"
        title="Delete rule"
      >
        ✕
      </button>
    </div>
  );
}
