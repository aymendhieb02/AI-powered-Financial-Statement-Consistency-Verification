export function RiskScoreCard({ score }: { score: number }) {
  const tone = score >= 70 ? 'bg-red-600' : score >= 35 ? 'bg-amber-500' : 'bg-audit-accent';
  return <div className="rounded-lg border border-audit-line bg-white p-5">
    <div className="mb-3 flex items-center justify-between"><h3 className="font-semibold">Risk score</h3><span>{score}/100</span></div>
    <div className="h-3 rounded-full bg-slate-100"><div className={'h-3 rounded-full ' + tone} style={{ width: Math.min(100, score) + '%' }} /></div>
  </div>;
}
