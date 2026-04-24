import { chainColor, chainLabel } from '@/lib/format';
import { Chain } from '@/lib/types';

interface ChainBadgeProps {
  chain: Chain;
  size?: 'sm' | 'md' | 'lg';
}

export function ChainBadge({ chain, size = 'md' }: ChainBadgeProps) {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  return (
    <span
      className={`${chainColor(
        chain
      )} text-white font-semibold rounded-apple-md ${sizeClasses[size]} inline-block`}
    >
      {chainLabel(chain)}
    </span>
  );
}
