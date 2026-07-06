import { api } from './client';
import type { PaginatedAnomalies, VerificationRunRequest, VerificationRunResponse, VerificationSummary } from '../types/api';

export async function runVerification(projectId: string, payload?: VerificationRunRequest) {
  const { data } = await api.post<VerificationRunResponse>(`/projects/${projectId}/verification/run`, payload ?? {});
  return data;
}

export async function getVerification(projectId: string, runId: string) {
  const { data } = await api.get<VerificationSummary>(`/projects/${projectId}/verification/${runId}`);
  return data;
}

export async function getAnomalies(projectId: string, runId: string, page = 1, pageSize = 25) {
  const { data } = await api.get<PaginatedAnomalies>(`/projects/${projectId}/verification/${runId}/anomalies`, {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function listProjectRuns(projectId: string) {
  const { data } = await api.get<Array<{ run_id: string; status: string; created_at: string; summary: Record<string, unknown> }>>(`/projects/${projectId}/runs`);
  return data;
}
