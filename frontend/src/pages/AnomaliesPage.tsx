import { useEffect, useState } from 'react';
import { getAnomalies } from '../api/verification';
import { AnomaliesTable } from '../components/anomalies/AnomaliesTable';
import { PageHeader } from '../components/ui/Cards';
import type { Anomaly } from '../types/api';

export function AnomaliesPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const runId = localStorage.getItem('finverify_run_id') ?? '';
  const [items, setItems] = useState<Anomaly[]>([]);
  useEffect(() => { if (projectId && runId) getAnomalies(projectId, runId).then((data) => setItems(data.items)).catch(() => undefined); }, [projectId, runId]);
  return <section className="space-y-6"><PageHeader eyebrow="Review queue" title="Anomalies" description="Dense accountant-first review table with filtering, sorting, pagination, evidence access, and a side detail drawer." /><AnomaliesTable anomalies={items} /></section>;
}
