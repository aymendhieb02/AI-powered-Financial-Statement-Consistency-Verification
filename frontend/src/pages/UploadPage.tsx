import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { FileUp, UploadCloud } from 'lucide-react';
import { listDocuments, uploadDocuments } from '../api/documents';
import { getApiErrorMessage } from '../api/client';
import type { UploadedDocument } from '../types/api';
import { useProject } from '../context/ProjectContext';
import { PageHeader, ProgressBar } from '../components/ui/Cards';
import { StatusBadge } from '../components/ui/Badge';
import { CompareTwoDocuments } from '../components/workflow/CompareTwoDocuments';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadPage() {
  const { projectId: routeProjectId } = useParams();
  const { projectId, oldDocumentId, newDocumentId, setOldDocumentId, setNewDocumentId, projectPath } = useProject();
  const activeProjectId = routeProjectId ?? projectId ?? '';
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [docs, setDocs] = useState<UploadedDocument[]>([]);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshDocuments() {
    if (!activeProjectId) return;
    const data = await listDocuments(activeProjectId);
    setDocs(data);
  }

  useEffect(() => {
    if (!activeProjectId) {
      setLoading(false);
      return;
    }
    refreshDocuments()
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load documents')))
      .finally(() => setLoading(false));
  }, [activeProjectId]);

  async function onFiles(files: FileList | null) {
    if (!files?.length) return;
    if (!activeProjectId) {
      setError('Create or select a project first.');
      return;
    }
    setUploading(true);
    setError(null);
    setMessage(null);
    setProgress(20);
    try {
      const data = await uploadDocuments(activeProjectId, Array.from(files));
      setDocs((prev) => {
        const map = new Map(prev.map((doc) => [doc.filename, doc]));
        data.uploaded.forEach((doc) => map.set(doc.filename, doc));
        return Array.from(map.values());
      });
      setProgress(100);
      const uploadedNames = data.uploaded.map((d) => d.filename).join(', ');
      setMessage(`Uploaded ${data.uploaded.length} file(s): ${uploadedNames}. Select two documents and run verification.`);
      if (data.failed.length) setError(data.failed.map((f) => f.error).join('; '));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Upload failed'));
      setProgress(0);
    } finally {
      setUploading(false);
    }
  }

  if (!activeProjectId) {
    return (
      <Card className="border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        No project selected. <Link to="/projects" className="font-medium underline">Create or open a project</Link> before uploading PDFs.
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card
        className="flex min-h-56 cursor-pointer flex-col items-center justify-center border-dashed p-8 text-center transition hover:border-slate-400"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); onFiles(e.dataTransfer.files); }}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="rounded-full bg-blue-50 p-4 text-blue-700"><UploadCloud size={28} /></div>
        <h2 className="mt-4 text-base font-semibold text-slate-950">Drop annual SICAV PDFs here</h2>
        <p className="mt-2 max-w-lg text-sm text-slate-500">Upload the prior-year and current-year annual reports for this project.</p>
        <input ref={fileInputRef} type="file" multiple accept="application/pdf" className="sr-only" onChange={(e) => onFiles(e.target.files)} />
        <Button variant="secondary" className="mt-4" type="button" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }} disabled={uploading}>
          <FileUp size={15} /> {uploading ? 'Uploading...' : 'Select PDFs'}
        </Button>
      </Card>

      {message && <p className="text-sm text-emerald-700">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <Card>
        <CardContent className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="section-title">Upload progress</div>
            <span className="text-xs text-slate-500">{progress}%</span>
          </div>
          <ProgressBar value={progress} />
        </CardContent>
      </Card>

      <Card className="overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Document</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Detected year</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={4} className="py-8 text-center text-sm text-slate-500">Loading documents...</TableCell></TableRow>
            ) : docs.length === 0 ? (
              <TableRow><TableCell colSpan={4} className="py-8 text-center text-sm text-slate-500">No documents uploaded yet.</TableCell></TableRow>
            ) : docs.map((doc) => (
              <TableRow key={doc.filename}>
                <TableCell>{doc.filename}</TableCell>
                <TableCell>{formatSize(doc.size)}</TableCell>
                <TableCell>{doc.detected_year ?? '-'}</TableCell>
                <TableCell><StatusBadge status={doc.status} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <CompareTwoDocuments
        documents={docs}
        oldDocumentId={oldDocumentId}
        newDocumentId={newDocumentId}
        onOldChange={setOldDocumentId}
        onNewChange={setNewDocumentId}
      />

      {docs.length >= 2 && (
        <div className="flex flex-wrap gap-2">
          <Button asChild><Link to={projectPath('verification')}>Continue to Run Verification</Link></Button>
        </div>
      )}
    </div>
  );
}
