import { useEffect, useState } from 'react';
import { listDocuments } from '../api/documents';
import { UploadedFilesTable } from '../components/upload/UploadedFilesTable';
import type { UploadedDocument } from '../types/api';

export function ProjectDetailPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [files, setFiles] = useState<UploadedDocument[]>([]);
  useEffect(() => { if (projectId) listDocuments(projectId).then(setFiles).catch(() => undefined); }, [projectId]);
  return <section className="space-y-5"><h1 className="text-2xl font-semibold">Project Detail</h1><div className="rounded-lg border border-audit-line bg-white p-4"><div className="text-sm text-audit-muted">Selected project</div><div className="font-mono text-sm">{projectId || 'No project selected'}</div></div><UploadedFilesTable files={files} /></section>;
}
