import {
  TraceResult,
  ProfileResult,
  AlertRule,
  AlertEvent,
  ReportData,
  Label,
  Chain,
} from './types';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

interface TraceRequest {
  input: string;
  chain: Chain;
  max_hops?: number;
  min_value_usd?: number;
}

interface ProfileRequest {
  address: string;
  chain: Chain;
}

interface AlertRuleRequest {
  address: string;
  rule_type: 'address' | 'value' | 'label';
  rule_value: string;
  min_value_usd?: number;
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

  async createAlert(rule: AlertRuleRequest): Promise<AlertRule> {
    return this.fetch('/monitor', {
      method: 'POST',
      body: JSON.stringify(rule),
    });
  }

  async listAlerts(): Promise<AlertEvent[]> {
    return this.fetch('/monitor/alerts');
  }

  async updateAlert(
    ruleId: string,
    enabled: boolean
  ): Promise<AlertRule> {
    return this.fetch(`/monitor/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    });
  }

  async deleteAlert(ruleId: string): Promise<void> {
    await this.fetch(`/monitor/${ruleId}`, {
      method: 'DELETE',
    });
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
    return this.fetch('/health');
  }
}

export const apiClient = new ApiClient();
