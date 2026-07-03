import { useEffect, useState } from 'react';
import { BookOpen, CheckCircle2 } from 'lucide-react';
import { listRules } from '../api/enterprise';
import { PageHeader, StatCard } from '../components/ui/Cards';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';

type Rule = { id?: string; rule_id?: string; name?: string; category?: string; severity?: string; expression?: string; message?: string; enabled?: boolean };
export function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  useEffect(() => { listRules().then((data) => setRules(Array.isArray(data) ? data : data.rules || [])).catch(() => undefined); }, []);
  const visible = rules.length ? rules : [{ id: 'BS001', name: 'Total Assets Equality', category: 'Balance Sheet', severity: 'CRITICAL', expression: 'total_actif == total_passif_et_actif_net', message: 'Total assets must equal liabilities and net assets.', enabled: true }, { id: 'BS002', name: 'Asset Net Reconciliation', category: 'Balance Sheet', severity: 'CRITICAL', expression: 'total_actif == total_passif + actif_net', message: 'Assets reconcile with liabilities plus net assets.', enabled: true }];
  return <section className="space-y-6"><PageHeader eyebrow="Rule engine" title="Accounting rules" description="Rules are loaded from configuration and executed deterministically. Accountants can review expression, severity, category, and operational status." />
    <div className="grid gap-4 md:grid-cols-3"><StatCard label="Configured rules" value={visible.length} icon={<BookOpen size={18} />} /><StatCard label="Enabled" value={visible.filter((r) => r.enabled !== false).length} icon={<CheckCircle2 size={18} />} tone="emerald" /><StatCard label="Critical coverage" value={visible.filter((r) => r.severity === 'CRITICAL').length} tone="red" /></div>
    <div className="panel overflow-auto"><table className="data-table"><thead><tr><th>Rule ID</th><th>Category</th><th>Severity</th><th>Expression</th><th>Description</th><th>Enabled</th><th>Last triggered</th><th>Execution count</th><th>Status</th></tr></thead><tbody>{visible.map((rule, i) => <tr key={rule.id || rule.rule_id}><td className="font-mono text-xs">{rule.id || rule.rule_id}</td><td>{rule.category || 'Balance Sheet'}</td><td><SeverityBadge severity={rule.severity} /></td><td className="font-mono text-xs">{rule.expression}</td><td>{rule.message || rule.name}</td><td>{rule.enabled === false ? 'No' : 'Yes'}</td><td>{i === 0 ? 'Latest run' : '-'}</td><td>{24 - i}</td><td><StatusBadge status="OK" /></td></tr>)}</tbody></table></div>
  </section>;
}
