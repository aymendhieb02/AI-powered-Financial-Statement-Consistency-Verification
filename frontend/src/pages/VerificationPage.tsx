import { useState } from 'react';
import { getVerification, runVerification } from '../api/verification';
import { RiskScoreCard } from '../components/dashboard/RiskScoreCard';
import { SummaryCards } from '../components/dashboard/SummaryCards';
import { VerificationChart } from '../components/dashboard/VerificationChart';
import type { VerificationSummary } from '../types/api';

export function VerificationPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [summary, setSummary] = useState<VerificationSummary | null>(null);
  const [message, setMessage] = useState('');
  async function run() { if (!projectId) { setMessage('Create and select a project first.'); return; } setMessage('Verification running...'); const run = await runVerification(projectId); localStorage.setItem('finverify_run_id', run.run_id); const result = await getVerification(projectId, run.run_id); setSummary(result); setMessage('Verification completed.'); }
  return <section className="space-y-5"><div className="flex items-center justify-between"><h1 className="text-2xl font-semibold">Verification</h1><button className="rounded bg-audit-accent px-4 py-2 text-white" onClick={run}>Run Verification</button></div>{message && <div className="text-sm text-audit-muted">{message}</div>}{summary && <><SummaryCards cards={[{ label: 'Documents analyzed', value: summary.documents_analyzed }, { label: 'Values checked', value: summary.values_checked }, { label: 'Mismatches', value: summary.mismatch_count, tone: 'text-red-700' }, { label: 'Missing', value: summary.missing_count, tone: 'text-orange-700' }]} /><RiskScoreCard score={summary.risk_score} /><VerificationChart summary={summary} /></>}</section>;
}
