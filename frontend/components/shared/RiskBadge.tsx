import { riskLevelColor } from '@/lib/format';

interface RiskBadgeProps {
  level: 'low' | 'medium' | 'high' | 'critical';
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

export function RiskBadge({ level, score, size = 'md' }: RiskBadgeProps) {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const levelLabel = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    critical: 'Critical',
  };

  return (
    <span
      className={`${riskLevelColor(
        level
      )} font-semibold rounded-apple-md ${sizeClasses[size]} inline-block`}
    >
      {levelLabel[level]} ({score})
    </span>
  );
}
