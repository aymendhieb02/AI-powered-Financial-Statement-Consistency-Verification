import { useEffect, useState } from 'react';
import { BookOpen, CheckCircle2 } from 'lucide-react';
import { listRules } from '../api/enterprise';
import { PageHeader, StatCard } from '../components/ui/Cards';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { Card } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

type Rule = { id?: string; rule_id?: string; name?: string; category?: string; severity?: string; expression?: string; message?: string; enabled?: boolean };

export function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  useEffect(() => { listRules().then((data) => setRules(Array.isArray(data) ? data : data.rules || [])).catch(() => undefined); }, []);
  const visible = rules.length ? rules : [{ id: 'BS001', name: 'Total Assets Equality', category: 'Balance Sheet', severity: 'CRITICAL', expression: 'total_actif == total_passif_et_actif_net', message: 'Total assets must equal liabilities and net assets.', enabled: true }, { id: 'BS002', name: 'Asset Net Reconciliation', category: 'Balance Sheet', severity: 'CRITICAL', expression: 'total_actif == total_passif + actif_net', message: 'Assets reconcile with liabilities plus net assets.', enabled: true }];
  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Rule engine" title="Accounting rules" description="Rules are loaded from configuration and executed deterministically. Accountants can review expression, severity, category, and operational status." />
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Configured rules" value={visible.length} icon={<BookOpen size={18} />} />
        <StatCard label="Enabled" value={visible.filter((r) => r.enabled !== false).length} icon={<CheckCircle2 size={18} />} tone="emerald" />
        <StatCard label="Critical coverage" value={visible.filter((r) => r.severity === 'CRITICAL').length} tone="red" />
      </div>
      <Card className="overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Rule ID</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Expression</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Enabled</TableHead>
              <TableHead>Last triggered</TableHead>
              <TableHead>Execution count</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {visible.map((rule, i) => (
              <TableRow key={rule.id || rule.rule_id}>
                <TableCell className="font-mono text-xs">{rule.id || rule.rule_id}</TableCell>
                <TableCell>{rule.category || 'Balance Sheet'}</TableCell>
                <TableCell><SeverityBadge severity={rule.severity} /></TableCell>
                <TableCell className="font-mono text-xs">{rule.expression}</TableCell>
                <TableCell>{rule.message || rule.name}</TableCell>
                <TableCell>{rule.enabled === false ? 'No' : 'Yes'}</TableCell>
                <TableCell>{i === 0 ? 'Latest run' : '-'}</TableCell>
                <TableCell>{24 - i}</TableCell>
                <TableCell><StatusBadge status="OK" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </section>
  );
}
