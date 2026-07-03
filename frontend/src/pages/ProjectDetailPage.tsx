import { FileText, GitCompareArrows, History, ShieldCheck, UploadCloud } from 'lucide-react';
import { PageHeader, StatCard } from '../components/ui/Cards';
import { PipelineProgress, ReportCard } from '../components/ui/Enterprise';
import { StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const tabs = ['Overview', 'Documents', 'Extraction', 'Validation', 'Comparison', 'Evidence', 'Reports', 'History'];

export function ProjectDetailPage() {
  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Workspace"
        title="MAXULA annual verification"
        description="Repository-style workspace for canonical documents, validation evidence, comparison results, and reports."
        actions={<Button><UploadCloud size={15} /> Upload PDFs</Button>}
      />
      <Tabs defaultValue="Overview">
        <TabsList className="overflow-x-auto">
          {tabs.map((tab) => <TabsTrigger key={tab} value={tab}>{tab}</TabsTrigger>)}
        </TabsList>
        <TabsContent value="Overview" className="mt-6 space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <StatCard label="Documents" value="4" icon={<FileText size={18} />} />
            <StatCard label="Fields compared" value="1,284" icon={<GitCompareArrows size={18} />} tone="blue" />
            <StatCard label="Confidence" value="98.4%" icon={<ShieldCheck size={18} />} tone="emerald" />
            <StatCard label="Runs" value="12" icon={<History size={18} />} />
          </div>
          <PipelineProgress />
          <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
            <Card className="overflow-hidden">
              <CardHeader>
                <CardTitle className="section-title font-normal">Latest comparisons</CardTitle>
              </CardHeader>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Statement</TableHead>
                    <TableHead>Canonical account</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {['total_actif', 'actif_net', 'total_passif', 'resultat_exercice'].map((label, i) => (
                    <TableRow key={label}>
                      <TableCell>Balance Sheet</TableCell>
                      <TableCell>{label}</TableCell>
                      <TableCell><StatusBadge status={i === 1 ? 'MISMATCH' : 'OK'} /></TableCell>
                      <TableCell>{98 - i}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
            <div className="space-y-3">
              <ReportCard title="Excel workbook" meta="Created for latest verification run" action={<Button variant="secondary">Download</Button>} />
              <ReportCard title="Evidence trace" meta="Line-level extraction provenance" action={<Button variant="secondary">Review</Button>} />
            </div>
          </div>
        </TabsContent>
        {tabs.slice(1).map((tab) => (
          <TabsContent key={tab} value={tab} className="mt-6">
            <Card><CardContent className="p-6 text-sm text-slate-500">{tab} workspace content will appear here after the next verification run.</CardContent></Card>
          </TabsContent>
        ))}
      </Tabs>
    </section>
  );
}
