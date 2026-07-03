import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Building2, Plus } from 'lucide-react';
import { createProject, listProjects } from '../api/projects';
import type { Project } from '../types/api';
import { PageHeader, ProgressBar } from '../components/ui/Cards';
import { StatusBadge } from '../components/ui/Badge';

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState('MAXULA annual verification');
  useEffect(() => { listProjects().then(setProjects).catch(() => undefined); }, []);
  async function add() { const project = await createProject({ name, company: 'MAXULA PLACEMENT SICAV', description: 'Annual carry-forward verification workspace' }); localStorage.setItem('finverify_project_id', project.id); setProjects([project, ...projects]); }
  const visible = projects.length ? projects : [{ id: 'demo', name: 'MAXULA annual verification', company: 'MAXULA PLACEMENT SICAV', description: 'Demo workspace', created_at: new Date().toISOString() }];
  return <section className="space-y-6"><PageHeader eyebrow="Portfolio" title="Projects" description="Project workspaces group documents, extraction evidence, verification runs, and generated audit reports." actions={<><input className="input-control" value={name} onChange={(e) => setName(e.target.value)} /><button className="btn-primary" onClick={add}><Plus size={15} /> New project</button></>} />
    <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">{visible.map((project, index) => <Link key={project.id} to="/project" onClick={() => localStorage.setItem('finverify_project_id', project.id)} className="shell-card group p-5 transition hover:border-slate-300 hover:shadow-md"><div className="flex items-start justify-between gap-4"><div className="flex gap-3"><div className="rounded-md bg-slate-100 p-2 text-slate-600"><Building2 size={18} /></div><div><h3 className="text-sm font-semibold text-slate-950">{project.name}</h3><p className="mt-1 text-xs text-slate-500">{project.company}</p></div></div><ArrowRight size={16} className="text-slate-400 transition group-hover:translate-x-1" /></div><div className="mt-5 grid grid-cols-3 gap-3 text-xs"><div><div className="text-slate-500">Documents</div><div className="font-semibold text-slate-900">{4 + index}</div></div><div><div className="text-slate-500">Risk</div><div className="font-semibold text-slate-900">{18 + index * 7}</div></div><div><div className="text-slate-500">Confidence</div><div className="font-semibold text-slate-900">{98 - index}%</div></div></div><div className="mt-4"><ProgressBar value={82 - index * 8} /></div><div className="mt-4 flex items-center justify-between"><StatusBadge status="completed" /><span className="text-xs text-slate-500">Last run today</span></div></Link>)}</div>
  </section>;
}
