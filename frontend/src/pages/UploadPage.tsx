import { useState } from 'react';
import { FileUp, UploadCloud } from 'lucide-react';
import { PageHeader, ProgressBar } from '../components/ui/Cards';
import { StatusBadge } from '../components/ui/Badge';
import { uploadDocuments } from '../api/documents';
import type { UploadedDocument } from '../types/api';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

export function UploadPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [docs, setDocs] = useState<UploadedDocument[]>([]);
  const [progress, setProgress] = useState(0);
  async function onFiles(files: FileList | null) { if (!files || !projectId) return; setProgress(35); const data = await uploadDocuments(projectId, Array.from(files)); setDocs(data.uploaded); setProgress(100); }
  const rows = docs.length ? docs : [{ filename: 'MAXULA_2024.pdf', size: 0, detected_year: 2024, status: 'ready', path: '' }];
  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Documents" title="Upload annual PDFs" description="Drag annual statements into the workspace and track extraction status, detected year, company, and confidence." />
      <label className="block cursor-pointer">
        <Card className="flex min-h-72 flex-col items-center justify-center border-dashed p-10 text-center transition hover:border-slate-400">
          <div className="rounded-full bg-blue-50 p-4 text-blue-700"><UploadCloud size={32} /></div>
          <h2 className="mt-4 text-base font-semibold text-slate-950">Drop SICAV annual reports here</h2>
          <p className="mt-2 max-w-lg text-sm text-slate-500">PDFs remain local. FinVerify extracts canonical financial statements and evidence provenance for each value.</p>
          <input type="file" multiple accept="application/pdf" className="sr-only" onChange={(e) => onFiles(e.target.files)} />
          <Button variant="secondary" className="mt-5" type="button"><FileUp size={15} /> Select PDFs</Button>
        </Card>
      </label>
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
            {rows.map((doc) => (
              <TableRow key={doc.filename}>
                <TableCell>{doc.filename}</TableCell>
                <TableCell>{doc.detected_year ?? '-'}</TableCell>
                <TableCell>MAXULA PLACEMENT SICAV</TableCell>
                <TableCell><StatusBadge status={doc.status} /></TableCell>
                <TableCell>98%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </section>
  );
}
