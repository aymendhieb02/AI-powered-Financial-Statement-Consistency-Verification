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
};

export type Anomaly = {
  pair: string;
  year: number;
  statement: string;
  old_label?: string | null;
  new_label?: string | null;
  canonical_label: string;
  old_value?: number | null;
  new_value?: number | null;
  status: string;
  severity: string;
  delta?: number | null;
  confidence: number;
  note?: string;
  old_evidence?: string;
  new_evidence?: string;
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
