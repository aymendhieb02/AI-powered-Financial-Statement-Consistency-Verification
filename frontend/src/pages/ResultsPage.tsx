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
    return (
      <EmptyState
        title="No comparison has been executed yet."
        description="Upload two annual financial statements and click Compare."
        action={<Button asChild><Link to="/compare">Go to Compare Documents</Link></Button>}
      />
    );
  }

  const verdict = getVerdict(summary);
  const consistency = getConsistency(summary);
  const confidence = formatConfidence(summary.overall_confidence, summary.values_checked);
  const risk = getRisk(summary.risk_score, summary.critical_anomalies);
  const hasReports = Boolean(projectId && runId && runId !== 'latest' && summary.report_paths?.length);
  const comparableLines = summary.comparable_lines ?? summary.values_checked;
  const coveragePercent = summary.comparison_coverage_percentage;

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Results"
        title="Audit result"
        description="Is the new annual report financially consistent with the previous annual report?"
      />

      <Card className={`border-l-4 ${verdict.borderClass}`}>
        <CardContent className="grid gap-5 p-5 lg:grid-cols-[1.1fr_1.4fr]">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Audit Verdict</div>
            <div className={`mt-2 text-3xl font-semibold ${verdict.textClass}`}>{verdict.label}</div>
            <div className="mt-3 text-sm text-slate-600">Carry-forward consistency</div>
            <div className="mt-1 text-2xl font-semibold text-slate-950">{consistency.label}</div>
            <p className="mt-1 text-sm text-slate-500">{consistency.detail}</p>
          </div>
          <div className="rounded-md bg-slate-50 p-4">
            <div className="text-sm font-semibold text-slate-950">Summary</div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              The {formatValue(summary.new_document_year, 'new report')} report was compared against the comparative {formatValue(summary.compared_year ?? summary.old_document_year, 'previous-year')} values.
              {' '}{summary.values_checked} financial values were checked.
              {' '}{summary.ok_count} matched.
              {' '}{summary.mismatch_count + summary.missing_count} require accountant review.
              {' '}{summary.critical_anomalies > 0 ? `${summary.critical_anomalies} critical accounting inconsistencies were detected.` : 'No critical accounting inconsistencies were detected.'}
            </p>
          </div>
        </CardContent>
      </Card>

      {comparableLines < 20 && (
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-5">
            <div className="text-sm font-semibold text-amber-800">Low comparison coverage</div>
            <p className="mt-1 text-sm text-slate-600">
              FinVerify extracted only {comparableLines} comparable values. Review extraction quality.
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="grid gap-4 p-5 text-sm md:grid-cols-5">
          <Fact label="Company" value={summary.company || 'Not detected'} />
          <Fact label="Old report year" value={summary.old_document_year ?? 'Not detected'} />
          <Fact label="New report year" value={summary.new_document_year ?? 'Not detected'} />
          <Fact label="Compared financial year" value={summary.compared_year ?? summary.old_document_year ?? 'Not detected'} />
          <Fact label="Comparison status" value={summary.status || 'completed'} />
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Compared financial values" value={summary.values_checked} icon={<ClipboardCheck size={18} />} />
        <StatCard label="Matched values" value={summary.ok_count} icon={<CheckCircle2 size={18} />} tone="emerald" />
        <StatCard label="Different values" value={summary.mismatch_count} icon={<AlertTriangle size={18} />} tone="amber" />
        <StatCard label="Missing accounts" value={summary.missing_count} tone="red" />
        <StatCard label="Critical anomalies" value={summary.critical_anomalies} tone="red" />
        <StatCard label="Medium anomalies" value={summary.medium_anomalies} tone="amber" />
        <StatCard label="Low anomalies" value={summary.low_anomalies} tone="blue" />
        <StatCard label="Confidence" value={confidence} icon={<ShieldCheck size={18} />} tone="emerald" />
      </div>

      <Card>
        <CardContent className="p-5">
          <div className="text-sm font-semibold text-slate-950">Comparison Coverage</div>
          <div className="mt-4 grid gap-4 text-sm md:grid-cols-3 xl:grid-cols-6">
            <Fact label="Old extracted lines" value={summary.old_extracted_lines ?? 'Not detected'} />
            <Fact label="New extracted lines" value={summary.new_extracted_lines ?? 'Not detected'} />
            <Fact label="Comparable lines" value={comparableLines} />
            <Fact label="Ignored lines" value={summary.ignored_lines ?? 0} />
            <Fact label="Missing in old" value={summary.missing_in_old ?? 0} />
            <Fact label="Coverage" value={coveragePercent == null ? 'Not calculated' : `${coveragePercent}%`} />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardContent className="p-5">
            <div className="text-sm font-semibold text-slate-950">Risk Level: {risk.level}</div>
            <div className="mt-2 text-3xl font-semibold text-slate-950">Score: {Math.round(summary.risk_score)} / 100</div>
            <p className="mt-2 text-sm text-slate-500">{risk.explanation}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="text-sm font-semibold text-slate-950">Carry-forward consistency</div>
            <div className="mt-2 text-3xl font-semibold text-slate-950">{consistency.label}</div>
            <p className="mt-2 text-sm text-slate-500">{consistency.detail}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-5">
          <div className="text-sm font-semibold text-slate-950">Pipeline checklist</div>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {pipelineStages.map((stage) => (
              <div key={stage} className="flex items-start gap-3 rounded-md border border-slate-200 p-3">
                <CheckCircle2 className="mt-0.5 text-emerald-600" size={18} />
                <div>
                  <div className="text-sm font-medium text-slate-950">{stage}</div>
                  <div className="text-xs text-slate-500">Completed - Duration not available</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex flex-col gap-3 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-sm font-semibold text-slate-950">Next actions</div>
            <p className="mt-1 text-sm text-slate-500">Review any anomalies first, then export the audit evidence package.</p>
            {!hasReports && <p className="mt-2 text-sm text-amber-700">Run a comparison first.</p>}
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild><Link to={`/anomalies/${runId}`}>Review Anomalies</Link></Button>
            {hasReports ? (
              <>
                <Button asChild variant="secondary">
                  <a href={excelReportUrl(projectId, runId)} download><Download size={16} /> Download Excel Audit Report</a>
                </Button>
                <Button asChild variant="secondary">
                  <a href={jsonReportUrl(projectId, runId)} download><FileJson size={16} /> Download JSON Report</a>
                </Button>
              </>
            ) : (
              <>
                <Button variant="secondary" disabled><Download size={16} /> Download Excel Audit Report</Button>
                <Button variant="secondary" disabled><FileJson size={16} /> Download JSON Report</Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

function getVerdict(summary: VerificationSummary) {
  if (summary.critical_anomalies > 0) {
    return { label: 'FAIL', textClass: 'text-red-700', borderClass: 'border-l-red-600' };
  }
  if (summary.mismatch_count > 0 || summary.missing_count > 0) {
    return { label: 'NEEDS REVIEW', textClass: 'text-amber-700', borderClass: 'border-l-amber-500' };
  }
  return { label: 'PASS', textClass: 'text-emerald-700', borderClass: 'border-l-emerald-600' };
}

function getConsistency(summary: VerificationSummary) {
  if (!summary.values_checked) {
    return { label: 'Not available', detail: 'No compared financial values are available for this run.' };
  }
  const percent = (summary.ok_count / summary.values_checked) * 100;
  return {
    label: `${percent.toFixed(2)}%`,
    detail: `${summary.ok_count} / ${summary.values_checked} values correctly carried forward`,
  };
}

function formatConfidence(confidence: number | undefined, comparedValues: number) {
  if (confidence == null || (confidence === 0 && comparedValues > 0)) return 'Not calculated';
  return `${(confidence * 100).toFixed(1)}%`;
}

function getRisk(score: number, criticalAnomalies: number) {
  if (criticalAnomalies > 0 && score >= 81) return { level: 'CRITICAL', explanation: 'Critical verification issues detected.' };
  if (score >= 81) return { level: 'HIGH', explanation: 'Manual accountant review recommended.' };
  if (score >= 51) return { level: 'HIGH', explanation: 'Manual accountant review recommended.' };
  if (score >= 21) return { level: 'MEDIUM', explanation: 'Manual accountant review recommended.' };
  return { level: 'LOW', explanation: 'Low review effort expected.' };
}

function formatValue(value: string | number | null | undefined, fallback: string) {
  return value ?? fallback;
}

function Fact({ label, value }: { label: string; value: string | number }) {
  return <div><div className="text-slate-500">{label}</div><div className="mt-1 font-semibold text-slate-950">{value}</div></div>;
}
