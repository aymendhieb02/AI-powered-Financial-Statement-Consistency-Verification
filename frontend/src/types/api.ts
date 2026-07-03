export type Project = { id: string; name: string; company: string; description: string; created_at: string };
export type UploadedDocument = { filename: string; size: number; detected_year?: number | null; status: string; path: string };
export type UploadResponse = { uploaded: UploadedDocument[]; failed: Array<{ filename?: string; error: string }> };
export type VerificationSummary = { run_id: string; status: string; documents_analyzed: number; pairs_checked: number; values_checked: number; ok_count: number; mismatch_count: number; missing_count: number; critical_anomalies: number; medium_anomalies: number; low_anomalies: number; risk_score: number; report_paths: string[] };
export type Anomaly = { pair: string; year: number; statement: string; old_label?: string | null; new_label?: string | null; canonical_label: string; old_value?: number | null; new_value?: number | null; status: string; severity: string; delta?: number | null; confidence: number; note?: string };
export type PaginatedAnomalies = { items: Anomaly[]; total: number; page: number; page_size: number };
export type BackendSettings = { storage_backend: string; ai_enabled: boolean; ollama_model: string; minio_configured: boolean };
export type Health = { status: string; app: string; version: string; storage_backend: string };
