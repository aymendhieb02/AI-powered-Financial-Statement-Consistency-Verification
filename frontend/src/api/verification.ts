import { api } from './client';
import type { ComparisonEvidence, DocumentPageResponse, EvidenceListResponse, PaginatedAnomalies, VerificationRunRequest, VerificationRunResponse, VerificationSummary } from '../types/api';

export async function runVerification(projectId: string, payload?: VerificationRunRequest) {
  const { data } = await api.post<VerificationRunResponse>('/projects/' + projectId + '/verification/run', payload ?? {});
  return data;
}

export async function getVerification(projectId: string, runId: string) {
  const { data } = await api.get<VerificationSummary>('/projects/' + projectId + '/verification/' + runId);
  return data;
}

export async function getAnomalies(projectId: string, runId: string, page = 1, pageSize = 25) {
  const { data } = await api.get<PaginatedAnomalies>('/projects/' + projectId + '/verification/' + runId + '/anomalies', {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function getEvidenceList(projectId: string, runId: string) {
  const { data } = await api.get<EvidenceListResponse>('/projects/' + projectId + '/verification/' + runId + '/evidence');
  return data;
}

export async function getEvidenceDetail(projectId: string, runId: string, evidenceId: string) {
  const { data } = await api.get<ComparisonEvidence>('/projects/' + projectId + '/verification/' + runId + '/evidence/' + encodeURIComponent(evidenceId));
  return data;
}

export async function getDocumentPage(projectId: string, documentId: string, pageNumber: number, runId?: string, evidenceId?: string) {
  const { data } = await api.get<DocumentPageResponse>('/projects/' + projectId + '/documents/' + encodeURIComponent(documentId) + '/page/' + pageNumber, {
    params: { run_id: runId, evidence_id: evidenceId },
  });
  return data;
}

export async function listProjectRuns(projectId: string) {
  const { data } = await api.get<Array<{ run_id: string; status: string; created_at: string; summary: Record<string, unknown> }>>('/projects/' + projectId + '/runs');
  return data;
}
