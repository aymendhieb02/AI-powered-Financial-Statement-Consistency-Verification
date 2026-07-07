import { AlertTriangle, CheckCircle2, ClipboardCheck, Download, FileJson, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { excelReportUrl, jsonReportUrl } from '../api/reports';
import { getVerification } from '../api/verification';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { EmptyState, PageHeader, StatCard } from '../components/ui/Cards';
import type { VerificationSummary } from '../types/api';

const pipelineStages = ['Extraction', 'Normalization', 'Validation', 'Rule Engine', 'Comparison', 'Report Generation'];

export function ResultsPage() {
  const { runId = '' } = useParams();
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [summary, setSummary] = useState<VerificationSummary | null>(() => {
    const cached = localStorage.getItem('finverify_last_summary');
    return cached ? JSON.parse(cached) as VerificationSummary : null;
  });

  useEffect(() => {
    if (projectId && runId && runId !== 'latest') {
      getVerification(projectId, runId).then((data) => {
        setSummary(data);
        localStorage.setItem('finverify_last_summary', JSON.stringify(data));
      }).catch(() => undefined);
    }
  }, [projectId, runId]);

  if (!summary) {
    return <EmptyState title="No comparison has been executed yet." description="Upload two annual financial statements and click Compare." action={<Button asChild><Link to="/compare">Go to Compare Documents</Link></Button>} />;
  }

  const verdict = verdictStyle(summary.verdict ?? getLegacyVerdict(summary));
  const hasReports = Boolean(projectId && runId && runId !== 'latest' && summary.report_paths?.length);
  const why = summary.why_verdict ?? {};
  const noFinancialFailure = (summary.actual_mismatches ?? summary.mismatch_count ?? 0) === 0 && (summary.critical_accounting_errors ?? summary.critical_anomalies ?? 0) === 0;

  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Results" title="Audit result" description="Is the new annual report financially consistent with the previous annual report?" />

      <Card className={'border-l-4 ' + verdict.borderClass}>
        <CardContent className="grid gap-5 p-5 lg:grid-cols-[1fr_1.5fr]">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Audit Verdict</div>
            <div className={'mt-2 text-3xl font-semibold ' + verdict.textClass}>{summary.verdict ?? verdict.label}</div>
            <p className="mt-3 text-sm leading-6 text-slate-600">{summary.verdict_reason || verdict.reason}</p>
            {noFinancialFailure && <p className="mt-3 rounded-md bg-emerald-50 p-3 text-sm font-medium text-emerald-800">Financial values compared successfully. Some rows may require extraction/label review.</p>}
          </div>
          <div className="rounded-md bg-slate-50 p-4">
            <div className="text-sm font-semibold text-slate-950">Why this verdict?</div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <ReasonList title="Passed" items={why.passed ?? ['No actual carry-forward value differences were detected.']} tone="emerald" />
              <ReasonList title="Needs review" items={why.needs_review ?? []} tone="amber" empty="No extraction or structural review items." />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card><CardContent className="grid gap-4 p-5 text-sm md:grid-cols-5"><Fact label="Company" value={summary.company || 'Not detected'} /><Fact label="Old report year" value={summary.old_document_year ?? 'Not detected'} /><Fact label="New report year" value={summary.new_document_year ?? 'Not detected'} /><Fact label="Compared financial year" value={summary.compared_year ?? summary.old_document_year ?? 'Not detected'} /><Fact label="Comparison status" value={summary.status || 'completed'} /></CardContent></Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Financial consistency" value={formatPercent(summary.financial_consistency)} icon={<CheckCircle2 size={18} />} tone="emerald" />
        <StatCard label="Extraction coverage" value={formatPercent(summary.extraction_coverage ?? summary.comparison_coverage_percentage)} icon={<ClipboardCheck size={18} />} tone="blue" />
        <StatCard label="Structural quality" value={formatPercent(summary.structural_quality)} icon={<ShieldCheck size={18} />} tone="emerald" />
        <StatCard label="Actual value differences" value={summary.actual_mismatches ?? summary.mismatch_count} icon={<AlertTriangle size={18} />} tone="amber" />
        <StatCard label="Missing / unpaired accounts" value={summary.missing_count ?? 0} tone="red" />
        <StatCard label="Duplicate / ambiguous labels" value={summary.duplicate_labels ?? 0} tone="amber" />
        <StatCard label="Polluted labels" value={summary.polluted_labels ?? 0} tone="amber" />
        <StatCard label="Critical accounting errors" value={summary.critical_accounting_errors ?? summary.critical_anomalies} tone="red" />
        <StatCard label="Extraction confidence" value={formatConfidence(summary.overall_confidence)} icon={<ShieldCheck size={18} />} tone="emerald" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <MetricCard title="Financial Consistency" value={formatPercent(summary.financial_consistency)} detail={(summary.financial_consistency_numerator ?? summary.ok_count) + ' / ' + (summary.financial_consistency_denominator ?? summary.values_checked) + ' actually compared values matched.'} />
        <MetricCard title="Extraction Coverage" value={formatPercent(summary.extraction_coverage)} detail={(summary.extraction_coverage_numerator ?? 0) + ' / ' + (summary.extraction_coverage_denominator ?? summary.comparable_lines ?? 0) + ' expected unique accounts were paired.'} />
        <MetricCard title={'Risk: ' + (summary.risk_level ?? 'LOW')} value={Math.round(summary.risk_score ?? 0) + ' / 100'} detail={(summary.risk_category ?? 'LOW') + ': ' + (summary.risk_rationale ?? 'Low review effort expected.')} />
      </div>

      <Card><CardContent className="p-5"><div className="text-sm font-semibold text-slate-950">Comparison evidence counts</div><div className="mt-4 grid gap-4 text-sm md:grid-cols-3 xl:grid-cols-6"><Fact label="Old extracted lines" value={summary.old_extracted_lines ?? 'Not detected'} /><Fact label="New extracted lines" value={summary.new_extracted_lines ?? 'Not detected'} /><Fact label="Actually compared" value={summary.financial_consistency_denominator ?? summary.values_checked} /><Fact label="Missing in old" value={summary.missing_in_old_current ?? summary.missing_in_old ?? 0} /><Fact label="Missing in new" value={summary.missing_in_new_comparative ?? summary.missing_in_new ?? 0} /><Fact label="Low confidence parses" value={summary.low_confidence_parse ?? 0} /></div></CardContent></Card>

      <Card><CardContent className="p-5"><div className="text-sm font-semibold text-slate-950">Pipeline checklist</div><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{pipelineStages.map((stage) => <div key={stage} className="flex items-start gap-3 rounded-md border border-slate-200 p-3"><CheckCircle2 className="mt-0.5 text-emerald-600" size={18} /><div><div className="text-sm font-medium text-slate-950">{stage}</div><div className="text-xs text-slate-500">Completed - Duration not available</div></div></div>)}</div></CardContent></Card>

      <Card><CardContent className="flex flex-col gap-3 p-5 lg:flex-row lg:items-center lg:justify-between"><div><div className="text-sm font-semibold text-slate-950">Next actions</div><p className="mt-1 text-sm text-slate-500">Review extraction/label issues separately from actual financial mismatches, then export the audit evidence package.</p>{!hasReports && <p className="mt-2 text-sm text-amber-700">Run a comparison first.</p>}</div><div className="flex flex-wrap gap-3"><Button asChild><Link to={'/anomalies/' + runId}>Review Anomalies</Link></Button>{hasReports ? <><Button asChild variant="secondary"><a href={excelReportUrl(projectId, runId)} download><Download size={16} /> Download Excel Audit Report</a></Button><Button asChild variant="secondary"><a href={jsonReportUrl(projectId, runId)} download><FileJson size={16} /> Download JSON Report</a></Button></> : <><Button variant="secondary" disabled><Download size={16} /> Download Excel Audit Report</Button><Button variant="secondary" disabled><FileJson size={16} /> Download JSON Report</Button></>}</div></CardContent></Card>
    </section>
  );
}

function MetricCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return <Card><CardContent className="p-5"><div className="text-sm font-semibold text-slate-950">{title}</div><div className="mt-2 text-3xl font-semibold text-slate-950">{value}</div><p className="mt-2 text-sm text-slate-500">{detail}</p></CardContent></Card>;
}

function ReasonList({ title, items, tone, empty }: { title: string; items: string[]; tone: 'emerald' | 'amber'; empty?: string }) {
  const dot = tone === 'emerald' ? 'bg-emerald-500' : 'bg-amber-500';
  return <div><div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</div><div className="mt-2 space-y-2">{items.length ? items.map((item) => <div key={item} className="flex gap-2 text-sm text-slate-600"><span className={'mt-2 h-1.5 w-1.5 rounded-full ' + dot} />{item}</div>) : <div className="text-sm text-slate-500">{empty}</div>}</div></div>;
}

function verdictStyle(label: string) {
  if (label === 'FAIL') return { label, textClass: 'text-red-700', borderClass: 'border-l-red-600', reason: 'Actual carry-forward mismatch or critical accounting issue detected.' };
  if (label === 'NEEDS REVIEW') return { label, textClass: 'text-amber-700', borderClass: 'border-l-amber-500', reason: 'Financial values match, but extraction or label issues require review.' };
  return { label: 'PASS', textClass: 'text-emerald-700', borderClass: 'border-l-emerald-600', reason: 'No financial mismatches detected.' };
}

function getLegacyVerdict(summary: VerificationSummary) {
  if (summary.critical_anomalies > 0 || summary.mismatch_count > 0) return 'FAIL';
  if (summary.missing_count > 0) return 'NEEDS REVIEW';
  return 'PASS';
}

function formatPercent(value?: number | null) {
  return value == null ? 'Not available' : value.toFixed(2) + '%';
}

function formatConfidence(confidence?: number) {
  if (confidence == null || confidence === 0) return 'Not calculated';
  return (confidence * 100).toFixed(1) + '%';
}

function Fact({ label, value }: { label: string; value: string | number }) {
  return <div><div className="text-slate-500">{label}</div><div className="mt-1 font-semibold text-slate-950">{value}</div></div>;
}
