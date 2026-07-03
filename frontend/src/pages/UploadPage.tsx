import { useEffect, useState } from 'react';
import { listDocuments, uploadDocuments } from '../api/documents';
import { UploadDropzone } from '../components/upload/UploadDropzone';
import { UploadedFilesTable } from '../components/upload/UploadedFilesTable';
import type { UploadedDocument } from '../types/api';

export function UploadPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [files, setFiles] = useState<UploadedDocument[]>([]);
  const [message, setMessage] = useState('');
  async function refresh() { if (projectId) setFiles(await listDocuments(projectId)); }
  useEffect(() => { refresh().catch(() => undefined); }, [projectId]);
  async function handleUpload(selected: File[]) { if (!projectId) { setMessage('Create and select a project first.'); return; } setMessage('Uploading...'); const result = await uploadDocuments(projectId, selected); setMessage(result.failed.length ? 'Some files failed.' : 'Upload completed.'); await refresh(); }
  return <section className="space-y-5"><h1 className="text-2xl font-semibold">Upload Documents</h1><UploadDropzone onFiles={handleUpload} />{message && <div className="text-sm text-audit-muted">{message}</div>}<UploadedFilesTable files={files} /></section>;
}
