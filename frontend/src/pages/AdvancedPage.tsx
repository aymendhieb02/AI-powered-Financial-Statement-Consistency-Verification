import { useEffect, useState } from 'react';
import { listRules, listHistory } from '../api/enterprise';
import { getSettings } from '../api/settings';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { Card, CardContent } from '../components/ui/card';
import { EmptyState, PageHeader } from '../components/ui/Cards';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import type { BackendSettings } from '../types/api';

type Rule = { id?: string; rule_id?: string; name?: string; category?: string; severity?: string; expression?: string; message?: string; enabled?: boolean };
type Run = { run_id: string; timestamp?: string; created_at?: string; confidence?: { overall?: number }; results?: { risk_score?: number; comparisons?: number; validations?: number } };

export function AdvancedPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [history, setHistory] = useState<Run[]>([]);
  const [settings, setSettings] = useState<BackendSettings | null>(null);
  const cachedSummary = localStorage.getItem('finverify_last_summary');
  const summary = cachedSummary ? JSON.parse(cachedSummary) : null;

  useEffect(() => {
    listRules().then((data) => setRules(Array.isArray(data) ? data : data.rules || [])).catch(() => undefined);
    listHistory().then((data) => setHistory(Array.isArray(data) ? data : data.runs || [])).catch(() => undefined);
    getSettings().then(setSettings).catch(() => undefined);
  }, []);

  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Advanced" title="Expert tools" description="Rule engine, evidence, confidence, history, and settings remain available for expert users, but they are no longer part of the first-run workflow." />
      <Tabs defaultValue="rules">
        <TabsList>
          <TabsTrigger value="rules">Rule Engine</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          <TabsTrigger value="confidence">Confidence</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        <TabsContent value="rules" className="pt-4">
          {rules.length ? <RulesTable rules={rules} /> : <EmptyState title="No rules loaded" description="Rules will appear here when the backend rule registry is available." />}
        </TabsContent>
        <TabsContent value="evidence" className="pt-4">
          <EmptyState title="Evidence is available in reports" description="Run a comparison and download the Excel report to review line-level evidence. A PDF-location viewer can be added later." />
        </TabsContent>
        <TabsContent value="confidence" className="pt-4">
          <Card><CardContent className="grid gap-4 p-5 md:grid-cols-3"><Metric label="Overall confidence" value={summary?.overall_confidence != null ? `${Math.round(summary.overall_confidence * 100)}%` : 'No run yet'} /><Metric label="Risk score" value={summary?.risk_score ?? 'No run yet'} /><Metric label="Values checked" value={summary?.values_checked ?? 'No run yet'} /></CardContent></Card>
        </TabsContent>
        <TabsContent value="history" className="pt-4">
          {history.length ? <HistoryTable runs={history} /> : <EmptyState title="No verification history yet" description="History appears after comparison runs are recorded." />}
        </TabsContent>
        <TabsContent value="settings" className="pt-4">
          <Card><CardContent className="grid gap-4 p-5 md:grid-cols-4"><Metric label="Storage" value={settings?.storage_backend || 'local'} /><Metric label="MinIO" value={settings?.minio_configured ? 'Configured' : 'Not configured'} /><Metric label="AI" value={settings?.ai_enabled ? 'Enabled' : 'Disabled'} /><Metric label="Model" value={settings?.ollama_model || 'n/a'} /></CardContent></Card>
        </TabsContent>
      </Tabs>
    </section>
  );
}

function RulesTable({ rules }: { rules: Rule[] }) {
  return <Card className="overflow-auto"><Table><TableHeader><TableRow><TableHead>Rule ID</TableHead><TableHead>Category</TableHead><TableHead>Severity</TableHead><TableHead>Expression</TableHead><TableHead>Status</TableHead></TableRow></TableHeader><TableBody>{rules.map((rule) => <TableRow key={rule.id || rule.rule_id}><TableCell className="font-mono text-xs">{rule.id || rule.rule_id}</TableCell><TableCell>{rule.category || 'Accounting'}</TableCell><TableCell><SeverityBadge severity={rule.severity} /></TableCell><TableCell className="font-mono text-xs">{rule.expression}</TableCell><TableCell><StatusBadge status={rule.enabled === false ? 'disabled' : 'OK'} /></TableCell></TableRow>)}</TableBody></Table></Card>;
}

function HistoryTable({ runs }: { runs: Run[] }) {
  return <Card className="overflow-auto"><Table><TableHeader><TableRow><TableHead>Run</TableHead><TableHead>Timestamp</TableHead><TableHead>Comparisons</TableHead><TableHead>Risk</TableHead><TableHead>Confidence</TableHead></TableRow></TableHeader><TableBody>{runs.map((run) => <TableRow key={run.run_id}><TableCell className="font-mono text-xs">{run.run_id}</TableCell><TableCell>{run.timestamp || run.created_at || '-'}</TableCell><TableCell>{run.results?.comparisons ?? '-'}</TableCell><TableCell>{run.results?.risk_score ?? '-'}</TableCell><TableCell>{run.confidence?.overall != null ? `${Math.round(run.confidence.overall * 100)}%` : '-'}</TableCell></TableRow>)}</TableBody></Table></Card>;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div><div className="text-sm text-slate-500">{label}</div><div className="mt-1 font-semibold text-slate-950">{value}</div></div>;
}

