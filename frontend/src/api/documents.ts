import { api } from './client';
import type { UploadedDocument, UploadResponse } from '../types/api';

export async function uploadDocuments(projectId: string, files: File[]) {
  const form = new FormData();
  files.forEach((file) => form.append('files', file));
  const { data } = await api.post<UploadResponse>('/projects/' + projectId + '/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function listDocuments(projectId: string) {
  const { data } = await api.get<UploadedDocument[]>('/projects/' + projectId + '/documents');
  return data;
}
