import { api, isNotFound } from './client';
import type { Anomaly, UploadedDocument, VerificationSummary } from '../types/api';

export type CompareTwoDocumentsResponse = {
  project_id: string;
  run_id: string;
  summary: VerificationSummary;
  anomalies: Anomaly[];
  report_paths: string[];
  old_document: UploadedDocument;
  new_document: UploadedDocument;
};

export async function compareTwoDocuments(oldDocument: File, newDocument: File) {
  try {
    return await compareViaSimpleEndpoint(oldDocument, newDocument);
  } catch (error) {
    if (!isNotFound(error)) throw error;
    return compareViaProjectWorkflow(oldDocument, newDocument);
  }
}

async function compareViaSimpleEndpoint(oldDocument: File, newDocument: File) {
  const form = new FormData();
  form.append('old_document', oldDocument);
  form.append('new_document', newDocument);

  const { data } = await api.post<CompareTwoDocumentsResponse>('/compare-two-documents', form);
  return data;
}

async function compareViaProjectWorkflow(oldDocument: File, newDocument: File): Promise<CompareTwoDocumentsResponse> {
  const project = await createTemporaryProject();
  const uploaded = await uploadDocuments(project.id, oldDocument, newDocument);
  const oldRecord = uploaded.uploaded[0];
  const newRecord = uploaded.uploaded[1];

  if (!oldRecord || !newRecord) {
    const detail = uploaded.failed.map((item) => `${item.filename ?? 'document'}: ${item.error}`).join('; ');
    throw new Error(detail || 'Could not upload both PDF documents.');
  }

  const { data: run } = await api.post<{ run_id: string; status: string }>(
    `/projects/${project.id}/verification/run`,
    {
      old_document_id: oldRecord.filename,
      new_document_id: newRecord.filename,
    },
  );
  const { data: summary } = await api.get<VerificationSummary>(`/projects/${project.id}/verification/${run.run_id}`);
  const { data: anomalies } = await api.get<{ items: Anomaly[] }>(
    `/projects/${project.id}/verification/${run.run_id}/anomalies`,
    { params: { page: 1, page_size: 500 } },
  );

  return {
    project_id: project.id,
    run_id: run.run_id,
    summary,
    anomalies: anomalies.items,
    report_paths: summary.report_paths,
    old_document: oldRecord,
    new_document: newRecord,
  };
}

async function createTemporaryProject() {
  const { data } = await api.post<{ id: string; name: string; company: string; description: string; created_at: string }>(
    '/projects',
    {
      name: 'Two-document comparison',
      company: 'SICAV',
      description: 'Created from the simplified compare workflow.',
    },
  );
  return data;
}

async function uploadDocuments(projectId: string, oldDocument: File, newDocument: File) {
  const form = new FormData();
  form.append('files', oldDocument);
  form.append('files', newDocument);

  const { data } = await api.post<{
    uploaded: UploadedDocument[];
    failed: Array<{ filename?: string; error: string }>;
  }>(`/projects/${projectId}/documents/upload`, form);
  return data;
}
