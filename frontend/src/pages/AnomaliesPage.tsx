import { useEffect, useState } from 'react';
import { getAnomalies } from '../api/verification';
import { AnomaliesTable } from '../components/anomalies/AnomaliesTable';
import type { Anomaly } from '../types/api';

export function AnomaliesPage() {
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const runId = localStorage.getItem('finverify_run_id') ?? '';
  const [items, setItems] = useState<Anomaly[]>([]);
  useEffect(() => { if (projectId && runId) getAnomalies(projectId, runId).then((data) => setItems(data.items)).catch(() => undefined); }, [projectId, runId]);
  return <section className="space-y-5"><h1 className="text-2xl font-semibold">Anomalies</h1><AnomaliesTable anomalies={items} /></section>;
}
