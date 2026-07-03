import { useRef, useState } from 'react';
import { FileUp, UploadCloud } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PageHeader, ProgressBar } from '../components/ui/Cards';
import { StatusBadge } from '../components/ui/Badge';
import { uploadDocuments } from '../api/documents';
import type { UploadedDocument } from '../types/api';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

export function UploadPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [docs, setDocs] = useState<UploadedDocument[]>([]);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState<string | null>(null);

  async function onFiles(files: FileList | null) {
    if (!files?.length) return;
    if (!projectId) {
      setMessage('Create or select a project first.');
      return;
    }
    setMessage(null);
    setProgress(35);
    try {
      const data = await uploadDocuments(projectId, Array.from(files));
      setDocs(data.uploaded);
      setProgress(100);
    } catch {
      setMessage('Upload failed. Check that the backend is running.');
      setProgress(0);
    }
  }

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  const rows = docs.length ? docs : [];

  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Documents" title="Upload annual PDFs" description="Drag annual statements into the workspace and track extraction status, detected year, company, and confidence." />
      {!projectId && (
        <Card className="border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          No project selected. <Link to="/projects" className="font-medium underline">Create or open a project</Link> before uploading PDFs.
        </Card>
      )}
      <Card
        className="flex min-h-72 cursor-pointer flex-col items-center justify-center border-dashed p-10 text-center transition hover:border-slate-400"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); onFiles(e.dataTransfer.files); }}
        onClick={openFilePicker}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openFilePicker(); } }}
      >
        <div className="rounded-full bg-blue-50 p-4 text-blue-700"><UploadCloud size={32} /></div>
        <h2 className="mt-4 text-base font-semibold text-slate-950">Drop SICAV annual reports here</h2>
        <p className="mt-2 max-w-lg text-sm text-slate-500">PDFs remain local. FinVerify extracts canonical financial statements and evidence provenance for each value.</p>
        <input ref={fileInputRef} type="file" multiple accept="application/pdf" className="sr-only" onChange={(e) => onFiles(e.target.files)} />
        <Button
          variant="secondary"
          className="mt-5"
          type="button"
          onClick={(e) => { e.stopPropagation(); openFilePicker(); }}
        >
          <FileUp size={15} /> Select PDFs
        </Button>
      </Card>
      {message && <p className="text-sm text-red-600">{message}</p>}
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
              <TableHead>Detected year</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Confidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length ? rows.map((doc) => (
              <TableRow key={doc.filename}>
                <TableCell>{doc.filename}</TableCell>
                <TableCell>{doc.detected_year ?? '-'}</TableCell>
                <TableCell>MAXULA PLACEMENT SICAV</TableCell>
                <TableCell><StatusBadge status={doc.status} /></TableCell>
                <TableCell>98%</TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={5} className="py-8 text-center text-sm text-slate-500">No documents uploaded yet.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </section>
  );
}
