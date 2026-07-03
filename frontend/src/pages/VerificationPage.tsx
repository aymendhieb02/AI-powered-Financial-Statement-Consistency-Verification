import { useState } from 'react';
import { Play, RotateCw } from 'lucide-react';
import { getVerification, runVerification } from '../api/verification';
import type { VerificationSummary } from '../types/api';
import { PageHeader, StatCard } from '../components/ui/Cards';
import { PipelineProgress, RiskScoreCard } from '../components/ui/Enterprise';
import { StatusBadge } from '../components/ui/Badge';

export function VerificationPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [summary, setSummary] = useState<VerificationSummary | null>(null);
  const [message, setMessage] = useState('Ready to run');
  const [running, setRunning] = useState(false);
  async function run() { if (!projectId) { setMessage('Create and select a project first.'); return; } setRunning(true); setMessage('Verification running through extraction, rules, comparison, and reporting...'); const run = await runVerification(projectId); localStorage.setItem('finverify_run_id', run.run_id); const result = await getVerification(projectId, run.run_id); setSummary(result); setMessage('Verification completed.'); setRunning(false); }
  const s = summary ?? { documents_analyzed: 0, pairs_checked: 0, values_checked: 0, ok_count: 0, mismatch_count: 0, missing_count: 0, critical_anomalies: 0, medium_anomalies: 0, low_anomalies: 0, risk_score: 0 } as VerificationSummary;
  return <section className="space-y-6"><PageHeader eyebrow="Verification operations" title="Run verification" description="Execute the full deterministic pipeline and generate accountant-facing reports without leaving the workspace." actions={<button className="btn-primary" disabled={running} onClick={run}>{running ? <RotateCw size={15} className="animate-spin" /> : <Play size={15} />} Run Verification</button>} />
    <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3"><div className="text-sm text-slate-600">{message}</div><StatusBadge status={running ? 'running' : summary ? 'completed' : 'queued'} /></div><PipelineProgress active={running ? 3 : summary ? 7 : 0} />
    <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6"><StatCard label="Documents" value={s.documents_analyzed} /><StatCard label="Pairs" value={s.pairs_checked} /><StatCard label="Values compared" value={s.values_checked} /><StatCard label="Matches" value={s.ok_count} tone="emerald" /><StatCard label="Differences" value={s.mismatch_count} tone="amber" /><StatCard label="Critical" value={s.critical_anomalies} tone="red" /></div><RiskScoreCard score={s.risk_score} />
  </section>;
}
