import { useEffect, useState } from 'react';
import { createProject, listProjects } from '../api/projects';
import type { Project } from '../types/api';

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState('MAXULA PLACEMENT SICAV');
  const [description, setDescription] = useState('Annual SICAV consistency check');
  async function refresh() { setProjects(await listProjects()); }
  useEffect(() => { refresh().catch(() => undefined); }, []);
  async function submit(event: React.FormEvent) { event.preventDefault(); const project = await createProject({ name, company: name, description }); localStorage.setItem('finverify_project_id', project.id); await refresh(); }
  return <section className="space-y-5"><h1 className="text-2xl font-semibold">Projects</h1><form onSubmit={submit} className="grid gap-3 rounded-lg border border-audit-line bg-white p-4 md:grid-cols-3"><input className="rounded border border-audit-line px-3 py-2" value={name} onChange={(e) => setName(e.target.value)} /><input className="rounded border border-audit-line px-3 py-2" value={description} onChange={(e) => setDescription(e.target.value)} /><button className="rounded bg-audit-accent px-4 py-2 text-white">Create Project</button></form><div className="rounded-lg border border-audit-line bg-white"><table className="w-full text-left text-sm"><thead className="bg-audit-panel text-audit-muted"><tr><th className="px-4 py-3">Name</th><th>Company</th><th>Description</th><th></th></tr></thead><tbody>{projects.map((project) => <tr key={project.id} className="border-t border-audit-line"><td className="px-4 py-3 font-medium">{project.name}</td><td>{project.company}</td><td>{project.description}</td><td><button className="rounded border border-audit-line px-3 py-1" onClick={() => localStorage.setItem('finverify_project_id', project.id)}>Select</button></td></tr>)}</tbody></table></div></section>;
}
