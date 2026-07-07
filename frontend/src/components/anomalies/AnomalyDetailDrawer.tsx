import { X } from 'lucide-react';
import type { Anomaly, EvidenceReference } from '../../types/api';
import { SeverityBadge, StatusBadge } from '../ui/Badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';

function money(value?: number | null) {
  return typeof value === 'number' ? new Intl.NumberFormat('fr-FR').format(value) : '-';
}

function percent(item: Anomaly) {
  if (!item.old_value || Number(item.old_value) === 0) return '-';
  return (((item.delta ?? 0) / Number(item.old_value)) * 100).toFixed(2) + '%';
}

export function AnomalyDetailDrawer({ anomaly, onClose }: { anomaly: Anomaly; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-950/20" onClick={onClose}>
      <aside
        className="h-full w-full max-w-md overflow-y-auto border-l border-slate-200 bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="section-title">Anomaly detail</div>
            <h2 className="mt-1 text-lg font-semibold text-slate-950">{anomaly.canonical_label}</h2>
            <div className="mt-2 flex gap-2">
              <SeverityBadge severity={anomaly.severity} />
              <StatusBadge status={anomaly.status} />
            </div>
          </div>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onClose} aria-label="Close detail">
            <X size={16} />
          </Button>
        </div>
        <div className="mt-6 grid gap-3 text-sm">
          <Detail label="Statement" value={anomaly.statement} />
          <Detail label="Original label (old)" value={anomaly.old_label || '-'} />
          <Detail label="Original label (new)" value={anomaly.new_label || '-'} />
          <Detail label="Old document value" value={money(anomaly.old_value)} />
          <Detail label="New comparative value" value={money(anomaly.new_value)} />
          <Detail label="Difference" value={money(anomaly.delta)} />
          <Detail label="Difference %" value={percent(anomaly)} />
          <Detail label="Confidence" value={Math.round((anomaly.confidence ?? 0) * 100) + '%'} />
          <Detail label="Explanation" value={anomaly.note || 'Cross-year deterministic comparison'} />
          <Detail label="Old document evidence" value={evidenceText(anomaly.old_evidence)} />
          <Detail label="New document evidence" value={evidenceText(anomaly.new_evidence)} />
        </div>
        {anomaly.note && (
          <Card className="mt-6 bg-slate-50 p-4">
            <div className="section-title mb-2">Rule / explanation</div>
            <p className="text-sm leading-6 text-slate-600">{anomaly.note}</p>
          </Card>
        )}
      </aside>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
      <span className="text-slate-500">{label}</span>
      <span className="max-w-[60%] text-right font-medium text-slate-900">{value}</span>
    </div>
  );
}


function evidenceText(evidence?: string | EvidenceReference) {
  if (!evidence) return 'Evidence not available for this anomaly.';
  if (typeof evidence === 'string') return evidence;
  return evidence.raw_text || evidence.section || (evidence.page != null ? 'Page ' + evidence.page : 'Evidence metadata available.');
}
