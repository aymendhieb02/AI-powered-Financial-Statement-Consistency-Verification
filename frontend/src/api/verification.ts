import { api } from './client';
import type { PaginatedAnomalies, VerificationSummary } from '../types/api';

export async function runVerification(projectId: string) {
  const { data } = await api.post<{ run_id: string; status: string }>('/projects/' + projectId + '/verification/run');
  return data;
}

export async function getVerification(projectId: string, runId: string) {
  const { data } = await api.get<VerificationSummary>('/projects/' + projectId + '/verification/' + runId);
  return data;
}

export async function getAnomalies(projectId: string, runId: string) {
  const { data } = await api.get<PaginatedAnomalies>('/projects/' + projectId + '/verification/' + runId + '/anomalies');
  return data;
}
