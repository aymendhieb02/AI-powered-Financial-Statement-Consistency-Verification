import { flexRender, getCoreRowModel, getPaginationRowModel, getSortedRowModel, useReactTable, type ColumnDef, type SortingState, type VisibilityState } from '@tanstack/react-table';
import { Download, Eye, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { Anomaly } from '../../types/api';
import { SeverityBadge, StatusBadge } from '../ui/Badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '../ui/sheet';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

function money(value?: number | null) { return typeof value === 'number' ? new Intl.NumberFormat('fr-FR').format(value) : '-'; }
function percent(item: Anomaly) { return item.old_value ? (((item.delta ?? 0) / Number(item.old_value)) * 100).toFixed(2) + '%' : '-'; }

export function AnomaliesTable({ anomalies }: { anomalies: Anomaly[] }) {
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('all');
  const [status, setStatus] = useState('all');
  const [sorting, setSorting] = useState<SortingState>([]);
  const [visibility, setVisibility] = useState<VisibilityState>({ note: false });
  const [selected, setSelected] = useState<Anomaly | null>(null);
  const data = useMemo(() => (anomalies.length ? anomalies : [{ pair: '2023-2024', year: 2024, statement: 'Balance Sheet', canonical_label: 'actif_net', old_label: 'ACTIF NET', new_label: 'Actif Net', old_value: 1520000, new_value: 1495000, delta: -25000, status: 'MISMATCH', severity: 'CRITICAL', confidence: 0.97, note: 'Comparative value differs from prior year closing balance.' }]), [anomalies]);
  const filtered = data.filter((item) => (severity === 'all' || item.severity === severity) && (status === 'all' || item.status === status) && [item.canonical_label, item.statement, item.old_label, item.new_label, item.note].join(' ').toLowerCase().includes(search.toLowerCase()));
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
    { id: 'evidence', header: 'Evidence', cell: ({ row }) => <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); setSelected(row.original); }}><Eye size={14} /> View</Button> },
  ], []);
  const table = useReactTable({ data: filtered, columns, state: { sorting, columnVisibility: visibility }, onSortingChange: setSorting, onColumnVisibilityChange: setVisibility, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getPaginationRowModel: getPaginationRowModel() });

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
            <SelectItem value="OK">OK</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="secondary"><Download size={15} /> Export CSV</Button>
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
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} className="cursor-pointer" onClick={() => setSelected(row.original)}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="whitespace-nowrap">{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
      <div className="flex items-center justify-between text-sm text-slate-500">
        <div>{filtered.length} anomalies</div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>Previous</Button>
          <Button variant="secondary" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>Next</Button>
        </div>
      </div>
      <Sheet open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent>
          {selected && (
            <>
              <SheetHeader>
                <div className="section-title">Anomaly detail</div>
                <SheetTitle>{selected.canonical_label}</SheetTitle>
              </SheetHeader>
              <div className="mt-6 grid gap-3 text-sm">
                <Detail label="Statement" value={selected.statement} />
                <Detail label="Old document value" value={money(selected.old_value)} />
                <Detail label="New comparative value" value={money(selected.new_value)} />
                <Detail label="Difference" value={money(selected.delta)} />
                <Detail label="Difference %" value={percent(selected)} />
                <Detail label="Confidence" value={Math.round((selected.confidence ?? 0) * 100) + '%'} />
                <Detail label="Triggered rule" value={selected.note || 'Cross-year deterministic comparison'} />
                <Detail label="Page" value="Evidence page pending PDF location" />
              </div>
              <Card className="mt-6 bg-slate-50 p-4">
                <div className="section-title mb-2">AI explanation</div>
                <p className="text-sm leading-6 text-slate-600">This row should be reviewed because the comparative value carried into the new annual statement does not reconcile with the prior-year closing value for the same canonical account.</p>
              </Card>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-4 border-b border-slate-100 pb-2"><span className="text-slate-500">{label}</span><span className="text-right font-medium text-slate-900">{value}</span></div>;
}
