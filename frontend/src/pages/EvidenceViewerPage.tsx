import { Search } from 'lucide-react';
import { PageHeader } from '../components/ui/Cards';
import { StatusBadge } from '../components/ui/Badge';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

const evidence = [
  { pdf: 'MAXULA_2024.pdf', page: 12, statement: 'Balance Sheet', box: '112,248,501,276', raw: 'ACTIF NET 1 495 000', value: '1 495 000', confidence: '97%', method: 'alias' },
  { pdf: 'MAXULA_2023.pdf', page: 11, statement: 'Balance Sheet', box: '108,244,498,272', raw: 'ACTIF NET 1 520 000', value: '1 520 000', confidence: '98%', method: 'exact' },
];

export function EvidenceViewerPage() {
  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Traceability"
        title="Evidence viewer"
        description="Every extracted financial value is traceable back to source PDF, page, row, raw text, normalized value, and matching method."
        actions={
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input className="pl-9" placeholder="Search evidence" />
          </div>
        }
      />
      <Card className="overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>PDF</TableHead>
              <TableHead>Page</TableHead>
              <TableHead>Statement</TableHead>
              <TableHead>Bounding box</TableHead>
              <TableHead>Raw text</TableHead>
              <TableHead>Normalized value</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Matching method</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {evidence.map((item) => (
              <TableRow key={item.pdf + item.raw}>
                <TableCell>{item.pdf}</TableCell>
                <TableCell>{item.page}</TableCell>
                <TableCell>{item.statement}</TableCell>
                <TableCell className="font-mono text-xs">{item.box}</TableCell>
                <TableCell>{item.raw}</TableCell>
                <TableCell>{item.value}</TableCell>
                <TableCell>{item.confidence}</TableCell>
                <TableCell>{item.method}</TableCell>
                <TableCell><StatusBadge status="OK" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </section>
  );
}
