type Card = { label: string; value: string | number; tone?: string };
export function SummaryCards({ cards }: { cards: Card[] }) {
  return <div className="grid gap-4 md:grid-cols-4">
    {cards.map((card) => <div key={card.label} className="rounded-lg border border-audit-line bg-white p-4">
      <div className="text-sm text-audit-muted">{card.label}</div>
      <div className={'mt-2 text-2xl font-semibold ' + (card.tone ?? 'text-audit-ink')}>{card.value}</div>
    </div>)}
  </div>;
}
