import { Eye } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getAnomalies } from '../api/verification';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { EmptyState, PageHeader } from '../components/ui/Cards';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '../components/ui/sheet';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import type { Anomaly, EvidenceReference } from '../types/api';

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
      <PageHeader eyebrow="Review" title="Anomalies" description="Review financial mismatches separately from extraction and label issues." />
      {items.length === 0 ? (
        <EmptyState title="No anomalies found" description="This run has no detected mismatches, missing rows, duplicate labels, or low-confidence rows." />
      ) : (
        <Card className="overflow-auto">
          <Table>
            <TableHeader><TableRow><TableHead>Severity</TableHead><TableHead>Status</TableHead><TableHead>Statement</TableHead><TableHead>Account</TableHead><TableHead>Expected</TableHead><TableHead>Actual</TableHead><TableHead>Difference</TableHead><TableHead>Issue type</TableHead><TableHead>Confidence</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={item.id || item.canonical_label + '-' + index}>
                  <TableCell><SeverityBadge severity={item.severity} /></TableCell>
                  <TableCell><StatusBadge status={item.status} /></TableCell>
                  <TableCell>{item.statement_name || item.statement}</TableCell>
                  <TableCell className="max-w-[260px] truncate">{item.canonical_label || item.old_label || item.new_label}</TableCell>
                  <TableCell>{money(item.expected_value ?? item.old_value)}</TableCell>
                  <TableCell>{money(item.actual_value ?? item.new_value)}</TableCell>
                  <TableCell>{money(item.difference ?? item.delta)}</TableCell>
                  <TableCell>{item.evidence_type ?? 'review'}</TableCell>
                  <TableCell>{Math.round((item.confidence ?? 0) * 100)}%</TableCell>
                  <TableCell><Button variant="secondary" size="sm" onClick={() => setSelected(item)}><Eye size={14} /> View</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
      <Sheet open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-4xl">
          <SheetHeader>
            <SheetTitle>{selected?.canonical_label}</SheetTitle>
            <SheetDescription>{selected?.statement_name || selected?.statement}</SheetDescription>
          </SheetHeader>
          {selected && <AnomalyDetail item={selected} />}
        </SheetContent>
      </Sheet>
    </section>
  );
}

function AnomalyDetail({ item }: { item: Anomaly }) {
  return (
    <div className="mt-6 space-y-5 text-sm">
      <div className="grid gap-3 md:grid-cols-2"><Detail label="Status" value={item.status} /><Detail label="Severity" value={item.severity} /><Detail label="Expected value" value={money(item.expected_value ?? item.old_value)} /><Detail label="Actual value" value={money(item.actual_value ?? item.new_value)} /><Detail label="Difference" value={money(item.difference ?? item.delta)} /><Detail label="Difference %" value={item.difference_percent == null ? '-' : item.difference_percent.toFixed(2) + '%'} /><Detail label="Confidence" value={Math.round((item.confidence ?? 0) * 100) + '%'} /><Detail label="Matching method" value={item.matching_method || 'deterministic'} /></div>
      <Card><CardContent className="p-4"><div className="font-semibold text-slate-950">Explanation</div><p className="mt-2 leading-6 text-slate-600">{item.explanation || item.note || 'This comparison row requires accountant review.'}</p><div className="mt-4 grid gap-3 md:grid-cols-2"><Detail label="Technical reason" value={item.technical_reason || '-'} /><Detail label="Accountant reason" value={item.accountant_reason || '-'} /></div><div className="mt-4 rounded-md bg-amber-50 p-3 text-amber-900"><span className="font-semibold">Recommended action: </span>{item.recommended_action || 'Inspect old and new evidence side by side.'}</div></CardContent></Card>
      <div className="grid gap-4 lg:grid-cols-2"><EvidencePanel title="Old document evidence" label={item.account_label_old || item.old_label || '-'} value={item.old_current_value ?? item.old_value} evidence={item.old_evidence} fallbackLine={item.old_line_text} page={item.old_page} section={item.old_section} /><EvidencePanel title="New document evidence" label={item.account_label_new || item.new_label || '-'} value={item.new_previous_value ?? item.new_value} evidence={item.new_evidence} fallbackLine={item.new_line_text} page={item.new_page} section={item.new_section} /></div>
    </div>
  );
}

function EvidencePanel({ title, label, value, evidence, fallbackLine, page, section }: { title: string; label: string; value?: number | null; evidence?: EvidenceReference | string; fallbackLine?: string | null; page?: number | null; section?: string | null }) {
  const evidenceObject = typeof evidence === 'string' ? undefined : evidence;
  const raw = (typeof evidence === 'string' ? evidence : evidenceObject?.raw_text) || fallbackLine || label;
  return <Card><CardContent className="p-4"><div className="font-semibold text-slate-950">{title}</div><div className="mt-3 grid gap-2"><Detail label="Label" value={label} /><Detail label="Value" value={money(value)} /><Detail label="Page" value={String(evidenceObject?.page ?? page ?? 'Not available')} /><Detail label="Section" value={evidenceObject?.section || section || 'Not available'} /></div><div className="mt-4 rounded-md bg-slate-50 p-3"><div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Raw extracted line</div><p className="mt-2 whitespace-pre-wrap leading-6 text-slate-700">{raw || 'Raw line not available.'}</p></div></CardContent></Card>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-4 border-b border-slate-100 pb-2"><span className="text-slate-500">{label}</span><span className="max-w-[65%] text-right font-medium text-slate-900">{value}</span></div>;
}
