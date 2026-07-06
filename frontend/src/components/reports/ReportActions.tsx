import { Download, FileJson, FileSpreadsheet } from 'lucide-react';
import { excelReportUrl, jsonReportUrl } from '../../api/reports';
import { Button } from '../ui/button';

type Props = {
  projectId?: string | null;
  runId?: string | null;
  compact?: boolean;
};

export function ReportActions({ projectId, runId, compact }: Props) {
  const disabled = !projectId || !runId;
  const hint = 'No report generated yet. Run verification first.';

  if (disabled) {
    return (
      <div className="space-y-2">
        <div className="flex flex-wrap gap-3">
          <Button disabled><FileSpreadsheet size={15} /> Excel report</Button>
          <Button variant="secondary" disabled><FileJson size={15} /> JSON report</Button>
        </div>
        <p className="text-sm text-slate-500">{hint}</p>
      </div>
    );
  }

  const excelHref = excelReportUrl(projectId, runId);
  const jsonHref = jsonReportUrl(projectId, runId);

  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        <Button asChild size="sm"><a href={excelHref} download><FileSpreadsheet size={14} /> Excel</a></Button>
        <Button variant="secondary" asChild size="sm"><a href={jsonHref} download><FileJson size={14} /> JSON</a></Button>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-3">
      <Button asChild><a href={excelHref} download><Download size={16} /> Download Excel Report</a></Button>
      <Button variant="secondary" asChild><a href={jsonHref} download><Download size={16} /> Download JSON Report</a></Button>
    </div>
  );
}
