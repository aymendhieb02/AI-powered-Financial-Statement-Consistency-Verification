import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { History } from 'lucide-react';
import { getApiErrorMessage } from '../api/client';
import { listProjectRuns } from '../api/verification';
import type { VerificationRunListItem } from '../types/api';
import { StatusBadge } from '../components/ui/Badge';
import { Card } from '../components/ui/card';

export function VerificationHistoryPage() {
  const { projectId: routeProjectId } = useParams();
  const [runs, setRuns] = useState<VerificationRunListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!routeProjectId) {
      setLoading(false);
      return;
    }
    listProjectRuns(routeProjectId)
      .then(setRuns)
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load verification history')))
      .finally(() => setLoading(false));
  }, [routeProjectId]);

  if (!routeProjectId) {
    return <Card className="p-4 text-sm text-slate-500">Select a project to view verification history.</Card>;
  }

  return (
    <div className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      {loading ? (
        <Card className="p-6 text-sm text-slate-500">Loading verification history...</Card>
      ) : runs.length === 0 ? (
        <Card className="p-6 text-sm text-slate-500">No verification runs recorded for this project yet.</Card>
      ) : (
        runs.map((run) => (
          <Card key={run.run_id} className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex gap-3">
                <div className="rounded-md bg-slate-100 p-2 text-slate-600"><History size={17} /></div>
                <div>
                  <div className="font-mono text-sm font-semibold text-slate-950">{run.run_id}</div>
                  <div className="mt-1 text-xs text-slate-500">{new Date(run.created_at).toLocaleString()}</div>
                </div>
              </div>
              <StatusBadge status={run.status} />
            </div>
            <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
              <Metric label="Values compared" value={run.summary.values_checked ?? 0} />
              <Metric label="Critical" value={run.summary.critical_anomalies ?? 0} />
              <Metric label="Risk score" value={run.summary.risk_score ?? 0} />
              <Metric label="Status" value={run.status} />
            </div>
          </Card>
        ))
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div><div className="text-slate-500">{label}</div><div className="mt-1 font-semibold text-slate-950">{value}</div></div>;
}
