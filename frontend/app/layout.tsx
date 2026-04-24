import type { Metadata } from 'next';
import { Nav } from '@/components/shared/Nav';
import './globals.css';

export const metadata: Metadata = {
  title: 'ChainTrace — Multi-Chain Blockchain Forensics',
  description:
    'Open-source, self-hostable forensics for tracing stolen funds and profiling wallets across multiple blockchains.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        <Nav />
        <main className="min-h-[calc(100vh-56px)]">{children}</main>
        <footer className="mt-24 border-t border-white/5">
          <div className="max-w-7xl mx-auto px-6 py-12 grid md:grid-cols-3 gap-8 text-[13px]">
            <div>
              <div className="font-display text-white font-semibold tracking-apple-display">
                ChainTrace
              </div>
              <p className="mt-3 text-ink-300 leading-relaxed">
                Self-hostable, open-source blockchain forensics for security
                researchers and incident response.
              </p>
            </div>
            <div>
              <div className="apple-eyebrow mb-3">Product</div>
              <ul className="space-y-2 text-ink-200">
                <li><a href="/trace">Hack Tracer</a></li>
                <li><a href="/profile/0x">Wallet Profiler</a></li>
                <li><a href="/monitor">Alerts</a></li>
              </ul>
            </div>
            <div>
              <div className="apple-eyebrow mb-3">Project</div>
              <ul className="space-y-2 text-ink-200">
                <li><a href="https://github.com/">GitHub</a></li>
                <li><a href="/#limitations">Limitations</a></li>
                <li><a href="/#contributing">Contributing</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/5">
            <div className="max-w-7xl mx-auto px-6 py-6 text-[12px] text-ink-400 flex flex-col md:flex-row justify-between gap-2">
              <span>© {new Date().getFullYear()} ChainTrace. MIT licensed.</span>
              <span>Not a replacement for law enforcement.</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
