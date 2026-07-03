export function excelReportUrl(projectId: string, runId: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
  return base + '/projects/' + projectId + '/reports/' + runId + '/excel';
}

export function jsonReportUrl(projectId: string, runId: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
  return base + '/projects/' + projectId + '/reports/' + runId + '/json';
}
