import { shortAddress, chainColor, chainLabel } from '@/lib/format';
import { Chain } from '@/lib/types';

interface AddressChipProps {
  address: string;
  chain: Chain;
  label?: string;
  onClick?: () => void;
  copyable?: boolean;
}

export function AddressChip({
  address,
  chain,
  label,
  onClick,
  copyable = true,
}: AddressChipProps) {
  const handleClick = () => {
    if (copyable) {
      navigator.clipboard.writeText(address);
    }
    onClick?.();
  };

  return (
    <div
      onClick={handleClick}
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-apple-md bg-ink-800 border border-white/10 ${
        copyable ? 'cursor-pointer hover:bg-white/5' : ''
      } transition-colors`}
    >
      <span className={`${chainColor(chain)} text-white px-2 py-0.5 rounded-apple text-xs font-semibold`}>
        {chainLabel(chain)}
      </span>
      <code className="text-ink-100 font-mono text-sm">{shortAddress(address)}</code>
      {label && <span className="text-ink-300 text-xs">({label})</span>}
      {copyable && <span className="text-ink-300 text-xs">⎘</span>}
    </div>
  );
}
