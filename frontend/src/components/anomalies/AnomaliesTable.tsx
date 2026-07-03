import { flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, useReactTable, type ColumnDef } from '@tanstack/react-table';
import { useMemo, useState } from 'react';
import type { Anomaly } from '../../types/api';
import { SeverityBadge } from './SeverityBadge';
import { StatusBadge } from './StatusBadge';

export function AnomaliesTable({ anomalies }: { anomalies: Anomaly[] }) {
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const filtered = anomalies.filter((item) => (!severity || item.severity === severity) && (!status || item.status === status) && item.canonical_label.toLowerCase().includes(search.toLowerCase()));
  const columns = useMemo<ColumnDef<Anomaly>[]>(() => [
    { accessorKey: 'severity', header: 'Severity', cell: ({ row }) => <SeverityBadge severity={row.original.severity} /> },
    { accessorKey: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { accessorKey: 'pair', header: 'Pair' },
    { accessorKey: 'year', header: 'Compared year' },
    { accessorKey: 'statement', header: 'Statement' },
    { accessorKey: 'canonical_label', header: 'Label' },
    { accessorKey: 'old_value', header: 'Old value' },
    { accessorKey: 'new_value', header: 'New comparative value' },
    { accessorKey: 'delta', header: 'Difference' },
    { id: 'difference_percent', header: 'Difference %', cell: ({ row }) => row.original.old_value ? (((row.original.delta ?? 0) / Number(row.original.old_value)) * 100).toFixed(2) + '%' : '-' },
    { accessorKey: 'note', header: 'Explanation' },
  ], []);
  const table = useReactTable({ data: filtered, columns, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getFilteredRowModel: getFilteredRowModel() });
  return <div className="space-y-3">
    <div className="flex flex-wrap gap-3"><input className="rounded border border-audit-line px-3 py-2" placeholder="Search label" value={search} onChange={(e) => setSearch(e.target.value)} /><select className="rounded border border-audit-line px-3 py-2" value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="">All severities</option><option>CRITICAL</option><option>MEDIUM</option><option>LOW</option></select><select className="rounded border border-audit-line px-3 py-2" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option><option>MISMATCH</option><option>MISSING_IN_OLD</option><option>MISSING_IN_NEW</option><option>LABEL_RENAMED</option></select></div>
    <div className="overflow-auto rounded-lg border border-audit-line bg-white"><table className="min-w-full text-left text-sm"><thead className="bg-audit-panel text-audit-muted">{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id} className="whitespace-nowrap px-3 py-3">{flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.id} className="border-t border-audit-line">{row.getVisibleCells().map((cell) => <td key={cell.id} className="whitespace-nowrap px-3 py-3">{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></div>
  </div>;
}
