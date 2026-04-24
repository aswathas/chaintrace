'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = [
  { href: '/trace', label: 'Tracer' },
  { href: '/profile/0x', label: 'Profiler' },
  { href: '/monitor', label: 'Alerts' },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-50 apple-glass">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="font-display font-semibold tracking-apple-display text-white hover:text-white text-[17px]"
        >
          <span className="inline-flex items-center gap-2">
            <span className="h-5 w-5 rounded-[6px] bg-gradient-to-br from-apple-blueBright to-emerald-400" />
            ChainTrace
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          {links.map((l) => {
            const base = l.href.replace(/\/0x$/, '');
            const active = pathname === base || pathname?.startsWith(base + '/');
            return (
              <Link
                key={l.href}
                href={l.href}
                className={[
                  'px-3 py-1.5 rounded-apple-pill text-[13px] font-medium transition-colors duration-200 ease-apple',
                  active
                    ? 'bg-white/10 text-white'
                    : 'text-ink-200 hover:text-white hover:bg-white/5',
                ].join(' ')}
              >
                {l.label}
              </Link>
            );
          })}
          <Link href="/trace" className="ml-2 apple-btn-primary text-[13px] px-4 py-1.5">
            Start a trace
          </Link>
        </nav>
      </div>
    </header>
  );
}
