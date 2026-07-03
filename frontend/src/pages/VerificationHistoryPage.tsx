import { useEffect, useState } from 'react';
import { GitCompareArrows, History } from 'lucide-react';
import { listHistory } from '../api/enterprise';
import { PageHeader } from '../components/ui/Cards';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';

type Run = { run_id: string; timestamp: string; documents?: string[]; confidence?: { overall?: number }; results?: { risk_score?: number; comparisons?: number; validations?: number }; new_anomalies?: string[]; resolved_anomalies?: string[] };

export function VerificationHistoryPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  useEffect(() => { listHistory().then((data) => setRuns(Array.isArray(data) ? data : data.runs || [])).catch(() => undefined); }, []);
  const visible = runs.length ? runs : [{ run_id: 'run-2024-06', timestamp: new Date().toISOString(), documents: ['MAXULA_2024.pdf'], confidence: { overall: 0.984 }, results: { risk_score: 18, comparisons: 642, validations: 18 }, new_anomalies: ['actif_net'], resolved_anomalies: [] }];
  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Audit trail"
        title="Verification history"
        description="Immutable run timeline with confidence changes, risk score movement, new anomalies, resolved anomalies, and report lineage."
        actions={<Button variant="secondary"><GitCompareArrows size={15} /> Compare runs</Button>}
      />
      <div className="space-y-3">
        {visible.map((run) => (
          <Card key={run.run_id} className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex gap-3">
                <div className="rounded-md bg-slate-100 p-2 text-slate-600"><History size={17} /></div>
                <div>
                  <div className="font-mono text-sm font-semibold text-slate-950">{run.run_id}</div>
                  <div className="mt-1 text-xs text-slate-500">{new Date(run.timestamp).toLocaleString()} - {run.documents?.length || 0} documents</div>
                </div>
              </div>
              <StatusBadge status="completed" />
            </div>
            <div className="mt-4 grid gap-3 text-sm md:grid-cols-5">
              <Metric label="Rules" value={run.results?.validations ?? 0} />
              <Metric label="Comparisons" value={run.results?.comparisons ?? 0} />
              <Metric label="Confidence" value={Math.round((run.confidence?.overall ?? 1) * 100) + '%'} />
              <Metric label="Risk score" value={run.results?.risk_score ?? 0} />
              <div>
                <div className="text-slate-500">Changes</div>
                <div className="mt-1 flex gap-2">
                  <Badge tone="warning">+{run.new_anomalies?.length || 0}</Badge>
                  <Badge tone="success">-{run.resolved_anomalies?.length || 0}</Badge>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div><div className="text-slate-500">{label}</div><div className="mt-1 font-semibold text-slate-950">{value}</div></div>;
}
