import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable, type ColumnDef, type SortingState, type VisibilityState } from '@tanstack/react-table';
import { Eye, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import type { Anomaly } from '../../types/api';
import { AnomalyDetailDrawer } from './AnomalyDetailDrawer';
import { SeverityBadge, StatusBadge } from '../ui/Badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

function money(value?: number | null) {
  return typeof value === 'number' ? new Intl.NumberFormat('fr-FR').format(value) : '-';
}

type Props = {
  anomalies: Anomaly[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
};

export function AnomaliesTable({ anomalies, total, page, pageSize, onPageChange }: Props) {
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('all');
  const [status, setStatus] = useState('all');
  const [sorting, setSorting] = useState<SortingState>([]);
  const [visibility, setVisibility] = useState<VisibilityState>({ note: false });
  const [selected, setSelected] = useState<Anomaly | null>(null);

  const filtered = useMemo(() => anomalies.filter((item) =>
    (severity === 'all' || item.severity === severity) &&
    (status === 'all' || item.status === status) &&
    [item.canonical_label, item.statement, item.old_label, item.new_label, item.note].join(' ').toLowerCase().includes(search.toLowerCase())
  ), [anomalies, severity, status, search]);

  const columns = useMemo<ColumnDef<Anomaly>[]>(() => [
    { accessorKey: 'severity', header: 'Severity', cell: ({ row }) => <SeverityBadge severity={row.original.severity} /> },
    { accessorKey: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { accessorKey: 'statement', header: 'Statement' },
    { accessorKey: 'canonical_label', header: 'Canonical account' },
    { accessorKey: 'old_label', header: 'Original label' },
    { accessorKey: 'old_value', header: 'Old value', cell: ({ row }) => money(row.original.old_value) },
    { accessorKey: 'new_value', header: 'New value', cell: ({ row }) => money(row.original.new_value) },
    { accessorKey: 'delta', header: 'Difference', cell: ({ row }) => money(row.original.delta) },
    { accessorKey: 'confidence', header: 'Confidence', cell: ({ row }) => Math.round((row.original.confidence ?? 0) * 100) + '%' },
    { accessorKey: 'note', header: 'Rule / explanation' },
    {
      id: 'evidence',
      header: 'Evidence',
      cell: ({ row }) => (
        <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); setSelected(row.original); }}>
          <Eye size={14} /> View
        </Button>
      ),
    },
  ], []);

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting, columnVisibility: visibility },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  useEffect(() => {
    if (page > totalPages) onPageChange(totalPages);
  }, [page, totalPages, onPageChange]);

  if (total === 0 && !search && severity === 'all' && status === 'all') {
    return (
      <Card>
        <div className="p-8 text-center text-sm text-slate-500">
          No anomalies found for the selected verification run.
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <Card className="flex flex-wrap items-center gap-3 p-3">
        <div className="relative min-w-72 flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input className="w-full pl-9" placeholder="Search accounts, statements, labels, rules" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <Select value={severity} onValueChange={setSeverity}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Severity" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severities</SelectItem>
            <SelectItem value="CRITICAL">CRITICAL</SelectItem>
            <SelectItem value="MEDIUM">MEDIUM</SelectItem>
            <SelectItem value="LOW">LOW</SelectItem>
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="MISMATCH">MISMATCH</SelectItem>
            <SelectItem value="MISSING_IN_OLD">MISSING_IN_OLD</SelectItem>
            <SelectItem value="MISSING_IN_NEW">MISSING_IN_NEW</SelectItem>
            <SelectItem value="LABEL_RENAMED">LABEL_RENAMED</SelectItem>
          </SelectContent>
        </Select>
      </Card>

      <Card className="overflow-auto">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((group) => (
              <TableRow key={group.id}>
                {group.headers.map((header) => (
                  <TableHead key={header.id} onClick={header.column.getToggleSortingHandler()} className="cursor-pointer select-none whitespace-nowrap">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow><TableCell colSpan={columns.length} className="py-8 text-center text-sm text-slate-500">No anomalies match the current filters.</TableCell></TableRow>
            ) : table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} className="cursor-pointer" onClick={() => setSelected(row.original)}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <div className="flex items-center justify-between text-sm text-slate-500">
        <div>{total} anomalies total · page {page} of {totalPages}</div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => onPageChange(page - 1)} disabled={page <= 1}>Previous</Button>
          <Button variant="secondary" size="sm" onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}>Next</Button>
        </div>
      </div>

      {selected && <AnomalyDetailDrawer anomaly={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
