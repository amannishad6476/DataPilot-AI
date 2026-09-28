export type StepType =
  | 'input'
  | 'ai_planning'
  | 'source_discovery'
  | 'extraction'
  | 'transformation'
  | 'validation'
  | 'deduplication'
  | 'merge'
  | 'output';

export interface FieldSpec {
  name: string;
  type: string;
  required: boolean;
  description?: string;
}

export interface SourceSpec {
  id: string;
  type: string;
  name: string;
  purpose: string;
  allowed_public_only: boolean;
  connector_id?: string;
  target_url?: string;
}

export interface ValidationRuleSpec {
  field: string;
  rule_type: string;
  description: string;
  severity: 'error' | 'warning';
  params?: Record<string, any>;
}

export interface WorkflowStepPlan {
  id: string;
  type: StepType;
  name: string;
  description: string;
  depends_on: string[];
  action: string;
  target_fields: string[];
  estimated_duration_sec: number;
}

export interface PlannerOutput {
  goal: string;
  domain: string;
  target_record_count: number;
  entities: string[];
  fields: FieldSpec[];
  sources: SourceSpec[];
  steps: WorkflowStepPlan[];
  validation_rules: ValidationRuleSpec[];
  deduplication_strategy: string;
  deduplication_keys: string[];
  output_format: string;
}

export interface WorkflowResponse {
  id: string;
  prompt: string;
  plan: PlannerOutput;
  created_at: string;
  run_count: number;
  latest_run_id?: string | null;
  latest_status?: string | null;
}

export interface StepExecutionStatus {
  step_id: string;
  step_name: string;
  step_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress_percent: number;
  message: string;
  records_produced: number;
  started_at?: string | null;
  completed_at?: string | null;
  error?: string | null;
}

export interface WorkflowRunStatus {
  run_id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  execution_mode: 'demo' | 'real' | 'n8n';
  total_records: number;
  valid_records: number;
  duplicate_records: number;
  progress_percent: number;
  current_step_id?: string | null;
  step_statuses: StepExecutionStatus[];
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface EvidenceItem {
  id: string;
  field_name: string;
  source_url: string;
  snippet: string;
  confidence: number;
  collected_at: string;
}

export interface RecordItem {
  id: string;
  data: Record<string, any>;
  is_valid: boolean;
  confidence_score: number;
  validation_errors: string[];
  deduplicated_with?: string | null;
  evidence_items: EvidenceItem[];
  created_at: string;
}

export interface DatasetResponse {
  run_id: string;
  workflow_id: string;
  prompt: string;
  goal: string;
  execution_mode: string;
  total_records: number;
  valid_records: number;
  duplicate_records: number;
  fields: FieldSpec[];
  records: RecordItem[];
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ConnectorDescriptor {
  connector_id: string;
  name: string;
  description: string;
  source_type: string;
  capabilities: string[];
  allowed_domains: string[];
  rate_limit_per_minute: number;
  supports_search: boolean;
  supports_fetch: boolean;
  supports_structured_data: boolean;
  health_status: 'active' | 'degraded' | 'offline';
}
