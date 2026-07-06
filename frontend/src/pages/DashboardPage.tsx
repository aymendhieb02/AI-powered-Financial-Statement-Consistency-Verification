import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderKanban } from 'lucide-react';
import { listProjects } from '../api/projects';
import { getApiErrorMessage } from '../api/client';
import type { Project } from '../types/api';
import { useProject } from '../context/ProjectContext';
import { PageHeader, StatCard } from '../components/ui/Cards';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

export function DashboardPage() {
  const { openProject } = useProject();
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProjects()
      .then(setProjects)
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load dashboard data')));
  }, []);

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Command center"
        title="Financial verification dashboard"
        description="Create a project, upload two annual PDFs, run comparison, review anomalies, and download reports."
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Projects" value={projects.length} detail="Active verification workspaces" icon={<FolderKanban size={18} />} />
      </div>
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="section-title">Accountant workflow</div>
          <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-600">
            <li>Create or open a project.</li>
            <li>Upload exactly two annual SICAV PDFs.</li>
            <li>Select old and new documents, then run comparison.</li>
            <li>Review anomalies and download Excel/JSON reports.</li>
          </ol>
          <div className="flex flex-wrap gap-2">
            <Button asChild><Link to="/projects">Open projects</Link></Button>
            {projects[0] && (
              <Button variant="secondary" onClick={() => openProject(projects[0].id, 'documents')}>
                Continue latest project
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
