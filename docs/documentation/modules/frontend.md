# Frontend Module

**Location:** `frontend/`

## Purpose

Next.js 14 app with TypeScript. Cytoscape.js transaction graph visualization. Real-time monitoring dashboard. Apple-style design via Tailwind config. Progressive disclosure of risk signals and clustering relationships.

## Architecture

```
frontend/
├─ app/
│  ├─ layout.tsx          # Root layout + Nav
│  ├─ page.tsx            # Homepage (search / quick actions)
│  ├─ trace/
│  │  └─ [id]/
│  │     └─ page.tsx      # Investigation result + graph
│  ├─ profile/
│  │  └─ [addr]/
│  │     └─ page.tsx      # Wallet profile + risk card
│  ├─ monitor/
│  │  └─ page.tsx         # Alert dashboard + rule editor
│  └─ report/
│     └─ [id]/
│        └─ page.tsx      # Shareable AI-generated report
├─ components/
│  ├─ graph/              # Cytoscape wrapper + controls
│  ├─ profiler/           # Risk card + counterparty table
│  ├─ tracer/             # Hop timeline + terminal summary
│  ├─ alerts/             # Alert list + rule editor
│  └─ shared/             # Reusable (AddressChip, ChainBadge, LabelPill, etc.)
├─ lib/
│  ├─ api.ts              # Backend HTTP client
│  ├─ ws.ts               # WebSocket monitor stream
│  ├─ format.ts           # Formatting helpers (address, number, date)
│  └─ types.ts            # TypeScript interfaces
├─ tailwind.config.ts     # Apple design tokens
├─ globals.css            # Global styles + animations
└─ tsconfig.json          # TS config
```

## Public API

### `lib/api.ts`

**`ApiClient`** singleton with methods:

```typescript
async startTrace(req: TraceRequest): Promise<{job_id: string}>
async getTrace(jobId: string): Promise<TraceResult>
async startProfile(req: ProfileRequest): Promise<{job_id: string}>
async getProfile(address: string, chain: Chain): Promise<ProfileResult>
async getLabel(address: string): Promise<Label[]>
async createAlert(rule: AlertRuleRequest): Promise<AlertRule>
async listAlerts(): Promise<AlertEvent[]>
async updateAlert(ruleId: string, enabled: boolean): Promise<AlertRule>
async deleteAlert(ruleId: string): Promise<void>
async generateReport(jobId: string): Promise<ReportData>
async getReport(reportId: string): Promise<ReportData>
async health(): Promise<{status: string}>
```

**Backend URL:** `process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'`

### `lib/ws.ts`

**WebSocket client for real-time alerts:**

```typescript
class WSMonitor {
  async connect(url: string)
  subscribe(channel: string, callback: (msg: any) => void)
  unsubscribe(channel: string)
  close()
}
```

**Channels:**
- `trace:{job_id}:stream` — hop updates during trace
- `alerts:new` — new alert triggered

### `lib/types.ts`

**Core types:**
```typescript
type Chain = 'ethereum' | 'polygon' | 'arbitrum' | 'base' | 'bsc' | 'solana'

interface TraceResult {
  seed: string
  chain: Chain
  nodes: HopNode[]
  edges: OutflowEdge[]
  terminals: Terminal[]
  visited_count: number
  truncated: boolean
}

interface ProfileResult {
  address: string
  chain: Chain
  risk_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  behavior_tags: string[]
  mixer_interactions: number
  top_counterparties: CounterpartyEntry[]
}

interface AlertRule {
  id: string
  address?: string
  rule_type: 'address' | 'value' | 'label'
  rule_value: string
  min_value_usd?: number
  enabled: boolean
}

interface AlertEvent {
  id: string
  rule_id: string
  timestamp: number
  triggered_on: string  // address that triggered
  description: string
}
```

## Design System

### `tailwind.config.ts`

