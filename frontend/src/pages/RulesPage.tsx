import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { BookOpen } from 'lucide-react';
import { listRules } from '../api/enterprise';
import { getApiErrorMessage } from '../api/client';
import { StatCard } from '../components/ui/Cards';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { Card } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

type Rule = { id?: string; rule_id?: string; name?: string; category?: string; severity?: string; expression?: string; message?: string; enabled?: boolean };

export function RulesPage() {
  const { projectId } = useParams();
  const [rules, setRules] = useState<Rule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listRules()
      .then((data) => setRules(Array.isArray(data) ? data : data.rules || []))
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load rules')))
      .finally(() => setLoading(false));
  }, []);

  if (!projectId) {
    return <Card className="p-4 text-sm text-slate-500">Select a project workspace to review rules.</Card>;
  }

  return (
    <div className="space-y-6">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Configured rules" value={rules.length} icon={<BookOpen size={18} />} />
        <StatCard label="Enabled" value={rules.filter((r) => r.enabled !== false).length} tone="emerald" />
        <StatCard label="Critical coverage" value={rules.filter((r) => r.severity === 'CRITICAL').length} tone="red" />
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
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={7} className="py-8 text-center text-sm text-slate-500">Loading rules...</TableCell></TableRow>
            ) : rules.length === 0 ? (
              <TableRow><TableCell colSpan={7} className="py-8 text-center text-sm text-slate-500">No rules configured.</TableCell></TableRow>
            ) : rules.map((rule) => (
              <TableRow key={rule.id || rule.rule_id}>
                <TableCell className="font-mono text-xs">{rule.id || rule.rule_id}</TableCell>
                <TableCell>{rule.category || 'Balance Sheet'}</TableCell>
                <TableCell><SeverityBadge severity={rule.severity} /></TableCell>
                <TableCell className="font-mono text-xs">{rule.expression}</TableCell>
                <TableCell>{rule.message || rule.name}</TableCell>
                <TableCell>{rule.enabled === false ? 'No' : 'Yes'}</TableCell>
                <TableCell><StatusBadge status="OK" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
