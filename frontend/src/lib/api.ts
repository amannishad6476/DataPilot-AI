import {
  WorkflowResponse,
  WorkflowRunStatus,
  DatasetResponse,
  EvidenceItem,
  ConnectorDescriptor,
  TimelineEvent,
  DataQualitySummary,
  RunComparisonResponse,
  SourceHealthReport,
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
      if (err.name === 'TypeError' && (err.message === 'Failed to fetch' || err.message.includes('fetch'))) {
        const netErr = new Error(
          `Cannot connect to DataPilot backend at ${API_BASE_URL}. Please ensure the FastAPI server is running on port 8000 (run "python run.py" in backend/).`
        );
        console.error(`API Request Failed: ${endpoint}`, netErr);
        throw netErr;
      }
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

  async listWorkflowRuns(workflowId: string): Promise<WorkflowRunStatus[]> {
    return this.fetchJson<WorkflowRunStatus[]>(`/workflows/${workflowId}/runs`);
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

  async rerunWorkflow(runId: string): Promise<WorkflowRunStatus> {
    return this.fetchJson<WorkflowRunStatus>(`/runs/${runId}/rerun`, {
      method: 'POST',
    });
  }

  async cancelWorkflow(runId: string): Promise<WorkflowRunStatus> {
    return this.fetchJson<WorkflowRunStatus>(`/runs/${runId}/cancel`, {
      method: 'POST',
    });
  }

  async listRuns(): Promise<WorkflowRunStatus[]> {
    return this.fetchJson<WorkflowRunStatus[]>('/runs');
  }

  async getRunStatus(runId: string): Promise<WorkflowRunStatus> {
    return this.fetchJson<WorkflowRunStatus>(`/runs/${runId}`);
  }

  async getRunTimeline(runId: string): Promise<TimelineEvent[]> {
    return this.fetchJson<TimelineEvent[]>(`/runs/${runId}/timeline`);
  }

  async getRunQuality(runId: string): Promise<DataQualitySummary> {
    return this.fetchJson<DataQualitySummary>(`/runs/${runId}/quality`);
  }

  async compareRuns(runA: string, runB: string): Promise<RunComparisonResponse> {
    return this.fetchJson<RunComparisonResponse>(`/runs/compare?run_a=${encodeURIComponent(runA)}&run_b=${encodeURIComponent(runB)}`);
  }

  // Connectors & Source Health
  async listConnectors(): Promise<ConnectorDescriptor[]> {
    return this.fetchJson<ConnectorDescriptor[]>('/connectors');
  }

  async getSourceHealthReport(): Promise<SourceHealthReport> {
    return this.fetchJson<SourceHealthReport>('/connectors/health');
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
      confidence_filter?: string;
      evidence_filter?: string;
      sort_by?: string;
      sort_order?: string;
      page?: number;
      page_size?: number;
    }
  ): Promise<DatasetResponse> {
    const query = new URLSearchParams();
    if (params?.search) query.set('search', params.search);
    if (params?.valid_filter) query.set('valid_filter', params.valid_filter);
    if (params?.confidence_filter) query.set('confidence_filter', params.confidence_filter);
    if (params?.evidence_filter) query.set('evidence_filter', params.evidence_filter);
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
