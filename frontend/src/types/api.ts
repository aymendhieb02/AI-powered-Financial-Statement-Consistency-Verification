export type Project = {
  id: string;
  name: string;
  company: string;
  description: string;
  created_at: string;
};

export type ProjectDetail = Project & {
  document_count: number;
  latest_run_id?: string | null;
  latest_run_status?: string | null;
  latest_risk_score?: number | null;
  latest_confidence?: number | null;
  updated_at?: string | null;
};

export type UploadedDocument = {
  filename: string;
  size: number;
  detected_year?: number | null;
  status: string;
  path: string;
};

export type UploadResponse = {
  uploaded: UploadedDocument[];
  failed: Array<{ filename?: string; error: string }>;
};

export type VerificationRunResponse = { run_id: string; status: string };

export type VerificationRunRequest = {
  old_document_id?: string;
  new_document_id?: string;
};

export type VerificationSummary = {
  run_id: string;
  status: string;
  company?: string;
  old_document_year?: number | null;
  new_document_year?: number | null;
  compared_year?: number | null;
  overall_confidence?: number;
  documents_analyzed: number;
  pairs_checked: number;
  values_checked: number;
  ok_count: number;
  mismatch_count: number;
  missing_count: number;
  critical_anomalies: number;
  medium_anomalies: number;
  low_anomalies: number;
  risk_score: number;
  report_paths: string[];
  old_extracted_lines?: number;
  new_extracted_lines?: number;
  comparable_lines?: number;
  matched_lines?: number;
  mismatched_lines?: number;
  missing_in_old?: number;
  missing_in_new?: number;
  ignored_lines?: number;
  comparison_coverage_percentage?: number;
  financial_consistency?: number;
  financial_consistency_numerator?: number;
  financial_consistency_denominator?: number;
  extraction_coverage?: number;
  extraction_coverage_numerator?: number;
  extraction_coverage_denominator?: number;
  structural_quality?: number;
  actual_mismatches?: number;
  missing_in_old_current?: number;
  missing_in_new_comparative?: number;
  duplicate_labels?: number;
  polluted_labels?: number;
  low_confidence_parse?: number;
  critical_accounting_errors?: number;
  carry_forward_ok?: number;
  carry_forward_mismatch?: number;
  risk_level?: string;
  risk_category?: string;
  risk_rationale?: string;
  verdict?: string;
  verdict_reason?: string;
  why_verdict?: {
    verdict?: string;
    reason?: string;
    passed?: string[];
    needs_review?: string[];
    issue_type?: string;
  };
  metric_debug?: Record<string, unknown>;
};

export type EvidenceReference = {
  page?: number | null;
  section?: string | null;
  raw_text?: string | null;
  bounding_box?: number[] | null;
  value?: number | null;
  extraction_method?: string | null;
};

export type Anomaly = {
  id?: string;
  pair: string;
  year: number;
  statement: string;
  statement_name?: string;
  old_label?: string | null;
  new_label?: string | null;
  account_label_old?: string | null;
  account_label_new?: string | null;
  canonical_label: string;
  old_value?: number | null;
  new_value?: number | null;
  old_current_value?: number | null;
  old_previous_value?: number | null;
  new_current_value?: number | null;
  new_previous_value?: number | null;
  expected_value?: number | null;
  actual_value?: number | null;
  status: string;
  severity: string;
  delta?: number | null;
  difference?: number | null;
  difference_percent?: number | null;
  confidence: number;
  explanation?: string;
  technical_reason?: string;
  accountant_reason?: string;
  recommended_action?: string;
  old_document_year?: number | null;
  new_document_year?: number | null;
  compared_year?: number | null;
  old_page?: number | null;
  new_page?: number | null;
  old_section?: string | null;
  new_section?: string | null;
  old_line_text?: string | null;
  new_line_text?: string | null;
  extraction_engine?: string;
  evidence_type?: string;
  matching_method?: string;
  note?: string;
  old_evidence?: EvidenceReference | string;
  new_evidence?: EvidenceReference | string;
};

export type PaginatedAnomalies = {
  items: Anomaly[];
  total: number;
  page: number;
  page_size: number;
};

export type VerificationRunListItem = {
  run_id: string;
  status: string;
  created_at: string;
  summary: Partial<VerificationSummary>;
};

export type BackendSettings = {
  storage_backend: string;
  ai_enabled: boolean;
  ollama_model: string;
  minio_configured: boolean;
};

export type Health = {
  status: string;
  app: string;
  version: string;
  storage_backend: string;
};

export type ApiError = { detail?: string; message?: string };
