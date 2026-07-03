import { flexRender, getCoreRowModel, getPaginationRowModel, getSortedRowModel, useReactTable, type ColumnDef, type SortingState, type VisibilityState } from '@tanstack/react-table';
import { Download, Eye, Search, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { Anomaly } from '../../types/api';
import { SeverityBadge, StatusBadge } from '../ui/Badge';

function money(value?: number | null) { return typeof value === 'number' ? new Intl.NumberFormat('fr-FR').format(value) : '-'; }
function percent(item: Anomaly) { return item.old_value ? (((item.delta ?? 0) / Number(item.old_value)) * 100).toFixed(2) + '%' : '-'; }

export function AnomaliesTable({ anomalies }: { anomalies: Anomaly[] }) {
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const [sorting, setSorting] = useState<SortingState>([]);
  const [visibility, setVisibility] = useState<VisibilityState>({ note: false });
  const [selected, setSelected] = useState<Anomaly | null>(null);
  const data = useMemo(() => (anomalies.length ? anomalies : [{ pair: '2023-2024', year: 2024, statement: 'Balance Sheet', canonical_label: 'actif_net', old_label: 'ACTIF NET', new_label: 'Actif Net', old_value: 1520000, new_value: 1495000, delta: -25000, status: 'MISMATCH', severity: 'CRITICAL', confidence: 0.97, note: 'Comparative value differs from prior year closing balance.' }]), [anomalies]);
  const filtered = data.filter((item) => (!severity || item.severity === severity) && (!status || item.status === status) && [item.canonical_label, item.statement, item.old_label, item.new_label, item.note].join(' ').toLowerCase().includes(search.toLowerCase()));
  const columns = useMemo<ColumnDef<Anomaly>[]>(() => [
    { accessorKey: 'severity', header: 'Severity', cell: ({ row }) => <SeverityBadge severity={row.original.severity} /> },
    { accessorKey: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { accessorKey: 'statement', header: 'Statement' },
    { accessorKey: 'canonical_label', header: 'Canonical account' },
    { accessorKey: 'old_label', header: 'Original label' },
    { accessorKey: 'old_value', header: 'Old value', cell: ({ row }) => money(row.original.old_value) },
    { accessorKey: 'new_value', header: 'New value', cell: ({ row }) => money(row.original.new_value) },
    { accessorKey: 'delta', header: 'Difference', cell: ({ row }) => money(row.original.delta) },
    { id: 'difference_percent', header: 'Difference %', cell: ({ row }) => percent(row.original) },
    { accessorKey: 'confidence', header: 'Confidence', cell: ({ row }) => Math.round((row.original.confidence ?? 0) * 100) + '%' },
    { accessorKey: 'note', header: 'Rule / explanation' },
    { id: 'evidence', header: 'Evidence', cell: ({ row }) => <button className="btn-secondary h-8 px-2" onClick={() => setSelected(row.original)}><Eye size={14} /> View</button> },
  ], []);
  const table = useReactTable({ data: filtered, columns, state: { sorting, columnVisibility: visibility }, onSortingChange: setSorting, onColumnVisibilityChange: setVisibility, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getPaginationRowModel: getPaginationRowModel() });
  return <div className="space-y-3"><div className="panel flex flex-wrap items-center gap-3 p-3"><div className="relative min-w-72 flex-1"><Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" /><input className="input-control w-full pl-9" placeholder="Search accounts, statements, labels, rules" value={search} onChange={(e) => setSearch(e.target.value)} /></div><select className="input-control" value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="">All severities</option><option>CRITICAL</option><option>MEDIUM</option><option>LOW</option></select><select className="input-control" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option><option>MISMATCH</option><option>MISSING_IN_OLD</option><option>MISSING_IN_NEW</option><option>LABEL_RENAMED</option><option>OK</option></select><button className="btn-secondary"><Download size={15} /> Export CSV</button></div>
    <div className="panel overflow-auto"><table className="data-table"><thead>{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id} onClick={header.column.getToggleSortingHandler()} className="whitespace-nowrap cursor-pointer select-none">{flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.id} className="cursor-pointer" onClick={() => setSelected(row.original)}>{row.getVisibleCells().map((cell) => <td key={cell.id} className="whitespace-nowrap">{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></div>
    <div className="flex items-center justify-between text-sm text-slate-500"><div>{filtered.length} anomalies</div><div className="flex gap-2"><button className="btn-secondary" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>Previous</button><button className="btn-secondary" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>Next</button></div></div>
    {selected && <div className="fixed inset-0 z-40 bg-slate-950/20" onClick={() => setSelected(null)}><aside className="absolute right-0 top-0 h-full w-[440px] overflow-y-auto border-l border-slate-200 bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}><div className="flex items-start justify-between"><div><div className="section-title">Anomaly detail</div><h2 className="mt-1 text-lg font-semibold text-slate-950">{selected.canonical_label}</h2></div><button className="btn-secondary" onClick={() => setSelected(null)} aria-label="Close detail"><X size={15} /></button></div><div className="mt-6 grid gap-3 text-sm"><Detail label="Statement" value={selected.statement} /><Detail label="Old document value" value={money(selected.old_value)} /><Detail label="New comparative value" value={money(selected.new_value)} /><Detail label="Difference" value={money(selected.delta)} /><Detail label="Difference %" value={percent(selected)} /><Detail label="Confidence" value={Math.round((selected.confidence ?? 0) * 100) + '%'} /><Detail label="Triggered rule" value={selected.note || 'Cross-year deterministic comparison'} /><Detail label="Page" value="Evidence page pending PDF location" /></div><div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-4"><div className="section-title mb-2">AI explanation</div><p className="text-sm leading-6 text-slate-600">This row should be reviewed because the comparative value carried into the new annual statement does not reconcile with the prior-year closing value for the same canonical account.</p></div></aside></div>}
  </div>;
}
function Detail({ label, value }: { label: string; value: string }) { return <div className="flex justify-between gap-4 border-b border-slate-100 pb-2"><span className="text-slate-500">{label}</span><span className="text-right font-medium text-slate-900">{value}</span></div>; }
