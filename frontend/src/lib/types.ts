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
  reasoning?: string[];
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

export interface TimelineEvent {
  id: string;
  timestamp: string;
  step_id?: string | null;
  level: 'info' | 'warning' | 'error' | 'success';
  stage: string;
  message: string;
  details?: Record<string, any> | null;
}

export interface DataQualitySummary {
  total_evaluated: number;
  valid_count: number;
  valid_rate_percent: number;
  field_completion_rates: Record<string, number>;
  confidence_breakdown: Record<string, number>;
  average_confidence: number;
  evidence_coverage_percent: number;
  deduplication_reduction_percent: number;
  issues_found: string[];
}

export interface SourceHealthItem {
  connector_id: string;
  name: string;
  source_type: string;
  status: 'HEALTHY' | 'DEGRADED' | 'UNAVAILABLE' | 'UNTESTED';
  total_requests: number;
  success_count: number;
  error_count: number;
  avg_latency_ms: number;
  last_attempt_at?: string | null;
  last_status_code?: number | null;
  details: string;
}

export interface SourceHealthReport {
  timestamp: string;
  overall_status: string;
  connectors: SourceHealthItem[];
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
  execution_timeline?: TimelineEvent[];
  quality_summary?: DataQualitySummary | null;
  source_health_summary?: SourceHealthReport | null;
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
  confidence_level?: 'HIGH' | 'MEDIUM' | 'LOW';
  evidence_status?: 'AVAILABLE' | 'PARTIAL' | 'MISSING';
  field_validations?: Record<string, 'VALID' | 'INVALID' | 'MISSING' | 'NEEDS_REVIEW'>;
  field_transformations?: Record<string, string[]>;
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
  quality_summary?: DataQualitySummary | null;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RunComparisonResponse {
  run_a_id: string;
  run_b_id: string;
  run_a_mode: string;
  run_b_mode: string;
  run_a_status: string;
  run_b_status: string;
  run_a_date?: string | null;
  run_b_date?: string | null;
  total_records_delta: number;
  valid_records_delta: number;
  duplicate_records_delta: number;
  average_confidence_a: number;
  average_confidence_b: number;
  confidence_delta: number;
  new_records_count: number;
  common_records_count: number;
  removed_records_count: number;
  summary: string;
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
