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
  extraction_coverage_raw_numerator?: number;
  extra_pairings?: number;
  extraction_coverage_denominator?: number;
  structural_quality?: number;
  actual_mismatches?: number;
  missing_in_old_current?: number;
  missing_in_new_comparative?: number;
  new_reporting_lines?: number;
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
  document_id?: string | null;
  source_pdf?: string | null;
  file_name?: string | null;
  page?: number | null;
  page_number?: number | null;
  statement_name?: string | null;
  statement?: string | null;
  section_name?: string | null;
  section?: string | null;
  raw_text?: string | null;
  raw_line?: string | null;
  normalized_line?: string | null;
  label_text?: string | null;
  value_text_current?: string | null;
  value_text_previous?: string | null;
  current_raw?: string | null;
  previous_raw?: string | null;
  current_value?: number | null;
  previous_value?: number | null;
  value?: number | null;
  value_used?: number | null;
  value_role?: string | null;
  extraction_method?: string | null;
  extraction_engine?: string | null;
  confidence?: number | null;
  bounding_box?: number[] | null;
  bbox_label?: number[] | null;
  bbox_current?: number[] | null;
  bbox_previous?: number[] | null;
  bbox_row?: number[] | null;
  bbox_value?: number[] | null;
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
  status_group?: string;
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

export type ComparisonEvidence = Anomaly & {
  hierarchy_path?: string | null;
  issue_type?: string;
  issue_classification?: string | null;
  old_raw_line?: string | null;
  new_raw_line?: string | null;
  old_bbox?: number[] | null;
  new_bbox?: number[] | null;
  old_document_id?: string | null;
  new_document_id?: string | null;
  duplicate_candidates?: EvidenceReference[];
};

export type EvidenceListResponse = {
  items: ComparisonEvidence[];
  total: number;
};

export type DocumentPageResponse = {
  document_id: string;
  page_number: number;
  source_file: string;
  file_url: string;
  image_url?: string | null;
  page_width?: number | null;
  page_height?: number | null;
  statement?: string | null;
  section?: string | null;
  raw_line?: string | null;
  bounding_box?: number[] | null;
};
