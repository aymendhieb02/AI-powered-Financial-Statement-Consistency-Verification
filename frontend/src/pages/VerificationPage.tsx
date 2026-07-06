import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Play, RotateCw } from 'lucide-react';
import { listDocuments } from '../api/documents';
import { getApiErrorMessage } from '../api/client';
import { getVerification, runVerification } from '../api/verification';
import type { UploadedDocument, VerificationSummary } from '../types/api';
import { useProject } from '../context/ProjectContext';
import { StatCard } from '../components/ui/Cards';
import { PipelineProgress, RiskScoreCard } from '../components/ui/Enterprise';
import { CompareTwoDocuments } from '../components/workflow/CompareTwoDocuments';
import { ReportActions } from '../components/reports/ReportActions';
import { StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

export function VerificationPage() {
  const { projectId: routeProjectId } = useParams();
  const {
    projectId,
    runId,
    setRunId,
    oldDocumentId,
    newDocumentId,
    setOldDocumentId,
    setNewDocumentId,
    projectPath,
  } = useProject();
  const activeProjectId = routeProjectId ?? projectId ?? '';
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [summary, setSummary] = useState<VerificationSummary | null>(null);
  const [message, setMessage] = useState('Select two documents and run comparison.');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeProjectId) return;
    listDocuments(activeProjectId).then(setDocuments).catch(() => undefined);
    if (runId) {
      getVerification(activeProjectId, runId).then(setSummary).catch(() => undefined);
    }
  }, [activeProjectId, runId]);

  async function run() {
    if (!activeProjectId) {
      setError('Select a project first.');
      return;
    }
    if (!oldDocumentId || !newDocumentId) {
      setError('Select old and new documents before running comparison.');
      return;
    }
    if (oldDocumentId === newDocumentId) {
      setError('Old and new documents must be different.');
      return;
    }
    setRunning(true);
    setError(null);
    setMessage('Running extraction, validation, comparison, and reporting...');
    try {
      const run = await runVerification(activeProjectId, {
        old_document_id: oldDocumentId,
        new_document_id: newDocumentId,
      });
      setRunId(run.run_id);
      const result = await getVerification(activeProjectId, run.run_id);
      setSummary(result);
      setMessage('Verification completed successfully.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Verification failed'));
      setMessage('Verification failed.');
    } finally {
      setRunning(false);
    }
  }

  const s = summary ?? {
    documents_analyzed: 0,
    pairs_checked: 0,
    values_checked: 0,
    ok_count: 0,
    mismatch_count: 0,
    missing_count: 0,
    critical_anomalies: 0,
    medium_anomalies: 0,
    low_anomalies: 0,
    risk_score: 0,
  } as VerificationSummary;

  if (!activeProjectId) {
    return <Card className="p-4 text-sm text-slate-500">Select a project to run verification.</Card>;
  }

  return (
    <div className="space-y-6">
      <CompareTwoDocuments
        documents={documents}
        oldDocumentId={oldDocumentId}
        newDocumentId={newDocumentId}
        onOldChange={setOldDocumentId}
        onNewChange={setNewDocumentId}
      />

      <Card className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="text-sm text-slate-600">{message}</div>
        <div className="flex items-center gap-2">
          <StatusBadge status={running ? 'running' : summary ? 'completed' : 'queued'} />
          <Button disabled={running || !oldDocumentId || !newDocumentId || oldDocumentId === newDocumentId} onClick={run}>
            {running ? <RotateCw size={15} className="animate-spin" /> : <Play size={15} />} Run Comparison
          </Button>
        </div>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 text-sm text-red-800">{error}</CardContent>
        </Card>
      )}

      <PipelineProgress active={running ? 3 : summary ? 7 : 0} />

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Documents" value={s.documents_analyzed} />
        <StatCard label="Pairs" value={s.pairs_checked} />
        <StatCard label="Values compared" value={s.values_checked} />
        <StatCard label="Matches" value={s.ok_count} tone="emerald" />
        <StatCard label="Differences" value={s.mismatch_count} tone="amber" />
        <StatCard label="Critical" value={s.critical_anomalies} tone="red" />
      </div>

      <RiskScoreCard score={s.risk_score} />

      {summary && (
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="section-title">Next steps</div>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" asChild><Link to={projectPath('anomalies')}>Review anomalies</Link></Button>
              <Button variant="secondary" asChild><Link to={projectPath('reports')}>Download reports</Link></Button>
            </div>
            <ReportActions projectId={activeProjectId} runId={runId} compact />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
