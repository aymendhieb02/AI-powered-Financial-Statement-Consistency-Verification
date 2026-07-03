import { Download } from 'lucide-react';
import { excelReportUrl, jsonReportUrl } from '../../api/reports';
import { Button } from '../ui/button';

export function ReportDownloadButtons({ projectId, runId }: { projectId?: string; runId?: string }) {
  const disabled = !projectId || !runId;
  if (disabled) {
    return (
      <div className="flex flex-wrap gap-3">
        <Button disabled><Download size={16} />Download Excel Report</Button>
        <Button variant="secondary" disabled><Download size={16} />Download JSON Report</Button>
      </div>
    );
  }
  return (
    <div className="flex flex-wrap gap-3">
      <Button asChild>
        <a href={excelReportUrl(projectId, runId)}><Download size={16} />Download Excel Report</a>
      </Button>
      <Button variant="secondary" asChild>
        <a href={jsonReportUrl(projectId, runId)}><Download size={16} />Download JSON Report</a>
      </Button>
    </div>
  );
}
