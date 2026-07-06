import { api } from './client';
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
  const form = new FormData();
  form.append('old_document', oldDocument);
  form.append('new_document', newDocument);
  const { data } = await api.post<CompareTwoDocumentsResponse>('/compare-two-documents', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