**Apple palette (SF Pro typography + spacing):**
- `fontFamily.sans` — Apple system fonts (SF Pro Text, Inter fallback)
- `fontFamily.display` — SF Pro Display (headlines)
- `fontFamily.mono` — SF Mono (code)

**Colors (ink + semantic):**
- `ink.*` — grayscale (#1d1d1f to #f5f5f7)
- `apple.blue` — action color (#0071e3)
- `emerald.5xx` — positive (success, buy)
- `amber.5xx` — warning (medium risk)
- `rose.4xx` — negative (danger, high risk)

**Shadows (layered elevation):**
- `apple-sm` — 1px, 2px offsets (cards, badges)
- `apple` — 4px, 16px (default elevation)
- `apple-lg` — 12px, 40px (modals)
- `apple-hi` — 24px, 60px (floating panels)

**Border radius:**
- `apple-sm` — 5px (small badges)
- `apple` — 12px (default)
- `apple-md` — 18px (larger cards)
- `apple-lg` → `apple-xl` — 28px–36px (hero sections)
- `apple-pill` — 980px (fully rounded buttons)

**Animations:**
- `fade-up` — 600ms cubic-bezier (entrance)
- `gradient-x` — 12s infinite (shimmer)
- Transition timing: `cubic-bezier(0.28, 0.11, 0.32, 1)` (Apple curve)

### `globals.css`

Root styles, CSS variables, custom animations.

## Components Organization

### `components/graph/`

**`TraceGraph.tsx`** — Cytoscape.js wrapper.
- Renders transaction graph from TraceResult.nodes + edges
- Node types: wallet (circle), terminal (rectangle), mixer exit (diamond)
- Edge styling by terminal type (color, dash pattern)
- Interactive: click node → show details, hover edge → value tooltip
- Zoom/pan/fit controls

**`GraphControls.tsx`** — Toolbar above graph.
- Zoom in/out, fit to view, reset layout
- Filter: show/hide terminals, show/hide low-value edges
- Export: PNG, SVG, JSON

**`GraphLegend.tsx`** — Key explaining node/edge colors and shapes.

### `components/profiler/`

**`RiskCard.tsx`** — Large risk score badge.
- Score 0–100 with color (emerald/amber/rose)
- Level label (low/medium/high/critical)
- Mini signal breakdown below

**`SignalList.tsx`** — Per-signal evidence.
- Signal name, weight, triggered (bool), evidence text
- Indented list, checkmark/x icon

**`CounterpartyTable.tsx`** — Top 10 counterparties.
- Columns: address (with chip), label, direction (in/out/both), value_usd, tx_count
- Sortable by value or count

**`BehaviorTags.tsx`** — Pill badges for inferred tags.
- Examples: airdrop_farmer, mev_bot, exchange_user
- Clickable → filter graph or show examples

### `components/tracer/`

**`HopTimeline.tsx`** — Vertical timeline of hops.
- Each hop: depth, wallet address (chip), terminal type (if any)
- Lines connecting hops
- On hover: highlight corresponding nodes in graph

**`TerminalSummary.tsx`** — Destination summary (stubs as JSON).
- Terminal type icon + label
- Value, block, timestamp
- Actions: view on Etherscan, mark as known, etc.

### `components/alerts/`

**`AlertList.tsx`** — List of registered rules + recent events.
- Table: rule description, enabled toggle, delete button
- Sub-rows: recent trigger events with timestamp

**`RuleEditor.tsx`** — Modal form to create/edit alert rules.
- Dropdown: address / value / label
- Input: rule value (address, USD threshold, label keyword)
- Toggle: enabled

**`AlertRow.tsx`** — Single row in AlertList (reusable).

### `components/shared/`

**`AddressChip.tsx`** — Wallet address display.
- Truncated (0x1234...abcd) or full
- Copy-to-clipboard button
- Color per chain
- Clickable → navigate to profile page

**`ChainBadge.tsx`** — Chain name badge.
- Ethereum → blue, Polygon → purple, etc.
- Icon + text label

**`LabelPill.tsx`** — Label badge.
- Label text, background color per label type (cex→green, mixer→red, etc.)
- Optional: source indicator (hardcoded, community, etherscan)

**`RiskBadge.tsx`** — Risk level (low/medium/high/critical).
- Color + text
- Optionally expandable to show signals

**`Nav.tsx`** — Top navigation bar.
- Logo + title
- Search bar (address or tx hash)
- Links: Home, Monitor, Docs
- User menu (if auth enabled)

## Page Routes

**`app/page.tsx`** — Homepage.
- Hero: "Investigate blockchain fund flow"
- Search form: address / tx / block input
- Quick actions: Profile, Trace, Monitor
- Example searches (known hacks)

**`app/trace/[id]/page.tsx`** — Trace result.
- Header: seed, chain, status (pending/complete/error)
- Main: TraceGraph (center), HopTimeline (left sidebar), TerminalSummary (right)
- Action buttons: Generate Report, Share

**`app/profile/[addr]/page.tsx`** — Wallet profile.
- Header: address chip, chain badge, risk card
- Main: RiskCard (left), CounterpartyTable + BehaviorTags (right)
- Action buttons: Cluster, Trace, Monitor

**`app/monitor/page.tsx`** — Alert dashboard.
- Header: "Real-time Monitoring"
- Main: AlertList (registered rules + recent events)
- Sidebar: RuleEditor (button to open modal)
- Real-time: WebSocket to alerts:new channel

**`app/report/[id]/page.tsx`** — Shareable report.
- Header: incident name, date, status
- Main: AI-generated prose (trace_report, profile_summary, cluster_explanation)
- Sidebar: metadata (addresses involved, total value, chains)
- Footer: report ID, generated timestamp, (optional) password-protected share link

## Data Flow

```
User → Search form → apiClient.startTrace()
├─ POST /trace → backend enqueues RQ job
├─ backend returns job_id
├─ frontend navigates to /trace/[job_id]
└─ /trace/[job_id] page polls GET /trace/[job_id] every 2s
   ├─ while status=pending: show spinner
   ├─ on status=complete: fetch TraceResult
   ├─ subscribe to WS trace:[job_id]:stream for live hop updates (optional)
   └─ render TraceGraph + HopTimeline

Clustering UI overlay:
├─ Cluster data fetched from API
├─ Nodes colored by cluster membership
├─ Edges labeled with heuristic type (common_funder, fingerprint, etc.)
└─ Hover heuristic edge → show confidence score + evidence
```

## Testing Guidance

**Component tests (Jest + React Testing Library):**
- Render `RiskCard` with score → verify color + level text
- Render `CounterpartyTable` → verify columns + sort
- Render `AddressChip` → verify truncation + copy button
- Render `TraceGraph` with nodes/edges → verify graph renders

**Page tests:**
- Navigate to `/trace/123` → fetch mocked TraceResult → render page
- Click on counterparty row → navigate to profile page
- Click "Generate Report" → POST /report/job_id → navigate to /report/report_id

**E2E (Cypress/Playwright):**
- Search for address → trace starts → graph loads
- Monitor page → create alert rule → trigger alert via WS → alert appears in list
- Profile page → generate report → share link works

## Known Gaps & TODOs

- `components/tracer/` — HopTimeline and TerminalSummary likely incomplete/stubs
- `app/monitor/page.tsx` — real-time WebSocket integration may be partial
- `app/report/[id]/page.tsx` — report rendering may not be fully implemented
- No dark mode toggle (Apple design has light + dark variants)
- No accessibility audit (contrast, keyboard nav, screen reader)
- No error boundary for graph rendering failures
- Cluster UI overlay not mentioned in visible components

## See Also

- `ai.md` — generates prose for `/report` pages
- `tracer.md`, `profiler.md` — data sources for graph and profile pages
- `lib/api.ts` — HTTP client for all page requests
