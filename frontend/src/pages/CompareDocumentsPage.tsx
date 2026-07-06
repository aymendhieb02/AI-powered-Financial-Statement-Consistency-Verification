import { AlertCircle, ArrowRight, FileText, Play, UploadCloud } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { compareTwoDocuments } from '../api/compare';
import { getApiErrorMessage } from '../api/client';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { PageHeader } from '../components/ui/Cards';

function detectedYear(file: File | null) {
  if (!file) return null;
  const match = file.name.match(/(20\d{2}|19\d{2})/);
  return match ? Number(match[1]) : null;
}

function DocumentPicker({ label, file, onChange }: { label: string; file: File | null; onChange: (file: File | null) => void }) {
  const year = detectedYear(file);
  return (
    <Card>
      <CardHeader><CardTitle>{label}</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center transition hover:border-slate-500 hover:bg-white">
          <UploadCloud size={28} className="text-slate-500" />
          <span className="mt-3 text-sm font-medium text-slate-900">Choose annual PDF</span>
          <span className="mt-1 text-xs text-slate-500">PDF only. The file stays in the local FinVerify workspace.</span>
          <input className="sr-only" type="file" accept="application/pdf" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
        </label>
        {file ? (
          <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
            <div className="flex items-start gap-3">
              <FileText size={18} className="mt-0.5 text-blue-600" />
              <div className="min-w-0">
                <div className="truncate font-medium text-slate-950">{file.name}</div>
                <div className="mt-1 text-slate-500">Detected company: pending extraction</div>
                <div className="mt-1 text-slate-500">Detected year: {year ?? 'not detected from filename'}</div>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2"><StatusBadge status="uploaded" /><Badge tone="neutral">Extraction after compare</Badge></div>
          </div>
        ) : <div className="text-sm text-slate-500">No document selected.</div>}
      </CardContent>
    </Card>
  );
}

export function CompareDocumentsPage() {
  const [oldFile, setOldFile] = useState<File | null>(null);
  const [newFile, setNewFile] = useState<File | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const canRun = !!oldFile && !!newFile && !running;
  const comparedYear = useMemo(() => detectedYear(oldFile), [oldFile]);

  async function runComparison() {
    if (!oldFile || !newFile) return;
    setRunning(true);
    setError('');
    try {
      const result = await compareTwoDocuments(oldFile, newFile);
      localStorage.setItem('finverify_project_id', result.project_id);
      localStorage.setItem('finverify_run_id', result.run_id);
      localStorage.setItem('finverify_last_summary', JSON.stringify(result.summary));
      navigate(`/results/${result.run_id}`);
    } catch (exc) {
      setError(getApiErrorMessage(exc, 'Comparison failed.'));
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Simple workflow"
        title="Compare two annual reports"
        description="Upload the old annual PDF and the new annual PDF. FinVerify will compare the current-year values from the old report with the comparative previous-year values from the new report."
      />
      <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr]">
        <DocumentPicker label="Old annual report" file={oldFile} onChange={setOldFile} />
        <div className="hidden items-center justify-center lg:flex"><div className="rounded-full border border-slate-200 bg-white p-3 text-slate-500"><ArrowRight size={20} /></div></div>
        <DocumentPicker label="New annual report" file={newFile} onChange={setNewFile} />
      </div>
      <Card>
        <CardContent className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-sm font-semibold text-slate-950">Comparison logic</div>
            <p className="mt-1 text-sm text-slate-500">Compared year: {comparedYear ?? 'detected after extraction'}. FinVerify checks whether that year was correctly carried forward into the new report.</p>
            {error && <div className="mt-3 flex items-center gap-2 text-sm text-red-700"><AlertCircle size={15} /> {error}</div>}
          </div>
          <Button onClick={runComparison} disabled={!canRun}><Play size={15} /> {running ? 'Running comparison...' : 'Run Comparison'}</Button>
        </CardContent>
      </Card>
    </section>
  );
}
