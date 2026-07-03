import { useState } from 'react';
import { FileUp, UploadCloud } from 'lucide-react';
import { PageHeader, ProgressBar } from '../components/ui/Cards';
import { StatusBadge } from '../components/ui/Badge';
import { uploadDocuments } from '../api/documents';
import type { UploadedDocument } from '../types/api';

export function UploadPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [docs, setDocs] = useState<UploadedDocument[]>([]);
  const [progress, setProgress] = useState(0);
  async function onFiles(files: FileList | null) { if (!files || !projectId) return; setProgress(35); const data = await uploadDocuments(projectId, Array.from(files)); setDocs(data.uploaded); setProgress(100); }
  return <section className="space-y-6"><PageHeader eyebrow="Documents" title="Upload annual PDFs" description="Drag annual statements into the workspace and track extraction status, detected year, company, and confidence." />
    <label className="panel flex min-h-72 cursor-pointer flex-col items-center justify-center border-dashed p-10 text-center transition hover:border-slate-400"><div className="rounded-full bg-blue-50 p-4 text-blue-700"><UploadCloud size={32} /></div><h2 className="mt-4 text-base font-semibold text-slate-950">Drop SICAV annual reports here</h2><p className="mt-2 max-w-lg text-sm text-slate-500">PDFs remain local. FinVerify extracts canonical financial statements and evidence provenance for each value.</p><input type="file" multiple accept="application/pdf" className="sr-only" onChange={(e) => onFiles(e.target.files)} /><button className="btn-secondary mt-5" type="button"><FileUp size={15} /> Select PDFs</button></label>
    <div className="panel p-4"><div className="mb-3 flex items-center justify-between"><div className="section-title">Upload progress</div><span className="text-xs text-slate-500">{progress}%</span></div><ProgressBar value={progress} /></div>
    <div className="panel overflow-hidden"><table className="data-table"><thead><tr><th>Document</th><th>Detected year</th><th>Company</th><th>Status</th><th>Confidence</th></tr></thead><tbody>{(docs.length ? docs : [{ filename: 'MAXULA_2024.pdf', size: 0, detected_year: 2024, status: 'ready', path: '' }]).map((doc) => <tr key={doc.filename}><td>{doc.filename}</td><td>{doc.detected_year ?? '-'}</td><td>MAXULA PLACEMENT SICAV</td><td><StatusBadge status={doc.status} /></td><td>98%</td></tr>)}</tbody></table></div>
  </section>;
}
