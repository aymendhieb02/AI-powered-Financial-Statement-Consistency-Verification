import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Building2, Plus } from 'lucide-react';
import { createProject, listProjects } from '../api/projects';
import { getApiErrorMessage } from '../api/client';
import type { Project } from '../types/api';
import { useProject } from '../context/ProjectContext';
import { PageHeader } from '../components/ui/Cards';
import { StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';

export function ProjectsPage() {
  const { openProject } = useProject();
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState('MAXULA annual verification');
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProjects()
      .then(setProjects)
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load projects')))
      .finally(() => setLoading(false));
  }, []);

  async function add() {
    setCreating(true);
    setError(null);
    try {
      const project = await createProject({
        name,
        company: 'MAXULA PLACEMENT SICAV',
        description: 'Annual carry-forward verification workspace',
      });
      setProjects((prev) => [project, ...prev]);
      openProject(project.id);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to create project'));
    } finally {
      setCreating(false);
    }
  }

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Portfolio"
        title="Projects"
        description="Create a workspace, upload two annual PDFs, run comparison, review anomalies, and download reports."
        actions={
          <>
            <Input className="w-64" value={name} onChange={(e) => setName(e.target.value)} />
            <Button onClick={add} disabled={creating || !name.trim()}>
              <Plus size={15} /> {creating ? 'Creating...' : 'New project'}
            </Button>
          </>
        }
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-500">Loading projects...</p>
      ) : projects.length === 0 ? (
        <Card className="p-8 text-center text-sm text-slate-500">No projects yet. Create your first verification workspace.</Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
          {projects.map((project) => (
            <button key={project.id} type="button" onClick={() => openProject(project.id)} className="text-left">
              <Card className="group p-5 transition hover:border-slate-300 hover:shadow-md">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-3">
                    <div className="rounded-md bg-slate-100 p-2 text-slate-600"><Building2 size={18} /></div>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-950">{project.name}</h3>
                      <p className="mt-1 text-xs text-slate-500">{project.company}</p>
                    </div>
                  </div>
                  <ArrowRight size={16} className="text-slate-400 transition group-hover:translate-x-1" />
                </div>
                <div className="mt-4 flex items-center justify-between">
                  <StatusBadge status="completed" />
                  <span className="text-xs text-slate-500">{new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </Card>
            </button>
          ))}
        </div>
      )}
      <p className="text-sm text-slate-500">
        Workflow: <Link className="underline" to="/projects">create project</Link> → upload 2 PDFs → run comparison → review anomalies → download report.
      </p>
    </section>
  );
}
