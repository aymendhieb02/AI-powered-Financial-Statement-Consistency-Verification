import { Download, FileJson, FileSpreadsheet } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { excelReportUrl, jsonReportUrl } from '../api/reports';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { EmptyState, PageHeader } from '../components/ui/Cards';
import type { VerificationSummary } from '../types/api';

export function ReportsPage() {
  const { runId = '' } = useParams();
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const cached = localStorage.getItem('finverify_last_summary');
  const summary = cached ? JSON.parse(cached) as VerificationSummary : null;
  const hasReport = Boolean(projectId && runId && runId !== 'latest' && summary?.report_paths?.length);

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Reports"
        title="Download verification reports"
        description="Export the accountant audit workbook or the machine-readable verification payload."
      />
      {hasReport ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardContent className="space-y-4 p-5">
              <div className="flex items-start gap-3">
                <FileSpreadsheet className="mt-0.5 text-emerald-700" size={20} />
                <div>
                  <div className="text-sm font-semibold text-slate-950">Excel Audit Report</div>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Contains comparison results, anomalies, evidence, rule results, and confidence.
                  </p>
                </div>
              </div>
              <Button asChild>
                <a href={excelReportUrl(projectId, runId)} download><Download size={16} /> Download Excel Audit Report</a>
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="space-y-4 p-5">
              <div className="flex items-start gap-3">
                <FileJson className="mt-0.5 text-blue-700" size={20} />
                <div>
                  <div className="text-sm font-semibold text-slate-950">JSON Verification Payload</div>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Machine-readable verification result for integrations, audit archives, or future review.
                  </p>
                </div>
              </div>
              <Button asChild variant="secondary">
                <a href={jsonReportUrl(projectId, runId)} download><Download size={16} /> Download JSON Report</a>
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : (
        <EmptyState
          title="Run a comparison first."
          description="Excel and JSON report downloads are enabled after FinVerify completes a two-document comparison."
          action={<Button asChild><Link to="/compare">Go to Compare Documents</Link></Button>}
        />
      )}
    </section>
  );
}
