import { Search } from 'lucide-react';
import { PageHeader } from '../components/ui/Cards';
import { StatusBadge } from '../components/ui/Badge';

const evidence = [{ pdf: 'MAXULA_2024.pdf', page: 12, statement: 'Balance Sheet', box: '112,248,501,276', raw: 'ACTIF NET 1 495 000', value: '1 495 000', confidence: '97%', method: 'alias' }, { pdf: 'MAXULA_2023.pdf', page: 11, statement: 'Balance Sheet', box: '108,244,498,272', raw: 'ACTIF NET 1 520 000', value: '1 520 000', confidence: '98%', method: 'exact' }];
export function EvidenceViewerPage() {
  return <section className="space-y-6"><PageHeader eyebrow="Traceability" title="Evidence viewer" description="Every extracted financial value is traceable back to source PDF, page, row, raw text, normalized value, and matching method." actions={<div className="relative"><Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" /><input className="input-control pl-9" placeholder="Search evidence" /></div>} />
    <div className="panel overflow-auto"><table className="data-table"><thead><tr><th>PDF</th><th>Page</th><th>Statement</th><th>Bounding box</th><th>Raw text</th><th>Normalized value</th><th>Confidence</th><th>Matching method</th><th>Status</th></tr></thead><tbody>{evidence.map((item) => <tr key={item.pdf + item.raw}><td>{item.pdf}</td><td>{item.page}</td><td>{item.statement}</td><td className="font-mono text-xs">{item.box}</td><td>{item.raw}</td><td>{item.value}</td><td>{item.confidence}</td><td>{item.method}</td><td><StatusBadge status="OK" /></td></tr>)}</tbody></table></div>
  </section>;
}
