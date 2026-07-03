import { Download, FileJson, FileSpreadsheet } from 'lucide-react';
import { PageHeader } from '../components/ui/Cards';
import { ReportCard } from '../components/ui/Enterprise';
import { ReportDownloadButtons } from '../components/reports/ReportDownloadButtons';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

export function ReportsPage() {
  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Reporting" title="Audit reports" description="Download structured reports generated from ComparisonReport objects: Excel for accountants, JSON for system integration, future PDF for board packs." />
      <div className="grid gap-4 lg:grid-cols-2">
        <ReportCard title="Excel consistency workbook" meta="Created today - Rule Results, Evidence, Confidence, History" action={<Button><FileSpreadsheet size={15} /> Excel</Button>} />
        <ReportCard title="JSON verification payload" meta="Created today - Canonical documents and anomalies" action={<Button variant="secondary"><FileJson size={15} /> JSON</Button>} />
      </div>
      <Card>
        <CardContent className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <div className="section-title">Legacy download actions</div>
              <div className="text-sm text-slate-500">Uses the existing backend report endpoints.</div>
            </div>
            <Download size={18} className="text-slate-400" />
          </div>
          <ReportDownloadButtons />
        </CardContent>
      </Card>
    </section>
  );
}
