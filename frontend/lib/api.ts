import {
  TraceResult,
  ProfileResult,
  AlertRule,
  AlertEvent,
  ReportData,
  Label,
  Chain,
} from './types';

const BACKEND_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
// Backend mounts routes under /api/v1 (see backend/main.py); /health stays at root.
const API_PREFIX = '/api/v1';
const BACKEND_URL = `${BACKEND_BASE}${API_PREFIX}`;

// Aligned with backend Pydantic models in backend/models/{trace,wallet,alert}.py
interface TraceRequest {
  seed_address: string;
  chain: Chain;
  max_hops?: number;
  min_value_usd?: number;
  label?: string;
}

interface ProfileRequest {
  address: string;
  chain: Chain;
}

interface AlertRuleRequest {
  rule_id?: string;
  address: string;
  chain: Chain;
  min_value_usd?: number;
  label_filter?: string;
  discord_webhook?: string;
  telegram_chat_id?: string;
  active?: boolean;
}

class ApiClient {
  private async fetch<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${BACKEND_URL}${path}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API error: ${response.status} ${error}`);
    }

    return response.json();
  }

  async startTrace(req: TraceRequest): Promise<{ job_id: string }> {
    return this.fetch('/trace', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async getTrace(jobId: string): Promise<TraceResult> {
    return this.fetch(`/trace/${jobId}`);
  }

  async startProfile(req: ProfileRequest): Promise<{ job_id: string }> {
    return this.fetch('/profile', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async getProfile(address: string, chain: Chain): Promise<ProfileResult> {
    return this.fetch(`/profile/${address}?chain=${chain}`);
  }

  async getLabel(address: string): Promise<Label[]> {
    return this.fetch(`/labels/${address}`);
  }

  async createAlert(rule: AlertRuleRequest): Promise<{ rule_id: string }> {
    // Backend AlertRule requires created_at — fill in client-side.
    const body = {
      rule_id: rule.rule_id ?? '',
      address: rule.address,
      chain: rule.chain,
      min_value_usd: rule.min_value_usd ?? 0,
      label_filter: rule.label_filter ?? null,
      discord_webhook: rule.discord_webhook ?? null,
      telegram_chat_id: rule.telegram_chat_id ?? null,
      created_at: new Date().toISOString(),
      active: rule.active ?? true,
    };
    return this.fetch('/monitor', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async listAlerts(): Promise<AlertEvent[]> {
    return this.fetch('/monitor/alerts');
  }

  // Note: backend has no PATCH/DELETE /monitor/{rule_id} routes yet — these are no-ops on the client.
  async updateAlert(_ruleId: string, _enabled: boolean): Promise<AlertRule> {
    throw new Error('Update alert: backend route not implemented yet');
  }

  async deleteAlert(_ruleId: string): Promise<void> {
    throw new Error('Delete alert: backend route not implemented yet');
  }

  async generateReport(jobId: string): Promise<ReportData> {
    return this.fetch(`/report/${jobId}`, {
      method: 'POST',
    });
  }

  async getReport(reportId: string): Promise<ReportData> {
    return this.fetch(`/report/${reportId}`);
  }

  async health(): Promise<{ status: string }> {
    // /health is at the root, not under /api/v1.
    const response = await fetch(`${BACKEND_BASE}/health`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
  }
}

export const apiClient = new ApiClient();
