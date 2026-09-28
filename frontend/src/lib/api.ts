import {
  WorkflowResponse,
  WorkflowRunStatus,
  DatasetResponse,
  EvidenceItem,
  ConnectorDescriptor,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private async fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(options?.headers || {}),
        },
      });

      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData?.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // ignore
        }
        throw new Error(errorMsg);
      }

      return await response.json();
    } catch (err: any) {
      console.error(`API Request Failed: ${endpoint}`, err);
      throw err;
    }
  }

  // Workflows
  async planWorkflow(prompt: string, targetCount: number = 30): Promise<WorkflowResponse> {
    return this.fetchJson<WorkflowResponse>('/workflows/plan', {
      method: 'POST',
      body: JSON.stringify({ prompt, target_record_count: targetCount }),
    });
  }

  async getWorkflow(workflowId: string): Promise<WorkflowResponse> {
    return this.fetchJson<WorkflowResponse>(`/workflows/${workflowId}`);
  }

  async listWorkflows(): Promise<WorkflowResponse[]> {
    return this.fetchJson<WorkflowResponse[]>('/workflows');
  }

  async deleteWorkflow(workflowId: string): Promise<void> {
    await fetch(`${API_BASE_URL}/workflows/${workflowId}`, { method: 'DELETE' });
  }

  // Execution
  async runWorkflow(
    workflowId: string,
    executionMode: 'demo' | 'real' | 'n8n' = 'demo',
    options?: { target_url?: string; n8n_webhook_url?: string }
  ): Promise<WorkflowRunStatus> {
    return this.fetchJson<WorkflowRunStatus>(`/workflows/${workflowId}/run`, {
      method: 'POST',
      body: JSON.stringify({
        execution_mode: executionMode,
        target_url: options?.target_url || undefined,
        n8n_webhook_url: options?.n8n_webhook_url || undefined,
      }),
    });
  }

  async getRunStatus(runId: string): Promise<WorkflowRunStatus> {
    return this.fetchJson<WorkflowRunStatus>(`/runs/${runId}`);
  }

  // Connectors & n8n
  async listConnectors(): Promise<ConnectorDescriptor[]> {
    return this.fetchJson<ConnectorDescriptor[]>('/connectors');
  }

  async checkConnectorHealth(connectorId: string): Promise<any> {
    return this.fetchJson<any>(`/connectors/${connectorId}/health`);
  }

  async getN8nTemplate(): Promise<any> {
    return this.fetchJson<any>('/connectors/n8n/template');
  }

  // Dataset
  async getDataset(
    runId: string,
    params?: {
      search?: string;
      valid_filter?: string;
      sort_by?: string;
      sort_order?: string;
      page?: number;
      page_size?: number;
    }
  ): Promise<DatasetResponse> {
    const query = new URLSearchParams();
    if (params?.search) query.set('search', params.search);
    if (params?.valid_filter) query.set('valid_filter', params.valid_filter);
    if (params?.sort_by) query.set('sort_by', params.sort_by);
    if (params?.sort_order) query.set('sort_order', params.sort_order);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.page_size) query.set('page_size', params.page_size.toString());

    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.fetchJson<DatasetResponse>(`/runs/${runId}/dataset${qs}`);
  }

  async getRecordEvidence(recordId: string): Promise<EvidenceItem[]> {
    return this.fetchJson<EvidenceItem[]>(`/records/${recordId}/evidence`);
  }

  getExportCsvUrl(runId: string): string {
    return `${API_BASE_URL}/runs/${runId}/export/csv`;
  }

  getExportJsonUrl(runId: string): string {
    return `${API_BASE_URL}/runs/${runId}/export/json`;
  }
}

export const api = new ApiClient();
