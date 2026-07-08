import { Eye } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getAnomalies } from '../api/verification';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/button';
import { EmptyState, PageHeader } from '../components/ui/Cards';
import { Card } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import type { Anomaly } from '../types/api';

function money(value?: number | null) {
  return typeof value === 'number' ? new Intl.NumberFormat('fr-FR').format(value) : '-';
}

function accountLabel(item: Anomaly) {
  return item.account_label_new || item.account_label_old || item.new_label || item.old_label || item.canonical_label.replace(/.*__/, '').replace(/_/g, ' ');
}

export function AnomaliesPage() {
  const { runId = '' } = useParams();
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [items, setItems] = useState<Anomaly[]>([]);

  useEffect(() => {
    if (projectId && runId && runId !== 'latest') {
      getAnomalies(projectId, runId).then((data) => setItems(data.items)).catch(() => undefined);
    }
  }, [projectId, runId]);

  if (!projectId || runId === 'latest') {
    return <EmptyState title='No anomalies yet' description='Run a comparison first, then return here to review anomalies.' action={<Button asChild><Link to='/compare'>Compare documents</Link></Button>} />;
  }

  return (
    <section className='space-y-6'>
      <PageHeader eyebrow='Review' title='Anomalies' description='Every review item links to evidence from both annual reports so the accountant can inspect the exact extracted context.' />
      {items.length === 0 ? (
        <EmptyState title='No anomalies found' description='This run has no detected mismatches, missing accounts, duplicate labels, or low-confidence rows.' />
      ) : (
        <Card className='overflow-auto'>
          <Table>
            <TableHeader><TableRow><TableHead>Severity</TableHead><TableHead>Status</TableHead><TableHead>Statement</TableHead><TableHead>Account</TableHead><TableHead>Expected</TableHead><TableHead>Actual</TableHead><TableHead>Difference</TableHead><TableHead>Issue</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={item.id || item.canonical_label + '-' + index}>
                  <TableCell><SeverityBadge severity={item.severity} /></TableCell>
                  <TableCell><StatusBadge status={item.status} /></TableCell>
                  <TableCell>{item.statement_name || item.statement || 'Not detected'}</TableCell>
                  <TableCell className='max-w-[280px] truncate'>{accountLabel(item)}</TableCell>
                  <TableCell>{money(item.expected_value ?? item.old_value)}</TableCell>
                  <TableCell>{money(item.actual_value ?? item.new_value)}</TableCell>
                  <TableCell>{money(item.difference ?? item.delta)}</TableCell>
                  <TableCell>{item.evidence_type || item.status || 'review'}</TableCell>
                  <TableCell><Button asChild variant='secondary' size='sm'><Link to={'/evidence/' + runId + '/' + encodeURIComponent(item.id || '')}><Eye size={14} /> Inspect</Link></Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </section>
  );
}
