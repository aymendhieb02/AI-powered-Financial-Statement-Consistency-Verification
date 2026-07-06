import { Link } from 'react-router-dom';
import { useOutletContext, useParams } from 'react-router-dom';
import { FileText, GitCompareArrows, ShieldCheck } from 'lucide-react';
import type { ProjectDetail } from '../types/api';
import { useProject } from '../context/ProjectContext';
import { StatCard } from '../components/ui/Cards';
import { ReportActions } from '../components/reports/ReportActions';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

type OutletContext = { project: ProjectDetail | null };

export function ProjectOverviewPage() {
  const { projectId } = useParams();
  const { runId, projectPath } = useProject();
  const { project } = useOutletContext<OutletContext>();

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Documents" value={project?.document_count ?? 0} icon={<FileText size={18} />} />
        <StatCard label="Latest risk" value={project?.latest_risk_score ?? '-'} icon={<GitCompareArrows size={18} />} tone="amber" />
        <StatCard label="Latest confidence" value={project?.latest_confidence != null ? `${project.latest_confidence}%` : '-'} icon={<ShieldCheck size={18} />} tone="emerald" />
        <StatCard label="Latest run" value={project?.latest_run_status ?? 'none'} />
      </div>
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="section-title">Next steps</div>
          <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-600">
            <li>Upload exactly two annual PDFs in Documents.</li>
            <li>Select old and new documents on the Verification page.</li>
            <li>Run comparison and review anomalies.</li>
            <li>Download Excel and JSON reports.</li>
          </ol>
          <div className="flex flex-wrap gap-2">
            <Button asChild><Link to={projectPath('documents')}>Go to Documents</Link></Button>
            <Button variant="secondary" asChild><Link to={projectPath('verification')}>Run verification</Link></Button>
            <Button variant="secondary" asChild><Link to={projectPath('anomalies')}>Review anomalies</Link></Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="space-y-3 p-5">
          <div className="section-title">Latest reports</div>
          <ReportActions projectId={projectId} runId={runId} />
        </CardContent>
      </Card>
    </div>
  );
}
