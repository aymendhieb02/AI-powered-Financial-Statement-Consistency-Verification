import { Eye } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getAnomalies } from '../api/verification';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { EmptyState, PageHeader } from '../components/ui/Cards';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '../components/ui/sheet';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import type { Anomaly } from '../types/api';

function money(value?: number | null) {
  return typeof value === 'number' ? new Intl.NumberFormat('fr-FR').format(value) : '-';
}

export function AnomaliesPage() {
  const { runId = '' } = useParams();
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [items, setItems] = useState<Anomaly[]>([]);
  const [selected, setSelected] = useState<Anomaly | null>(null);

  useEffect(() => {
    if (projectId && runId && runId !== 'latest') {
      getAnomalies(projectId, runId).then((data) => setItems(data.items)).catch(() => undefined);
    }
  }, [projectId, runId]);

  if (!projectId || runId === 'latest') {
    return <EmptyState title="No anomalies yet" description="Run a comparison first, then return here to review anomalies." action={<Button asChild><Link to="/compare">Compare documents</Link></Button>} />;
  }

  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Review" title="Anomalies" description="Only issues requiring accountant attention are shown here." />
      {items.length === 0 ? (
        <EmptyState title="No anomalies found" description="This run has no detected mismatches or missing rows." />
      ) : (
        <Card className="overflow-auto">
          <Table>
            <TableHeader><TableRow><TableHead>Severity</TableHead><TableHead>Status</TableHead><TableHead>Statement</TableHead><TableHead>Account label</TableHead><TableHead>Old value</TableHead><TableHead>New value</TableHead><TableHead>Difference</TableHead><TableHead>Page</TableHead><TableHead>Confidence</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={`${item.canonical_label}-${index}`}>
                  <TableCell><SeverityBadge severity={item.severity} /></TableCell>
                  <TableCell><StatusBadge status={item.status} /></TableCell>
                  <TableCell>{item.statement}</TableCell>
                  <TableCell>{item.canonical_label || item.old_label || item.new_label}</TableCell>
                  <TableCell>{money(item.old_value)}</TableCell>
                  <TableCell>{money(item.new_value)}</TableCell>
                  <TableCell>{money(item.delta)}</TableCell>
                  <TableCell>{item.old_evidence || item.new_evidence ? 'Available' : '-'}</TableCell>
                  <TableCell>{Math.round((item.confidence ?? 0) * 100)}%</TableCell>
                  <TableCell><Button variant="secondary" size="sm" onClick={() => setSelected(item)}><Eye size={14} /> View</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
      <Sheet open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>{selected?.canonical_label}</SheetTitle>
            <SheetDescription>{selected?.statement}</SheetDescription>
          </SheetHeader>
          {selected && (
            <div className="mt-6 space-y-3 text-sm">
              <Detail label="Severity" value={selected.severity} />
              <Detail label="Status" value={selected.status} />
              <Detail label="Old value" value={money(selected.old_value)} />
              <Detail label="New value" value={money(selected.new_value)} />
              <Detail label="Difference" value={money(selected.delta)} />
              <Detail label="Confidence" value={`${Math.round((selected.confidence ?? 0) * 100)}%`} />
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="font-medium text-slate-950">Evidence</div>
                <p className="mt-1 text-slate-500">{selected.old_evidence || selected.new_evidence ? 'Evidence metadata is available in the generated report.' : 'No page-level evidence was captured for this anomaly yet.'}</p>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-4 border-b border-slate-100 pb-2"><span className="text-slate-500">{label}</span><span className="text-right font-medium text-slate-900">{value}</span></div>;
}
