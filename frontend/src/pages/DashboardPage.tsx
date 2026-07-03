import { useEffect, useState } from 'react';
import { listProjects } from '../api/projects';
import { SummaryCards } from '../components/dashboard/SummaryCards';

export function DashboardPage() {
  const [count, setCount] = useState(0);
  useEffect(() => { listProjects().then((projects) => setCount(projects.length)).catch(() => undefined); }, []);
  return <section className="space-y-5"><h1 className="text-2xl font-semibold">Dashboard</h1><SummaryCards cards={[{ label: 'Total projects', value: count }, { label: 'Latest verification runs', value: '-' }, { label: 'Total anomalies', value: '-' }, { label: 'Average risk score', value: '-' }]} /><div className="rounded-lg border border-audit-line bg-white p-5 text-sm text-audit-muted">Select or create a project, upload PDFs, run verification, review anomalies, then download the audit report.</div></section>;
}
