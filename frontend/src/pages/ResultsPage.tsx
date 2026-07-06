import { AlertTriangle, CheckCircle2, FileText, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getVerification } from '../api/verification';
import { ReportActions } from '../components/reports/ReportActions';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { EmptyState, PageHeader, StatCard } from '../components/ui/Cards';
import type { VerificationSummary } from '../types/api';

export function ResultsPage() {
  const { runId = '' } = useParams();
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [summary, setSummary] = useState<VerificationSummary | null>(() => {
    const cached = localStorage.getItem('finverify_last_summary');
    return cached ? JSON.parse(cached) as VerificationSummary : null;
  });

  useEffect(() => {
    if (projectId && runId) {
      getVerification(projectId, runId).then((data) => {
        setSummary(data);
        localStorage.setItem('finverify_last_summary', JSON.stringify(data));
      }).catch(() => undefined);
    }
  }, [projectId, runId]);

  if (!summary) {
    return <EmptyState title="No comparison result yet" description="Upload two annual PDFs and run a comparison first." action={<Button asChild><Link to="/compare">Compare documents</Link></Button>} />;
  }

  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Results" title="Comparison summary" description="A clear accountant summary of what FinVerify checked and what needs review." actions={<ReportActions projectId={projectId} runId={runId} compact />} />
      <Card>
        <CardContent className="grid gap-4 p-5 text-sm md:grid-cols-4">
          <Fact label="Company" value={summary.company || 'Detected after extraction'} />
          <Fact label="Old document year" value={summary.old_document_year ?? '-'} />
          <Fact label="New document year" value={summary.new_document_year ?? '-'} />
          <Fact label="Compared year" value={summary.compared_year ?? summary.old_document_year ?? '-'} />
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Values checked" value={summary.values_checked} icon={<FileText size={18} />} />
        <StatCard label="Matches" value={summary.ok_count} icon={<CheckCircle2 size={18} />} tone="emerald" />
        <StatCard label="Mismatches" value={summary.mismatch_count} icon={<AlertTriangle size={18} />} tone="amber" />
        <StatCard label="Missing rows" value={summary.missing_count} tone="red" />
        <StatCard label="Critical anomalies" value={summary.critical_anomalies} tone="red" />
        <StatCard label="Medium anomalies" value={summary.medium_anomalies} tone="amber" />
        <StatCard label="Low anomalies" value={summary.low_anomalies} tone="blue" />
        <StatCard label="Confidence" value={`${Math.round((summary.overall_confidence ?? 0) * 100)}%`} icon={<ShieldCheck size={18} />} tone="emerald" />
      </div>
      <Card>
        <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div><div className="text-sm font-semibold text-slate-950">Risk score</div><div className="mt-1 text-sm text-slate-500">Higher scores indicate more accountant review required.</div></div>
          <div className="text-3xl font-semibold text-slate-950">{summary.risk_score}</div>
        </CardContent>
      </Card>
      <div className="flex flex-wrap gap-3">
        <Button asChild><Link to={`/anomalies/${runId}`}>Review anomalies</Link></Button>
        <Button asChild variant="secondary"><Link to={`/reports/${runId}`}>Download reports</Link></Button>
      </div>
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string | number }) {
  return <div><div className="text-slate-500">{label}</div><div className="mt-1 font-semibold text-slate-950">{value}</div></div>;
}
