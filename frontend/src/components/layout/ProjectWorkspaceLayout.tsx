import { Outlet, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getProject } from '../../api/projects';
import { getApiErrorMessage } from '../../api/client';
import type { ProjectDetail } from '../../types/api';
import { useProject } from '../../context/ProjectContext';
import { PageHeader } from '../ui/Cards';
import { ProjectWorkspaceNav } from './ProjectWorkspaceNav';
import { Card, CardContent } from '../ui/card';

export function ProjectWorkspaceLayout() {
  const { projectId: routeProjectId } = useParams();
  const { setProjectId, setRunId } = useProject();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!routeProjectId) return;
    setProjectId(routeProjectId);
    getProject(routeProjectId)
      .then((data) => {
        setProject(data);
        if (data.latest_run_id) setRunId(data.latest_run_id);
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Project not found')));
  }, [routeProjectId, setProjectId, setRunId]);

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Workspace"
        title={project?.name ?? 'Project workspace'}
        description={project?.description || 'Upload two annual PDFs, run comparison, review anomalies, and download reports.'}
      />
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 text-sm text-red-800">{error}</CardContent>
        </Card>
      )}
      <ProjectWorkspaceNav />
      <Outlet context={{ project }} />
    </section>
  );
}
