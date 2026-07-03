import { ReportDownloadButtons } from '../components/reports/ReportDownloadButtons';

export function ReportsPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const runId = localStorage.getItem('finverify_run_id') ?? '';
  return <section className="space-y-5"><h1 className="text-2xl font-semibold">Reports</h1><div className="rounded-lg border border-audit-line bg-white p-5"><ReportDownloadButtons projectId={projectId} runId={runId} /></div></section>;
}
