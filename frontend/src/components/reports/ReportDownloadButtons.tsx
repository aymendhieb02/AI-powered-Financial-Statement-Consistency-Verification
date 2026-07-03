import { Download } from 'lucide-react';
import { excelReportUrl, jsonReportUrl } from '../../api/reports';

export function ReportDownloadButtons({ projectId, runId }: { projectId?: string; runId?: string }) {
  const disabled = !projectId || !runId;
  const baseClass = 'inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium ';
  return <div className="flex gap-3">
    <a className={baseClass + (disabled ? 'pointer-events-none bg-slate-200 text-slate-500' : 'bg-audit-accent text-white')} href={disabled ? '#' : excelReportUrl(projectId, runId)}><Download size={16} />Download Excel Report</a>
    <a className={baseClass + (disabled ? 'pointer-events-none bg-slate-200 text-slate-500' : 'border border-audit-line bg-white text-audit-ink')} href={disabled ? '#' : jsonReportUrl(projectId, runId)}><Download size={16} />Download JSON Report</a>
  </div>;
}
